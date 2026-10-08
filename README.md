# 小麦麦穗检测识别系统

基于 PyQt5 的桌面检测软件，模型为 YOLOv8n + C2f-EMA + WIoU。
支持图像、视频、摄像头检测，检测结果展示、麦穗计数、数据分析、历史记录与结果导出。

## 安装与启动

建议使用 Windows 和 Python 3.10，在项目根目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

需要 NVIDIA GPU 时，可先安装与驱动兼容的 CUDA 版 PyTorch，例如本项目训练使用的组合：

```powershell
python -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu124
python -m pip install -r requirements.txt
```

默认设备为 GPU 0；没有可用 GPU 时，在系统设置页将设备改为 `cpu`。
通过 `start_windows.cmd` 也可启动；该脚本优先使用项目内 `.venv`。

## 模型与默认推理配置

- 权重：`weights/yolov8n_c2fema_wiou_best.pt`
- 输入尺寸：768
- 置信度：0.40
- 设备：0（可在设置页修改）
- 检测历史与输出：`output/sessions/`
- 保留手动选择其他权重和调整推理参数的功能。

仓库包含与最终权重配套的本地 Ultralytics 8.4.45 源码和 `internal_module.py`。
请从仓库根目录启动，使 Python 优先导入本地源码。
C2f-EMA 的具体实现见 `internal_module.py`；名称中的 WIoU 表示训练时的框回归损失配置。

## 最终测试结果

| Precision | Recall | F1 | mAP@0.5 | mAP@0.5:0.95 |
|---:|---:|---:|---:|---:|
| 0.923962 | 0.886569 | 0.904879 | 0.944603 | 0.544774 |

F1 根据该次测试的 Precision 和 Recall 计算：`2PR/(P+R)`。
来源为已有最终测试输出，本次发布没有重新选择模型或重跑 test。
最终训练设置为 AdamW、lr0=0.01、imgsz=768、batch=8、workers=4、cache=ram、close_mosaic=0、最多200轮。
精确测试数值、权重 SHA256 和实际完成轮数记录在 `model_metadata.json`。

## 目录

```text
app/                    界面、检测引擎、分析和历史记录逻辑
config/configs.yaml     默认软件配置
icon/                   界面图标和图片
img/wheat_backgrounds/  界面背景素材及来源
tool/                   图像绘制与结果导出工具
ultralytics/            配套模型运行源码
weights/                最终模型权重
main.py                 启动入口
verify_release.py       界面初始化与可选单张推理检查
```

## 检查发布包

```powershell
python verify_release.py
python verify_release.py --image "你的测试图片.png" --device cpu
```

第二条命令保存真实检测预览，并输出模型加载与推理结果。
完整数据集、个人论文、旧权重、备份、历史检测记录和视频未包含在发布包内。

## 第三方组件

Ultralytics 源码保留原版权标记，许可为 AGPL-3.0，详见 `LICENSE-ULTRALYTICS`。
PyQt5 和其他依赖遵循各自许可证。
界面背景图片来源记录在 `img/wheat_backgrounds/SOURCES.txt`。
本仓库没有为第三方图片、模型及其他依赖重新授予许可。
