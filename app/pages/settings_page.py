from __future__ import annotations

from typing import Dict, List

from PyQt5 import QtCore, QtWidgets

from app.widgets import NoWheelComboBox, NoWheelDoubleSpinBox, NoWheelSpinBox, SectionCard, ToolbarButton


class SettingsPage(QtWidgets.QWidget):
    save_requested = QtCore.pyqtSignal()
    reload_model_requested = QtCore.pyqtSignal()
    restore_default_requested = QtCore.pyqtSignal()
    open_output_requested = QtCore.pyqtSignal()
    choose_weight_requested = QtCore.pyqtSignal()
    choose_output_requested = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PageSurface")
        self._build_ui()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        root.addWidget(scroll)

        container = QtWidgets.QWidget()
        scroll.setWidget(container)
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(14)

        # ── Action Bar ─────────────────────────────────────────────
        action_card = SectionCard("系统设置", with_bg=True)
        action_row = QtWidgets.QHBoxLayout()
        action_row.setSpacing(10)
        self.btn_save = ToolbarButton("保存配置", role="primary")
        self.btn_reload_model = ToolbarButton("重新加载模型")
        self.btn_restore = ToolbarButton("恢复默认", role="danger")
        self.btn_open_output = ToolbarButton("打开输出目录")
        action_row.addWidget(self.btn_save)
        action_row.addWidget(self.btn_reload_model)
        action_row.addWidget(self.btn_restore)
        action_row.addWidget(self.btn_open_output)
        action_row.addStretch(1)
        action_card.layout.addLayout(action_row)
        layout.addWidget(action_card)

        # ── Settings Grid ──────────────────────────────────────────
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        layout.addLayout(grid)

        # Model Settings
        model_card = SectionCard("模型设置", with_bg=True)
        model_form = QtWidgets.QFormLayout()
        model_form.setSpacing(10)

        weight_row = QtWidgets.QHBoxLayout()
        weight_row.setSpacing(8)
        self.weight_combo = NoWheelComboBox()
        self.btn_choose_weight = ToolbarButton("选择权重")
        weight_row.addWidget(self.weight_combo, 1)
        weight_row.addWidget(self.btn_choose_weight)

        self.model_name_edit = QtWidgets.QLineEdit()
        self.baseline_edit = QtWidgets.QLineEdit()
        self.backbone_edit = QtWidgets.QLineEdit()
        self.description_edit = QtWidgets.QPlainTextEdit()
        self.description_edit.setMaximumHeight(72)
        self.improvements_edit = QtWidgets.QPlainTextEdit()
        self.improvements_edit.setMaximumHeight(90)
        self.metrics_edit = QtWidgets.QPlainTextEdit()
        self.metrics_edit.setMaximumHeight(72)

        model_form.addRow("权重文件", weight_row)
        model_form.addRow("模型名称", self.model_name_edit)
        model_form.addRow("基线模型", self.baseline_edit)
        model_form.addRow("Backbone", self.backbone_edit)
        model_form.addRow("模型说明", self.description_edit)
        model_form.addRow("改进策略", self.improvements_edit)
        model_form.addRow("评价指标", self.metrics_edit)
        model_card.layout.addLayout(model_form)
        grid.addWidget(model_card, 0, 0)

        # Runtime Settings
        runtime_card = SectionCard("推理设置", with_bg=True)
        runtime_form = QtWidgets.QFormLayout()
        runtime_form.setSpacing(10)
        self.conf_spin = NoWheelDoubleSpinBox()
        self.conf_spin.setRange(0.01, 0.99)
        self.conf_spin.setSingleStep(0.01)
        self.conf_spin.setDecimals(2)
        self.imgsz_spin = NoWheelSpinBox()
        self.imgsz_spin.setRange(320, 2048)
        self.imgsz_spin.setSingleStep(32)
        self.device_combo = NoWheelComboBox()
        self.device_combo.addItems(["cpu", "0", "1"])
        self.camera_spin = NoWheelSpinBox()
        self.camera_spin.setRange(0, 9)
        self.interval_spin = NoWheelSpinBox()
        self.interval_spin.setRange(20, 1000)
        self.history_limit_spin = NoWheelSpinBox()
        self.history_limit_spin.setRange(200, 10000)
        self.class_filter_edit = QtWidgets.QLineEdit()
        self.class_filter_edit.setPlaceholderText("可选，例如 [0]")
        runtime_form.addRow("置信度", self.conf_spin)
        runtime_form.addRow("输入尺寸", self.imgsz_spin)
        runtime_form.addRow("运行设备", self.device_combo)
        runtime_form.addRow("摄像头编号", self.camera_spin)
        runtime_form.addRow("播放间隔(ms)", self.interval_spin)
        runtime_form.addRow("历史记录上限", self.history_limit_spin)
        runtime_form.addRow("类别筛选", self.class_filter_edit)
        runtime_card.layout.addLayout(runtime_form)
        grid.addWidget(runtime_card, 0, 1)

        # Output Settings
        output_card = SectionCard("输出设置", with_bg=True)
        output_form = QtWidgets.QFormLayout()
        output_form.setSpacing(10)
        output_row = QtWidgets.QHBoxLayout()
        output_row.setSpacing(8)
        self.output_edit = QtWidgets.QLineEdit()
        self.btn_choose_output = ToolbarButton("选择目录")
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(self.btn_choose_output)
        output_form.addRow("输出目录", output_row)
        output_card.layout.addLayout(output_form)

        self.auto_save_images = QtWidgets.QCheckBox("自动保存结果图")
        self.auto_save_records = QtWidgets.QCheckBox("自动保存结构化记录")
        self.auto_export_summary = QtWidgets.QCheckBox("批量任务完成后自动导出会话摘要")
        output_card.layout.addWidget(self.auto_save_images)
        output_card.layout.addWidget(self.auto_save_records)
        output_card.layout.addWidget(self.auto_export_summary)
        output_card.layout.addStretch(1)
        grid.addWidget(output_card, 1, 0)

        # Display Settings
        display_card = SectionCard("显示设置", with_bg=True)
        display_form = QtWidgets.QFormLayout()
        display_form.setSpacing(10)
        self.theme_combo = NoWheelComboBox()
        self.theme_combo.addItems(["agriculture_light", "dark", "wheat_gold"])
        self.image_mode_combo = NoWheelComboBox()
        self.image_mode_combo.addItems(["dual", "single"])
        self.table_font_spin = NoWheelSpinBox()
        self.table_font_spin.setRange(9, 16)
        display_form.addRow("主题风格", self.theme_combo)
        display_form.addRow("图像显示方式", self.image_mode_combo)
        display_form.addRow("表格字号", self.table_font_spin)
        display_card.layout.addLayout(display_form)
        display_card.layout.addStretch(1)
        grid.addWidget(display_card, 1, 1)

        # Hidden note for compatibility
        self.display_note = QtWidgets.QLabel("")
        self.display_note.setVisible(False)

        # Connect signals
        self.btn_choose_weight.clicked.connect(self.choose_weight_requested.emit)
        self.btn_choose_output.clicked.connect(self.choose_output_requested.emit)
        self.btn_save.clicked.connect(self.save_requested.emit)
        self.btn_reload_model.clicked.connect(self.reload_model_requested.emit)
        self.btn_restore.clicked.connect(self.restore_default_requested.emit)
        self.btn_open_output.clicked.connect(self.open_output_requested.emit)

    def set_weight_candidates(self, candidates: List[str], current_value: str):
        self.weight_combo.blockSignals(True)
        self.weight_combo.clear()
        self.weight_combo.addItems(candidates)
        if current_value:
            if self.weight_combo.findText(current_value) < 0:
                self.weight_combo.addItem(current_value)
            self.weight_combo.setCurrentText(current_value)
        self.weight_combo.blockSignals(False)

    def load_config(self, config: Dict):
        model_cfg = config["MODEL"]
        runtime_cfg = config["RUNTIME"]
        feature_cfg = config["FEATURES"]
        display_cfg = config["DISPLAY"]
        path_cfg = config["PATHS"]

        self.model_name_edit.setText(str(model_cfg.get("model_name", "")))
        self.baseline_edit.setText(str(model_cfg.get("baseline_name", "")))
        self.backbone_edit.setText(str(model_cfg.get("backbone", "")))
        self.description_edit.setPlainText(str(model_cfg.get("description", "")))
        self.improvements_edit.setPlainText("\n".join(model_cfg.get("improvement_points", [])))
        self.metrics_edit.setPlainText("\n".join(f"{key}={value}" for key, value in model_cfg.get("metrics", {}).items()))
        self.conf_spin.setValue(float(model_cfg.get("conf", 0.4)))
        self.imgsz_spin.setValue(int(model_cfg.get("imgsize", 640)))
        self.device_combo.setCurrentText(str(model_cfg.get("device", "cpu")))
        self.camera_spin.setValue(int(runtime_cfg.get("camera_index", 0)))
        self.interval_spin.setValue(int(runtime_cfg.get("playback_interval_ms", 80)))
        self.history_limit_spin.setValue(int(runtime_cfg.get("history_limit", 2000)))
        self.class_filter_edit.setText("" if model_cfg.get("classes") is None else str(model_cfg.get("classes")))
        self.output_edit.setText(str(path_cfg.get("output_root", "")))
        self.auto_save_images.setChecked(bool(feature_cfg.get("auto_save_result_image", True)))
        self.auto_save_records.setChecked(bool(feature_cfg.get("auto_save_structured_record", True)))
        self.auto_export_summary.setChecked(bool(feature_cfg.get("auto_export_session_summary", False)))
        self.theme_combo.setCurrentText(str(display_cfg.get("theme", "agriculture_light")))
        self.image_mode_combo.setCurrentText(str(display_cfg.get("image_view_mode", "dual")))
        self.table_font_spin.setValue(int(display_cfg.get("table_font_size", 10)))

    def build_config_patch(self) -> Dict:
        improvements = [line.strip() for line in self.improvements_edit.toPlainText().splitlines() if line.strip()]
        metrics = {}
        for line in self.metrics_edit.toPlainText().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                metrics[key.strip()] = value.strip()
        return {
            "MODEL": {
                "weight": self.weight_combo.currentText().strip(),
                "model_name": self.model_name_edit.text().strip(),
                "baseline_name": self.baseline_edit.text().strip(),
                "backbone": self.backbone_edit.text().strip(),
                "description": self.description_edit.toPlainText().strip(),
                "improvement_points": improvements,
                "metrics": metrics,
                "conf": round(self.conf_spin.value(), 2),
                "imgsize": int(self.imgsz_spin.value()),
                "device": self.device_combo.currentText(),
                "classes": self.class_filter_edit.text().strip() or None,
            },
            "RUNTIME": {
                "camera_index": int(self.camera_spin.value()),
                "playback_interval_ms": int(self.interval_spin.value()),
                "history_limit": int(self.history_limit_spin.value()),
            },
            "PATHS": {
                "output_root": self.output_edit.text().strip(),
            },
            "FEATURES": {
                "auto_save_result_image": self.auto_save_images.isChecked(),
                "auto_save_structured_record": self.auto_save_records.isChecked(),
                "auto_export_session_summary": self.auto_export_summary.isChecked(),
            },
            "DISPLAY": {
                "theme": self.theme_combo.currentText(),
                "image_view_mode": self.image_mode_combo.currentText(),
                "table_font_size": int(self.table_font_spin.value()),
            },
        }
