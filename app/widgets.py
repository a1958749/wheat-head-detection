from __future__ import annotations

from typing import Iterable, List, Sequence

import cv2
from matplotlib import rcParams
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from tool.tools import resize_with_padding


rcParams["font.family"] = "sans-serif"
rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "Segoe UI",
    "SimHei",
    "Noto Sans CJK SC",
    "DejaVu Sans",
]
rcParams["axes.unicode_minus"] = False


def apply_shadow(
    widget: QtWidgets.QWidget,
    blur_radius: int = 14,
    offset_y: int = 3,
    color: QtGui.QColor | None = None,
) -> None:
    """Apply drop shadow effect to widget.
    
    Note: QGraphicsDropShadowEffect can cause layout issues in some cases.
    Shadow is now disabled to prevent layout drift issues.
    """
    # Disabled shadow effect to prevent layout drift
    # If you want to re-enable shadows, uncomment the following:
    # effect = QtWidgets.QGraphicsDropShadowEffect(widget)
    # effect.setBlurRadius(blur_radius)
    # effect.setOffset(0, offset_y)
    # effect.setColor(color or QtGui.QColor(25, 42, 34, 20))
    # widget.setGraphicsEffect(effect)
    pass


class NoWheelMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event):  # type: ignore[override]
        event.ignore()


class NoWheelComboBox(NoWheelMixin, QtWidgets.QComboBox):
    pass


class NoWheelSpinBox(NoWheelMixin, QtWidgets.QSpinBox):
    pass


class NoWheelDoubleSpinBox(NoWheelMixin, QtWidgets.QDoubleSpinBox):
    pass


class PageHeader(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("SectionCard")
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        self.left_label = QtWidgets.QLabel("--")
        self.left_label.setObjectName("InfoBadge")
        self.center_label = QtWidgets.QLabel("")
        self.center_label.setObjectName("MetaText")
        self.right_badge = QtWidgets.QLabel("空闲")
        self.right_badge.setObjectName("StatusBadge")

        layout.addWidget(self.left_label)
        layout.addWidget(self.center_label, 1)
        layout.addWidget(self.right_badge)
        apply_shadow(self, blur_radius=18, offset_y=4)

    def set_left(self, text: str):
        self.left_label.setText(text)

    def set_center(self, text: str):
        self.center_label.setText(text)

    def set_right(self, text: str, style: str = ""):
        self.right_badge.setText(text)
        if style:
            self.right_badge.setStyleSheet(style)


class StatusBadge(QtWidgets.QLabel):
    def __init__(self, text: str = ""):
        super().__init__(text)
        self.setObjectName("StatusBadge")
        self.setAlignment(Qt.AlignCenter)


class StatusChip(StatusBadge):
    def set_status(self, text: str, color: str = ""):
        self.setText(text)
        if color:
            self.setStyleSheet(
                f"background:{color}; color:white; border:none; border-radius:12px; "
                "padding:6px 12px; font-weight:800;"
            )
        else:
            self.setStyleSheet("")


class SectionCard(QtWidgets.QFrame):
    """带可选背景图片的卡片组件"""
    # 类级别的背景图片缓存
    _bg_pixmap_cache = None
    _bg_path = "./img/wheat_backgrounds/wheat_golden_field.jpg"
    
    def __init__(self, title: str = "", subtitle: str = "", with_bg: bool = False):
        super().__init__()
        self.setObjectName("SectionCard")
        self._with_bg = with_bg
        self._bg_opacity = 0.12
        
        # 懒加载背景图片
        if with_bg and SectionCard._bg_pixmap_cache is None:
            from app.config import resolve_path
            SectionCard._bg_pixmap_cache = QtGui.QPixmap(str(resolve_path(SectionCard._bg_path)))
        
        self.outer_layout = QtWidgets.QVBoxLayout(self)
        self.outer_layout.setContentsMargins(14, 12, 14, 12)
        self.outer_layout.setSpacing(8)

        self.header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QVBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("PanelTitle")
        self.subtitle_label = QtWidgets.QLabel(subtitle)
        self.subtitle_label.setObjectName("PanelSubtitle")
        self.subtitle_label.setWordWrap(True)

        if title:
            header_layout.addWidget(self.title_label)
        if subtitle:
            header_layout.addWidget(self.subtitle_label)
        self.header_widget.setVisible(bool(title or subtitle))
        self.outer_layout.addWidget(self.header_widget)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        self.outer_layout.addLayout(self.layout)
        apply_shadow(self, blur_radius=16, offset_y=4)

    def paintEvent(self, event):
        """绘制背景图片"""
        super().paintEvent(event)
        if not self._with_bg or SectionCard._bg_pixmap_cache is None or SectionCard._bg_pixmap_cache.isNull():
            return
            
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        
        rect = self.rect()
        
        # 缩放背景图片
        scaled_bg = SectionCard._bg_pixmap_cache.scaled(
            rect.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        # 居中裁剪
        offset_x = max((scaled_bg.width() - rect.width()) // 2, 0)
        offset_y = max((scaled_bg.height() - rect.height()) // 2, 0)
        
        # 创建圆角路径
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(rect), 16, 16)
        painter.setClipPath(path)
        
        # 绘制背景图片
        painter.setOpacity(self._bg_opacity)
        painter.drawPixmap(
            0, 0,
            scaled_bg,
            offset_x, offset_y,
            rect.width(), rect.height()
        )
        
        painter.end()

    def set_header(self, title: str, subtitle: str = ""):
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
        self.title_label.setVisible(bool(title))
        self.subtitle_label.setVisible(bool(subtitle))
        self.header_widget.setVisible(bool(title or subtitle))


class StatsCard(QtWidgets.QFrame):
    def __init__(self, title: str, value: str = "--", subtitle: str = ""):
        super().__init__()
        self.setObjectName("StatsCard")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("StatsCardTitle")
        self.value_label = QtWidgets.QLabel(str(value))
        self.value_label.setObjectName("StatsCardValue")
        self.subtitle_label = QtWidgets.QLabel(subtitle)
        self.subtitle_label.setObjectName("StatsCardSubtitle")
        self.subtitle_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)
        layout.addStretch(1)
        apply_shadow(self, blur_radius=16, offset_y=4)

    def set_content(self, value, subtitle: str = "") -> None:
        self.value_label.setText(str(value))
        self.subtitle_label.setText(str(subtitle))


class InfoRow(QtWidgets.QWidget):
    def __init__(self, label_text: str, value_text: str = "--"):
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.label = QtWidgets.QLabel(label_text)
        self.label.setObjectName("InfoRowLabel")
        self.value = QtWidgets.QLabel(value_text)
        self.value.setObjectName("InfoRowValue")
        self.value.setWordWrap(True)
        self.value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(self.label, 0, Qt.AlignTop)
        layout.addWidget(self.value, 1)

    def set_value(self, value_text: str):
        self.value.setText(str(value_text))


class KeyValueBlock(InfoRow):
    pass


class PreviewPanel(QtWidgets.QFrame):
    def __init__(self, title: str, subtitle: str = "", minimum_height: int = 280):
        super().__init__()
        self.setObjectName("PreviewPanelFrame")
        self._image = None
        self._note = subtitle
        self._last_size = (0, 0)
        self._rendering = False  # Flag to prevent recursive rendering

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header_layout = QtWidgets.QVBoxLayout()
        header_layout.setSpacing(4)
        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("PanelTitle")
        self.meta_label = QtWidgets.QLabel(subtitle)
        self.meta_label.setObjectName("MetaText")
        self.meta_label.setWordWrap(True)
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.meta_label)

        self.image_label = QtWidgets.QLabel(subtitle or "暂无图像")
        self.image_label.setObjectName("ImageStage")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(minimum_height)
        # Use Fixed size policy to prevent layout changes from pixmap
        self.image_label.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.image_label.setScaledContents(False)

        layout.addLayout(header_layout)
        layout.addWidget(self.image_label, 1)
        apply_shadow(self, blur_radius=18, offset_y=5)

    def set_placeholder(self, text: str):
        self._image = None
        self._note = text
        self.meta_label.setText(text)
        self.image_label.setText(text)
        self.image_label.setPixmap(QtGui.QPixmap())

    def set_image(self, image, note: str = ""):
        if image is None:
            self.set_placeholder(note or "暂无图像")
            return
        self._image = image.copy()
        self._note = note
        self.meta_label.setText(note)
        self._render_image()

    def _render_image(self):
        if self._image is None or self._rendering:
            return
        self._rendering = True
        try:
            # Use fixed display size based on current label size
            display_width = max(self.image_label.width(), 300)
            display_height = max(self.image_label.height(), 200)
            # Cap the size to prevent infinite growth
            display_width = min(display_width, 1200)
            display_height = min(display_height, 800)
            
            preview = resize_with_padding(self._image, display_width, display_height, [248, 249, 247])
            preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
            qt_image = QtGui.QImage(
                preview.data,
                preview.shape[1],
                preview.shape[0],
                preview.shape[1] * 3,
                QtGui.QImage.Format_RGB888,
            )
            self.image_label.setText("")
            pixmap = QtGui.QPixmap.fromImage(qt_image)
            # Scale pixmap to fit label without changing label size
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        finally:
            self._rendering = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Disable automatic re-rendering on resize to prevent infinite loops
        # Images will be rendered once when set_image is called
        pass


class MatplotlibCanvas(FigureCanvas):
    def __init__(self):
        self.figure = Figure(figsize=(5, 3), dpi=100)
        super().__init__(self.figure)
        self.setMinimumHeight(220)
        # Set fixed size policy to prevent layout drift
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored,
            QtWidgets.QSizePolicy.Ignored
        )
        # Prevent size hint changes
        self.setMinimumSize(100, 100)
        self._palette = {
            "surface": "#FFFFFF",
            "text": "#1E2E23",
            "muted": "#4A6B55",
            "border": "#D0DDD2",
            "primary": "#2F7D57",
            "accent": "#D7A03C",
        }
        # Use fixed subplot parameters to prevent layout changes
        self.figure.subplots_adjust(left=0.12, right=0.95, top=0.90, bottom=0.15)
    
    def sizeHint(self):
        """Return a fixed size hint to prevent layout recalculation."""
        return QtCore.QSize(400, 250)
    
    def minimumSizeHint(self):
        """Return a fixed minimum size hint."""
        return QtCore.QSize(100, 100)

    def set_palette(self, palette: dict) -> None:
        self._palette = {
            "surface": palette.get("surface", "#FFFFFF"),
            "text": palette.get("text", "#1E2E23"),
            "muted": palette.get("muted", "#4A6B55"),
            "border": palette.get("border", "#D0DDD2"),
            "primary": palette.get("primary", "#2F7D57"),
            "accent": palette.get("accent", "#D7A03C"),
        }
        self.figure.patch.set_facecolor(self._palette["surface"])
        self.figure.patch.set_alpha(0.0)

    def clear_axes(self):
        self.figure.clear()
        self.figure.patch.set_facecolor(self._palette["surface"])
        self.figure.patch.set_alpha(0.0)
        # Use fixed subplot parameters
        axes = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=0.12, right=0.95, top=0.90, bottom=0.15)
        axes.set_facecolor("none")
        axes.tick_params(colors=self._palette["muted"])
        axes.xaxis.label.set_color(self._palette["muted"])
        axes.yaxis.label.set_color(self._palette["muted"])
        axes.title.set_color(self._palette["text"])
        for spine in axes.spines.values():
            spine.set_color(self._palette["border"])
        return axes

    def _safe_draw(self):
        """Draw without triggering layout changes."""
        try:
            self.draw_idle()
        except Exception:
            pass

    def plot_bar(self, labels: Sequence[str], values: Sequence[float], title: str):
        axes = self.clear_axes()
        if not labels:
            axes.text(0.5, 0.5, "暂无数据", ha="center", va="center", color=self._palette["muted"])
            axes.set_xticks([])
            axes.set_yticks([])
            self._safe_draw()
            return
        axes.bar(labels, values, color=self._palette["primary"], edgecolor="none", width=0.62)
        axes.set_title(title)
        axes.tick_params(axis="x", rotation=18)
        axes.grid(axis="y", linestyle="--", alpha=0.28, color=self._palette["border"])
        self._safe_draw()

    def plot_line(self, labels: Sequence[str], values: Sequence[float], title: str):
        axes = self.clear_axes()
        if not labels:
            axes.text(0.5, 0.5, "暂无数据", ha="center", va="center", color=self._palette["muted"])
            axes.set_xticks([])
            axes.set_yticks([])
            self._safe_draw()
            return
        x_values = list(range(len(values)))
        axes.plot(x_values, values, color=self._palette["accent"], marker="o", linewidth=2.6)
        axes.fill_between(x_values, values, alpha=0.14, color=self._palette["accent"])
        axes.set_xticks(x_values)
        axes.set_xticklabels(labels)
        axes.set_title(title)
        axes.tick_params(axis="x", rotation=20)
        axes.grid(axis="y", linestyle="--", alpha=0.28, color=self._palette["border"])
        self._safe_draw()

    def plot_pie(self, labels: Sequence[str], values: Sequence[float], title: str):
        axes = self.clear_axes()
        if not labels:
            axes.text(0.5, 0.5, "暂无数据", ha="center", va="center", color=self._palette["muted"])
            axes.set_xticks([])
            axes.set_yticks([])
            self._safe_draw()
            return
        colors = [
            self._palette["primary"],
            self._palette["accent"],
            "#5EA27E",
            "#C88635",
            "#89B89D",
            "#E0B45C",
        ]
        axes.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors[: len(values)])
        axes.set_title(title)
        self._safe_draw()

    def plot_hist(self, values: Iterable[float], title: str):
        axes = self.clear_axes()
        values = list(values)
        if not values:
            axes.text(0.5, 0.5, "暂无数据", ha="center", va="center", color=self._palette["muted"])
            axes.set_xticks([])
            axes.set_yticks([])
            self._safe_draw()
            return
        axes.hist(values, bins=8, color=self._palette["primary"], edgecolor="white", alpha=0.92)
        axes.set_title(title)
        axes.set_xlabel("置信度")
        axes.set_ylabel("数量")
        axes.grid(axis="y", linestyle="--", alpha=0.28, color=self._palette["border"])
        self._safe_draw()


class ChartCard(SectionCard):
    def __init__(self, title: str, subtitle: str = ""):
        super().__init__(title, subtitle)
        self.setObjectName("ChartCard")
        self.canvas = MatplotlibCanvas()
        self.layout.addWidget(self.canvas)


class ToolbarButton(QtWidgets.QPushButton):
    def __init__(self, text: str, role: str = "secondary"):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setAutoDefault(False)
        self.setDefault(False)
        if role == "primary":
            self.setObjectName("PrimaryButton")
        elif role == "danger":
            self.setObjectName("DangerButton")
        elif role == "accent":
            self.setObjectName("AccentButton")
        else:
            self.setObjectName("SecondaryButton")


class AppMessageDialog(QtWidgets.QDialog):
    ICONS = {
        "info": ("i", "#2F7D57", "#E9F5EE"),
        "success": ("✓", "#2D8D5C", "#EAF7EF"),
        "warning": ("!", "#CF8C29", "#FFF3E2"),
        "error": ("×", "#C9584F", "#FDEDEC"),
    }

    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        title: str,
        text: str,
        kind: str = "info",
        ok_text: str = "确定",
        cancel_text: str = "取消",
        show_cancel: bool = False,
    ):
        super().__init__(parent)
        self._accepted = False
        self._kind = kind if kind in self.ICONS else "info"

        self.setObjectName("AppMessageDialog")
        self.setModal(True)
        self.setWindowFlag(Qt.Dialog, True)
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setSizeGripEnabled(False)

        if parent is not None and parent.styleSheet():
            self.setStyleSheet(parent.styleSheet())

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(22, 22, 22, 22)
        outer.setSpacing(0)

        card = QtWidgets.QFrame()
        card.setObjectName("DialogCard")
        apply_shadow(card, blur_radius=28, offset_y=10, color=QtGui.QColor(20, 31, 26, 34))
        outer.addWidget(card)

        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(22, 22, 22, 18)
        card_layout.setSpacing(16)

        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(14)

        symbol, fg_color, bg_color = self.ICONS[self._kind]
        self.icon_label = QtWidgets.QLabel(symbol)
        self.icon_label.setObjectName("DialogIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(48, 48)
        self.icon_label.setStyleSheet(
            f"background:{bg_color}; color:{fg_color}; border-radius:24px; font-size:24px; font-weight:800;"
        )

        title_col = QtWidgets.QVBoxLayout()
        title_col.setSpacing(6)
        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("DialogTitle")
        self.body_label = QtWidgets.QLabel(text)
        self.body_label.setObjectName("DialogBody")
        self.body_label.setWordWrap(True)
        self.body_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        title_col.addWidget(self.title_label)
        title_col.addWidget(self.body_label)

        top_row.addWidget(self.icon_label, 0, Qt.AlignTop)
        top_row.addLayout(title_col, 1)
        card_layout.addLayout(top_row)

        button_row = QtWidgets.QHBoxLayout()
        button_row.setSpacing(10)
        button_row.addStretch(1)

        self.cancel_button: ToolbarButton | None = None
        if show_cancel:
            self.cancel_button = ToolbarButton(cancel_text, role="secondary")
            self.cancel_button.setMinimumWidth(96)
            self.cancel_button.clicked.connect(self.reject)
            button_row.addWidget(self.cancel_button)

        self.ok_button = ToolbarButton(ok_text, role="primary" if kind != "error" else "danger")
        self.ok_button.setMinimumWidth(96)
        self.ok_button.clicked.connect(self._accept_dialog)
        button_row.addWidget(self.ok_button)
        card_layout.addLayout(button_row)

    def _accept_dialog(self):
        self._accepted = True
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()
        if self.parentWidget() is None:
            return
        parent_geometry = self.parentWidget().frameGeometry()
        center = parent_geometry.center()
        geometry = self.frameGeometry()
        geometry.moveCenter(center)
        self.move(geometry.topLeft())

    @classmethod
    def _run(
        cls,
        parent: QtWidgets.QWidget | None,
        title: str,
        text: str,
        kind: str,
        ok_text: str = "确定",
        cancel_text: str = "取消",
        show_cancel: bool = False,
    ) -> bool:
        dialog = cls(parent, title, text, kind=kind, ok_text=ok_text, cancel_text=cancel_text, show_cancel=show_cancel)
        return dialog.exec_() == QtWidgets.QDialog.Accepted

    @classmethod
    def information(cls, parent: QtWidgets.QWidget | None, title: str, text: str) -> bool:
        return cls._run(parent, title, text, kind="info")

    @classmethod
    def success(cls, parent: QtWidgets.QWidget | None, title: str, text: str) -> bool:
        return cls._run(parent, title, text, kind="success")

    @classmethod
    def warning(cls, parent: QtWidgets.QWidget | None, title: str, text: str) -> bool:
        return cls._run(parent, title, text, kind="warning")

    @classmethod
    def error(cls, parent: QtWidgets.QWidget | None, title: str, text: str) -> bool:
        return cls._run(parent, title, text, kind="error")

    @classmethod
    def confirm(
        cls,
        parent: QtWidgets.QWidget | None,
        title: str,
        text: str,
        ok_text: str = "确定",
        cancel_text: str = "取消",
    ) -> bool:
        return cls._run(parent, title, text, kind="warning", ok_text=ok_text, cancel_text=cancel_text, show_cancel=True)


def add_widgets(target_layout, widgets: List[QtWidgets.QWidget], stretch_last: bool = False):
    for widget in widgets:
        target_layout.addWidget(widget)
    if stretch_last:
        target_layout.addStretch(1)
