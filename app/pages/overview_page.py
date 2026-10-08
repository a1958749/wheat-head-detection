from __future__ import annotations

from typing import Dict

from PyQt5 import QtCore, QtGui, QtWidgets

from app.config import resolve_path
from app.models import ModelInfo
from app.widgets import ToolbarButton


class OverviewPage(QtWidgets.QWidget):
    """首页 - 居中布局，带背景图片"""
    start_detection_requested = QtCore.pyqtSignal()
    history_requested = QtCore.pyqtSignal()
    analytics_requested = QtCore.pyqtSignal()
    settings_requested = QtCore.pyqtSignal()
    load_demo_requested = QtCore.pyqtSignal()

    def __init__(self, app_title: str, app_subtitle: str, app_description: str):
        super().__init__()
        self.app_title = app_title
        self.app_subtitle = app_subtitle
        self.app_description = app_description
        self.setObjectName("OverviewPageSurface")
        
        # 加载背景图片
        self._bg_pixmap = QtGui.QPixmap(str(resolve_path("./img/wheat_backgrounds/wheat_field_trees.jpg")))
        
        self._build_ui()
        self._connect_signals()

    def paintEvent(self, event):
        """绘制背景图片"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        
        rect = self.rect()
        
        if not self._bg_pixmap.isNull():
            # 缩放背景图片以覆盖整个区域
            scaled_bg = self._bg_pixmap.scaled(
                rect.size(),
                QtCore.Qt.KeepAspectRatioByExpanding,
                QtCore.Qt.SmoothTransformation,
            )
            # 居中裁剪
            offset_x = max((scaled_bg.width() - rect.width()) // 2, 0)
            offset_y = max((scaled_bg.height() - rect.height()) // 2, 0)
            
            # 绘制背景图片
            painter.setOpacity(0.25)
            painter.drawPixmap(
                0, 0, 
                scaled_bg, 
                offset_x, offset_y, 
                rect.width(), rect.height()
            )
        
        painter.end()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(0)

        # 隐藏的状态标签（保持兼容性）
        self.datetime_badge = QtWidgets.QLabel("--")
        self.datetime_badge.setVisible(False)
        self.system_status_badge = QtWidgets.QLabel("待机")
        self.system_status_badge.setVisible(False)
        self.model_badge = QtWidgets.QLabel("模型：未加载")
        self.model_badge.setVisible(False)
        self.device_badge = QtWidgets.QLabel("设备：--")
        self.device_badge.setVisible(False)

        # ── 上部弹性空间 ──
        root.addStretch(2)

        # ── 中央内容区域（居中） ──
        center_widget = QtWidgets.QWidget()
        center_layout = QtWidgets.QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(16)
        center_layout.setAlignment(QtCore.Qt.AlignCenter)

        # 标题区域（居中）
        self.kicker_label = QtWidgets.QLabel("WHEAT DETECTION SYSTEM")
        self.kicker_label.setObjectName("OverviewKicker")
        self.kicker_label.setAlignment(QtCore.Qt.AlignCenter)

        self.title_label = QtWidgets.QLabel(self.app_title)
        self.title_label.setObjectName("OverviewTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)

        subtitle_text = self.app_subtitle or "面向小麦麦穗识别的智能检测与分析平台"
        self.subtitle_label = QtWidgets.QLabel(subtitle_text)
        self.subtitle_label.setObjectName("OverviewSubtitle")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(QtCore.Qt.AlignCenter)

        center_layout.addWidget(self.kicker_label)
        center_layout.addWidget(self.title_label)
        center_layout.addWidget(self.subtitle_label)
        center_layout.addSpacing(20)

        # ── 主操作区域（居中，更宽） ──
        action_panel = QtWidgets.QFrame()
        action_panel.setObjectName("OverviewActionPanel")
        action_panel.setMinimumWidth(500)
        action_panel.setMaximumWidth(900)
        action_layout = QtWidgets.QVBoxLayout(action_panel)
        action_layout.setContentsMargins(40, 32, 40, 32)
        action_layout.setSpacing(18)

        self.search_title_label = QtWidgets.QLabel("从这里开始一轮检测")
        self.search_title_label.setObjectName("OverviewActionTitle")
        self.search_title_label.setAlignment(QtCore.Qt.AlignCenter)
        
        self.search_hint_label = QtWidgets.QLabel("选择图片、文件夹、视频或摄像头后，进入检测工作台")
        self.search_hint_label.setObjectName("OverviewActionHint")
        self.search_hint_label.setWordWrap(True)
        self.search_hint_label.setAlignment(QtCore.Qt.AlignCenter)

        self.btn_start = ToolbarButton("进入检测工作台", role="primary")
        self.btn_start.setMinimumHeight(56)
        self.btn_start.setMinimumWidth(240)

        action_layout.addWidget(self.search_title_label)
        action_layout.addWidget(self.search_hint_label)
        action_layout.addSpacing(12)
        
        btn_container = QtWidgets.QHBoxLayout()
        btn_container.addStretch(1)
        btn_container.addWidget(self.btn_start)
        btn_container.addStretch(1)
        action_layout.addLayout(btn_container)

        # 将操作面板居中，占据更多宽度
        action_container = QtWidgets.QHBoxLayout()
        action_container.setContentsMargins(40, 0, 40, 0)
        action_container.addWidget(action_panel, 1)
        center_layout.addLayout(action_container)

        center_layout.addSpacing(16)

        # ── 快捷操作按钮行（居中） ──
        quick_row = QtWidgets.QHBoxLayout()
        quick_row.setSpacing(12)
        quick_row.addStretch(1)

        self.btn_demo = ToolbarButton("加载演示样例", role="accent")
        self.btn_history = ToolbarButton("查看历史")
        self.btn_analytics = ToolbarButton("数据分析")
        self.btn_settings = ToolbarButton("系统设置")
        for button in (self.btn_demo, self.btn_history, self.btn_analytics, self.btn_settings):
            button.setMinimumHeight(40)
            quick_row.addWidget(button)
        quick_row.addStretch(1)
        center_layout.addLayout(quick_row)

        root.addWidget(center_widget)

        # ── 下部弹性空间 ──
        root.addStretch(2)

        # ── 底部统计卡片区域 ──
        stats_row = QtWidgets.QHBoxLayout()
        stats_row.setSpacing(14)

        self.stats_cards = {}
        stats_data = [
            ("records", "累计检测次数", "0", "历史记录总数"),
            ("targets", "识别目标总数", "0", "累计识别目标"),
            ("avg_time", "平均推理耗时", "--", "全量任务平均耗时"),
            ("latest_time", "最近一次检测", "--", "最近任务时间"),
        ]
        
        for key, title, value, subtitle in stats_data:
            card = self._create_stats_card(title, value, subtitle)
            self.stats_cards[key] = card
            stats_row.addWidget(card, 1)
        
        root.addLayout(stats_row)

        # ── 底部说明 ──
        description_text = self.app_description or ""
        if description_text:
            self.description_label = QtWidgets.QLabel(description_text)
            self.description_label.setObjectName("OverviewFootnote")
            self.description_label.setWordWrap(True)
            self.description_label.setAlignment(QtCore.Qt.AlignCenter)
            root.addSpacing(12)
            root.addWidget(self.description_label)
        else:
            self.description_label = QtWidgets.QLabel("")

        # 兼容性占位
        self.sample_original = _DummyPanel()
        self.sample_result = _DummyPanel()

    def _create_stats_card(self, title: str, value: str, subtitle: str) -> QtWidgets.QFrame:
        """创建统计卡片"""
        card = QtWidgets.QFrame()
        card.setObjectName("OverviewStatsCard")
        
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        title_label = QtWidgets.QLabel(title)
        title_label.setObjectName("OverviewStatsTitle")
        
        value_label = QtWidgets.QLabel(value)
        value_label.setObjectName("OverviewStatsValue")
        
        subtitle_label = QtWidgets.QLabel(subtitle)
        subtitle_label.setObjectName("OverviewStatsSubtitle")
        subtitle_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(subtitle_label)
        layout.addStretch(1)

        # 存储引用以便更新
        card._value_label = value_label
        card._subtitle_label = subtitle_label
        
        return card

    def _connect_signals(self):
        self.btn_start.clicked.connect(self.start_detection_requested.emit)
        self.btn_demo.clicked.connect(self.load_demo_requested.emit)
        self.btn_history.clicked.connect(self.history_requested.emit)
        self.btn_analytics.clicked.connect(self.analytics_requested.emit)
        self.btn_settings.clicked.connect(self.settings_requested.emit)

    def update_datetime(self, text: str):
        self.datetime_badge.setText(text)

    def update_status(self, text: str):
        self.system_status_badge.setText(text)

    def update_model_info(self, model_info: ModelInfo):
        self.model_badge.setText(f"模型：{model_info.model_name}")
        self.device_badge.setText(f"设备：{model_info.device.upper()}")
        self.search_hint_label.setText(
            f"当前使用 {model_info.model_name}，选择图片、文件夹、视频或摄像头后，进入检测工作台"
        )

    def update_system_stats(self, stats: Dict[str, str]):
        if "records" in self.stats_cards:
            self.stats_cards["records"]._value_label.setText(stats.get("records", "0"))
        if "targets" in self.stats_cards:
            self.stats_cards["targets"]._value_label.setText(stats.get("targets", "0"))
        if "avg_time" in self.stats_cards:
            self.stats_cards["avg_time"]._value_label.setText(stats.get("avg_time", "--"))
        if "latest_time" in self.stats_cards:
            card = self.stats_cards["latest_time"]
            latest_time = stats.get("latest_time", "--")
            card._value_label.setText(latest_time)
            card._subtitle_label.setText("最近任务时间" if latest_time != "--" else "暂无历史任务")

    def update_samples(self, original_image, result_image, original_note: str, result_note: str):
        pass


class _DummyPanel:
    def set_image(self, *args, **kwargs):
        pass

    def setVisible(self, *args, **kwargs):
        pass
