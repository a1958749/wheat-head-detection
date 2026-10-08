import torch
import torch.nn as nn

from ultralytics.nn.modules import Bottleneck, C2f, Conv


class EMAAttention(nn.Module):
    def __init__(self, c1: int, groups: int = 8):
        super().__init__()
        self.groups = max(1, min(groups, c1))
        while c1 % self.groups != 0 and self.groups > 1:
            self.groups -= 1
        group_channels = c1 // self.groups
        self.conv1x1 = nn.Conv2d(group_channels, group_channels, kernel_size=1, stride=1, padding=0)
        self.conv3x3 = nn.Conv2d(
            group_channels,
            group_channels,
            kernel_size=3,
            stride=1,
            padding=1,
            groups=group_channels,
            bias=False,
        )
        self.gn = nn.GroupNorm(1, group_channels)
        self.softmax = nn.Softmax(dim=-1)
        self.agp = nn.AdaptiveAvgPool2d(1)

    def forward(self, x):
        b, c, h, w = x.size()
        g = self.groups
        xg = x.view(b * g, -1, h, w)
        x_h = xg.mean(dim=3, keepdim=True)
        x_w = xg.mean(dim=2, keepdim=True).permute(0, 1, 3, 2)
        hw = torch.cat([x_h, x_w], dim=2)
        hw = self.conv1x1(hw)
        x_h, x_w = torch.split(hw, [h, w], dim=2)
        x_w = x_w.permute(0, 1, 3, 2)
        x1 = self.gn(xg * torch.sigmoid(x_h) * torch.sigmoid(x_w))
        x2 = self.conv3x3(xg)
        x11 = self.softmax(self.agp(x1).view(b * g, 1, -1))
        x12 = x2.view(b * g, -1, h * w)
        x21 = self.softmax(self.agp(x2).view(b * g, 1, -1))
        x22 = x1.view(b * g, -1, h * w)
        weights = (torch.bmm(x11, x12) + torch.bmm(x21, x22)).view(b * g, 1, h, w)
        out = (xg * torch.sigmoid(weights)).view(b, c, h, w)
        return out


class RFAConv(nn.Module):
    def __init__(self, c1: int, c2: int, k: int = 3, s: int = 1):
        super().__init__()
        p = k // 2
        self.local = Conv(c1, c2, k, s)
        self.context = nn.Sequential(
            nn.AvgPool2d(kernel_size=3, stride=1, padding=1),
            Conv(c1, c2, 1, 1),
        )
        self.fuse = Conv(c2 * 2, c2, 1, 1)

    def forward(self, x):
        local_feat = self.local(x)
        context_feat = self.context(x)
        return self.fuse(torch.cat([local_feat, context_feat], dim=1))


class BottleneckRFA(nn.Module):
    def __init__(self, c: int, shortcut: bool = False, g: int = 1, e: float = 1.0):
        super().__init__()
        hidden = int(c * e)
        self.cv1 = Conv(c, hidden, 1, 1)
        self.cv2 = RFAConv(hidden, c, 3, 1)
        self.add = shortcut and c == c

    def forward(self, x):
        y = self.cv2(self.cv1(x))
        return x + y if self.add else y


class C2f_EMA(C2f):
    def __init__(self, c1: int, c2: int, n: int = 1, shortcut: bool = False, g: int = 1, e: float = 0.5):
        super().__init__(c1, c2, n=n, shortcut=shortcut, g=g, e=e)
        self.ema = EMAAttention(self.c)

    def forward(self, x):
        y = list(self.cv1(x).chunk(2, 1))
        y.extend(m(y[-1]) for m in self.m)
        y[-1] = self.ema(y[-1])
        return self.cv2(torch.cat(y, 1))


class C2f_RFAConv(C2f):
    def __init__(self, c1: int, c2: int, n: int = 1, shortcut: bool = False, g: int = 1, e: float = 0.5):
        super().__init__(c1, c2, n=n, shortcut=shortcut, g=g, e=e)
        self.m = nn.ModuleList(BottleneckRFA(self.c, shortcut=shortcut, e=1.0) for _ in range(n))
