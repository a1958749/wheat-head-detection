from __future__ import annotations

from typing import List

import cv2
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from app.models import DetectionItem, RuntimeState
from app.widgets import (
    InfoRow,
    NoWheelDoubleSpinBox,
    NoWheelSpinBox,
    SectionCard,
    StatusChip,
    ToolbarButton,
    apply_shadow,
)
from tool.tools import resize_with_padding


# ─────────────────────────────────────────────────────────────────
#  ImageStage  — pure stretch label, zero height cap
# ─────────────────────────────────────────────────────────────────
class ImageStage(QtWidgets.QLabel):
    def __init__(self, placeholder: str):
        super().__init__(placeholder)
        self._image = None
        self._last_size = (0, 0)
        self._rendering = False  # Flag to prevent recursive rendering
        self.setObjectName("ImageStage")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(180)
        # Use Ignored policy to prevent pixmap from affecting layout
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored,
            QtWidgets.QSizePolicy.Ignored,
        )
        self.setScaledContents(False)

    def set_placeholder(self, text: str):
        self._image = None
        self.setPixmap(QtGui.QPixmap())
        self.setText(text)

    def set_image(self, image, _note: str = ""):
        if image is None:
            self.set_placeholder("暂无图像")
            return
        self._image = image.copy()
        self._render()

    def _render(self):
        if self._image is None or self._rendering:
            return
        self._rendering = True
        try:
            w = max(self.width(), 300)
            h = max(self.height(), 180)
            # Cap the size to prevent infinite growth
            w = min(w, 1200)
            h = min(h, 800)
            
            buf = resize_with_padding(self._image, w, h, [238, 242, 239])
            buf = cv2.cvtColor(buf, cv2.COLOR_BGR2RGB)
            qi = QtGui.QImage(buf.data, buf.shape[1], buf.shape[0],
                              buf.shape[1] * 3, QtGui.QImage.Format_RGB888)
            self.setText("")
            pixmap = QtGui.QPixmap.fromImage(qi)
            # Scale pixmap to fit without changing widget size
            scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
        finally:
            self._rendering = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Disable automatic re-rendering on resize to prevent infinite loops
        pass


# ─────────────────────────────────────────────────────────────────
#  StatChip — compact horizontal pill: LABEL ··· VALUE unit
# ─────────────────────────────────────────────────────────────────
class StatChip(QtWidgets.QFrame):
    def __init__(self, label: str, default: str = "--", unit: str = ""):
        super().__init__()
        self.setObjectName("MetricTile")
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(4)

        self._lbl = QtWidgets.QLabel(label)
        self._lbl.setObjectName("MetricLabel")
        self._lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self._val = QtWidgets.QLabel(default)
        self._val.setObjectName("MetricValue")
        self._val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._unit = QtWidgets.QLabel(unit)
        self._unit.setObjectName("MetricFoot")
        self._unit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lay.addWidget(self._lbl)
        lay.addStretch(1)
        lay.addWidget(self._val)
        lay.addWidget(self._unit)

    def set_value(self, val: str, unit: str = ""):
        self._val.setText(str(val))
        if unit:
            self._unit.setText(str(unit))


# ─────────────────────────────────────────────────────────────────
#  WorkbenchPage
# ─────────────────────────────────────────────────────────────────
class WorkbenchPage(QtWidgets.QWidget):
    select_image_requested   = QtCore.pyqtSignal()
    select_folder_requested  = QtCore.pyqtSignal()
    select_video_requested   = QtCore.pyqtSignal()
    connect_camera_requested = QtCore.pyqtSignal()
    start_requested          = QtCore.pyqtSignal()
    pause_requested          = QtCore.pyqtSignal()
    resume_requested         = QtCore.pyqtSignal()
    stop_requested           = QtCore.pyqtSignal()
    clear_requested          = QtCore.pyqtSignal()
    export_requested         = QtCore.pyqtSignal()
    load_demo_requested      = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PageSurface")
        self._device_value          = "cpu"
        self._class_filter_value    = None
        self._display_mode          = "dual"
        self._source_type           = "未选择"
        self._source_path           = "请选择图片、文件夹、视频或摄像头。"
        self._current_summary_text  = "当前尚未开始检测。"
        self._session_summary_text  = "当前会话暂无记录。"
        self._build_ui()

    # ── Main build ────────────────────────────────────────────────
    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        # ── Top: 3-column body ─────────────────────────────────────
        body = QtWidgets.QHBoxLayout()
        body.setSpacing(10)
        root.addLayout(body, 1)   # stretch=1 → consumes all space above table

        left = self._make_left()
        left.setFixedWidth(260)
        body.addWidget(left)

        body.addWidget(self._make_center(), 1)   # flex centre

        right = self._make_right()
        right.setFixedWidth(280)
        body.addWidget(right)

        # ── Bottom: session results table (compact, capped) ────────
        root.addWidget(self._make_table())

        # Signals
        self.btn_select_image.clicked.connect(self.select_image_requested.emit)
        self.btn_select_folder.clicked.connect(self.select_folder_requested.emit)
        self.btn_select_video.clicked.connect(self.select_video_requested.emit)
        self.btn_connect_camera.clicked.connect(self.connect_camera_requested.emit)
        self.btn_load_demo.clicked.connect(self.load_demo_requested.emit)
        self.btn_start.clicked.connect(self.start_requested.emit)
        self.btn_pause.clicked.connect(self.pause_requested.emit)
        self.btn_resume.clicked.connect(self.resume_requested.emit)
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        self.btn_clear.clicked.connect(self.clear_requested.emit)
        self.btn_export.clicked.connect(self.export_requested.emit)
        self.toggle_group.idClicked.connect(self._switch_view)
        self._refresh_summary()

    # ── Left column ───────────────────────────────────────────────
    def _make_left(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        vl = QtWidgets.QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(10)

        # Input source selection
        ic = SectionCard("输入选择", "", with_bg=True)
        self.btn_select_image = ToolbarButton("📷 导入图片")
        self.btn_select_folder = ToolbarButton("📁 导入文件夹")
        self.btn_select_video = ToolbarButton("🎬 导入视频")
        self.btn_connect_camera = ToolbarButton("📹 连接摄像头")
        self.btn_load_demo = ToolbarButton("⭐ 加载示例", role="accent")

        # 使用垂直布局避免按钮重叠
        for button in (
            self.btn_select_image,
            self.btn_select_folder,
            self.btn_select_video,
            self.btn_connect_camera,
        ):
            button.setMinimumHeight(36)
            button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            ic.layout.addWidget(button)
        
        self.btn_load_demo.setMinimumHeight(36)
        self.btn_load_demo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        ic.layout.addSpacing(4)
        ic.layout.addWidget(self.btn_load_demo)
        vl.addWidget(ic)

        # Inference parameters
        pc = SectionCard("推理参数", "", with_bg=True)
        self.conf_spin = NoWheelDoubleSpinBox()
        self.conf_spin.setRange(0.01, 0.99)
        self.conf_spin.setSingleStep(0.01)
        self.conf_spin.setDecimals(2)
        self.conf_spin.setValue(0.40)

        self.imgsz_spin = NoWheelSpinBox()
        self.imgsz_spin.setRange(320, 2048)
        self.imgsz_spin.setSingleStep(32)
        self.imgsz_spin.setValue(640)

        for label_text, editor in (("置信度", self.conf_spin), ("尺寸", self.imgsz_spin)):
            row = QtWidgets.QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)
            label = QtWidgets.QLabel(label_text)
            label.setObjectName("InlineFieldLabel")
            label.setFixedWidth(42)
            editor.setMinimumHeight(34)
            editor.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            editor.setAlignment(Qt.AlignCenter)
            row.addWidget(label)
            row.addWidget(editor, 1)
            pc.layout.addLayout(row)
        vl.addWidget(pc)

        # Run control
        ac = SectionCard("运行控制", "", with_bg=True)
        self.btn_start = ToolbarButton("▶ 开始检测", role="primary")
        self.btn_stop = ToolbarButton("⏹ 停止")
        self.btn_clear = ToolbarButton("🗑 清空")
        self.btn_export = ToolbarButton("📤 导出")
        self.btn_pause = ToolbarButton("⏸ 暂停")
        self.btn_resume = ToolbarButton("▶ 继续")
        self.btn_pause.setVisible(False)
        self.btn_resume.setVisible(False)

        self.btn_start.setMinimumHeight(40)
        self.btn_start.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        ac.layout.addWidget(self.btn_start)

        # 使用水平布局放置停止、清空、导出按钮
        action_row = QtWidgets.QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(6)
        for button in (self.btn_stop, self.btn_clear, self.btn_export):
            button.setMinimumHeight(34)
            button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            action_row.addWidget(button)
        ac.layout.addLayout(action_row)
        vl.addWidget(ac)

        vl.addStretch(1)
        return w

    # ── Centre column ─────────────────────────────────────────────
    def _make_center(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        vl = QtWidgets.QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(8)

        # ── 4 stat chips — compact horizontal row ────
        self.chip_target = StatChip("目标数",    "0",  "个")
        self.chip_avg    = StatChip("平均置信度", "--", "")
        self.chip_max    = StatChip("最高置信度", "--", "")
        self.chip_time   = StatChip("推理耗时",  "--", "")
        cr = QtWidgets.QHBoxLayout()
        cr.setSpacing(6)
        for ch in (self.chip_target, self.chip_avg, self.chip_max, self.chip_time):
            cr.addWidget(ch, 1)
        vl.addLayout(cr)

        # ── Image viewer card ──────────────────────────────────────
        vc = QtWidgets.QFrame()
        vc.setObjectName("SectionCard")
        apply_shadow(vc, blur_radius=18, offset_y=4)
        vcl = QtWidgets.QVBoxLayout(vc)
        vcl.setContentsMargins(14, 10, 14, 10)
        vcl.setSpacing(6)

        # Header row: title + toggle buttons
        hdr = QtWidgets.QHBoxLayout()
        hdr.setSpacing(8)
        self.viewer_title = QtWidgets.QLabel("图像预览")
        self.viewer_title.setObjectName("PanelTitle")
        self.viewer_summary = QtWidgets.QLabel("选择输入源后开始检测")
        self.viewer_summary.setObjectName("MetaText")
        self.viewer_summary.setWordWrap(True)
        hdr.addWidget(self.viewer_title)
        hdr.addWidget(self.viewer_summary, 1)

        self.toggle_result   = ToolbarButton("结果")
        self.toggle_original = ToolbarButton("原图")
        self.toggle_result.setCheckable(True)
        self.toggle_original.setCheckable(True)
        self.toggle_result.setChecked(True)
        self.toggle_group = QtWidgets.QButtonGroup(self)
        self.toggle_group.setExclusive(True)
        self.toggle_group.addButton(self.toggle_result,   0)
        self.toggle_group.addButton(self.toggle_original, 1)
        self.toggle_result.setMinimumHeight(28)
        self.toggle_original.setMinimumHeight(28)
        self.toggle_result.setMinimumWidth(60)
        self.toggle_original.setMinimumWidth(60)
        hdr.addWidget(self.toggle_result)
        hdr.addWidget(self.toggle_original)
        vcl.addLayout(hdr)

        # ── Image stack — fills ALL remaining card height ──
        self.viewer_stack   = QtWidgets.QStackedWidget()
        self.result_panel   = ImageStage("点击左侧按钮选择输入源，然后开始检测")
        self.original_panel = ImageStage("原始图像预览")
        self.viewer_stack.addWidget(self.result_panel)
        self.viewer_stack.addWidget(self.original_panel)
        self.viewer_stack.setMinimumHeight(300)
        vcl.addWidget(self.viewer_stack, 1)

        vl.addWidget(vc, 1)
        return w

    # ── Right column ──────────────────────────────────────────────
    def _make_right(self) -> QtWidgets.QWidget:
        """
        Two-section layout:
          1. Compact status card — badges, progress
          2. Detection items table (stretch=1) — fills remaining space
        """
        w = QtWidgets.QWidget()
        vl = QtWidgets.QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(8)

        # ── 1. Compact status card ──────────────────────
        sc = SectionCard("任务状态", "", with_bg=True)
        sc_inner = QtWidgets.QVBoxLayout()
        sc_inner.setSpacing(6)

        # Status badge + source type on one row
        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(8)
        self.run_status_badge = StatusChip("待机")
        self.source_row = InfoRow("类型", "未选择")
        top_row.addWidget(self.run_status_badge)
        top_row.addWidget(self.source_row, 1)
        sc_inner.addLayout(top_row)

        # Progress row inline
        prog_row = QtWidgets.QHBoxLayout()
        prog_row.setSpacing(6)
        prog_label = QtWidgets.QLabel("进度")
        prog_label.setObjectName("MetaText")
        prog_label.setFixedWidth(32)
        self.progress_row = QtWidgets.QLabel("-")
        self.progress_row.setObjectName("MetaText")
        prog_row.addWidget(prog_label)
        prog_row.addWidget(self.progress_row, 1)
        sc_inner.addLayout(prog_row)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumHeight(12)
        sc_inner.addWidget(self.progress_bar)

        # Compact summary text
        self.summary_browser = QtWidgets.QTextBrowser()
        self.summary_browser.setObjectName("SummaryBrowser")
        self.summary_browser.setMaximumHeight(55)
        sc.layout.addLayout(sc_inner)
        sc.layout.addWidget(self.summary_browser)
        vl.addWidget(sc)

        # ── 2. Detection targets table — stretch to fill remaining ─
        items_card = SectionCard("检测目标", "", with_bg=True)
        self.current_items_table = QtWidgets.QTableWidget(0, 3)
        self.current_items_table.setObjectName("CompactTable")
        self.current_items_table.setHorizontalHeaderLabels(["类别", "置信度", "边界框"])
        self.current_items_table.verticalHeader().setVisible(False)
        self.current_items_table.verticalHeader().setDefaultSectionSize(26)
        self.current_items_table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        self.current_items_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self.current_items_table.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection)
        self.current_items_table.setAlternatingRowColors(True)
        self.current_items_table.setWordWrap(False)
        h = self.current_items_table.horizontalHeader()
        h.setStretchLastSection(False)
        h.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        items_card.layout.addWidget(self.current_items_table)
        vl.addWidget(items_card, 1)

        return w

    # ── Bottom table ──────────────────────────────────────────────
    def _make_table(self) -> QtWidgets.QFrame:
        """Session history table — compact."""
        tc = SectionCard("检测结果表", "点击行可回看结果", with_bg=True)
        self.result_table = QtWidgets.QTableWidget(0, 9)
        self.result_table.setHorizontalHeaderLabels(
            ["#", "类型", "文件名", "时间", "结果摘要",
             "目标", "置信度", "耗时", "路径"])
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.verticalHeader().setDefaultSectionSize(28)
        self.result_table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        self.result_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self.result_table.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setWordWrap(False)
        self.result_table.setHorizontalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.result_table.setMinimumHeight(60)
        self.result_table.setMaximumHeight(160)
        h = self.result_table.horizontalHeader()
        for i in range(9):
            h.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
        h.setSectionResizeMode(8, QtWidgets.QHeaderView.Stretch)
        tc.layout.addWidget(self.result_table)
        return tc

    # ── Internal ──────────────────────────────────────────────────
    def _switch_view(self, index: int):
        self.viewer_stack.setCurrentIndex(index)

    def _refresh_summary(self):
        cur  = "<br/>".join(l for l in self._current_summary_text.splitlines() if l.strip())
        sess = "<br/>".join(l for l in self._session_summary_text.splitlines() if l.strip())
        self.summary_browser.setHtml(
            f"<div style='line-height:1.7;font-size:11px;'>"
            f"<b>本次</b> {cur or '—'}&nbsp;&nbsp;"
            f"<b>会话</b> {sess or '—'}"
            f"</div>"
        )

    # ── Public API (all original signatures preserved) ─────────────
    def set_display_mode(self, mode: str):
        self._display_mode = mode
        show = mode == "dual"
        self.toggle_original.setVisible(show)
        if not show and self.viewer_stack.currentWidget() is self.original_panel:
            self.toggle_result.setChecked(True)
            self.viewer_stack.setCurrentWidget(self.result_panel)

    def current_param_values(self):
        return {
            "conf":    round(self.conf_spin.value(), 2),
            "imgsize": int(self.imgsz_spin.value()),
            "device":  self._device_value,
            "classes": self._class_filter_value,
        }

    def apply_runtime_config(self, config: dict):
        mc = config.get("MODEL", {})
        dc = config.get("DISPLAY", {})
        self.conf_spin.setValue(float(mc.get("conf",    0.4)))
        self.imgsz_spin.setValue(int(mc.get("imgsize",  640)))
        self._device_value       = str(mc.get("device", "cpu"))
        self._class_filter_value = mc.get("classes")
        self.set_display_mode(str(dc.get("image_view_mode", "dual")))

    def set_source_info(self, source_type: str, source_path: str):
        self._source_type = source_type or "未选择"
        self._source_path = source_path or "—"
        self.source_row.set_value(self._source_type)
        if self._source_type == "未选择":
            self.progress_row.setText("-")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    def update_runtime(self, state: RuntimeState):
        self.source_row.set_value(state.source_type or self._source_type)
        if state.progress_total > 0:
            self.progress_row.setText(
                f"{state.progress_current} / {state.progress_total}")
            self.progress_bar.setRange(0, max(state.progress_total, 1))
            self.progress_bar.setValue(
                min(state.progress_current, state.progress_total))
        elif state.status.value == "running" and state.source_type == "实时摄像头":
            self.progress_row.setText("实时流")
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_row.setText("-")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    def update_previews(self, original_image, result_image,
                        original_note: str, result_note: str):
        self.original_panel.set_image(original_image, original_note)
        self.result_panel.set_image(result_image, result_note)
        self.viewer_title.setText(result_note or "检测结果")
        self.viewer_summary.setText(result_note)
        self.toggle_result.setChecked(True)
        self.viewer_stack.setCurrentWidget(self.result_panel)

    def update_detection_summary(
        self,
        source_type: str,
        target_count,
        average_confidence: str,
        max_confidence: str,
        inference_ms: str,
        summary_text: str,
    ):
        self.source_row.set_value(source_type or self._source_type)
        self.chip_target.set_value(str(target_count), "个")
        self.chip_avg.set_value(str(average_confidence))
        self.chip_max.set_value(str(max_confidence))
        self.chip_time.set_value(str(inference_ms))
        self._current_summary_text = summary_text or "当前尚未开始检测。"
        self._refresh_summary()

    def update_session_summary(self, text: str):
        self._session_summary_text = text or "当前会话暂无记录。"
        self._refresh_summary()

    def update_current_detection_items(self, detections: List[DetectionItem]):
        items = sorted(detections, key=lambda x: x.confidence, reverse=True)[:30]
        self.current_items_table.setRowCount(len(items))
        for row, item in enumerate(items):
            vals = [
                item.display_name or item.class_name,
                f"{item.confidence * 100:.1f}%",
                f"[{item.box[0]}, {item.box[1]}, {item.box[2]}, {item.box[3]}]",
            ]
            for col, val in enumerate(vals):
                ti = QtWidgets.QTableWidgetItem(val)
                ti.setTextAlignment(
                    Qt.AlignCenter if col != 2
                    else Qt.AlignVCenter | Qt.AlignLeft)
                self.current_items_table.setItem(row, col, ti)

    def update_result_table(self, rows: List[List[object]]):
        self.result_table.setRowCount(len(rows))
        for ri, row_vals in enumerate(rows):
            for ci, val in enumerate(row_vals):
                ti = QtWidgets.QTableWidgetItem(str(val))
                ti.setTextAlignment(
                    Qt.AlignCenter if ci in {0, 1, 5, 6, 7}
                    else Qt.AlignVCenter | Qt.AlignLeft)
                self.result_table.setItem(ri, ci, ti)