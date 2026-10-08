from __future__ import annotations

import json
import os
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import cv2
from app.detection import DetectionEngine
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt

from app.analytics import (
    build_analysis_summary,
    build_class_series,
    build_confidence_histogram,
    build_input_type_series,
    build_recent_target_series,
)
from app.config import (
    CONFIG_PATH,
    build_model_info,
    deep_merge,
    load_config,
    resolve_path,
    restore_default_config,
    save_config,
    scan_weight_candidates,
)
from app.models import DetectionItem, DetectionRecord, RuntimeStatus
from app.pages.analytics_page import AnalyticsPage
from app.pages.history_page import HistoryPage
from app.pages.overview_page import OverviewPage
from app.pages.settings_page import SettingsPage
from app.pages.workbench_page import WorkbenchPage
from app.state import RuntimeStateManager
from app.storage import (
    RecordRepository,
    build_class_counts,
    build_result_summary,
    build_top_class,
    current_time_text,
    format_source_type,
    read_image,
)
from app.styles import THEMES, build_stylesheet, status_color
from app.widgets import AppMessageDialog, apply_shadow


PAGE_INFO = {
    "overview": ("系统总览", "展示系统概况、模型信息、历史统计与样例效果。"),
    "workbench": ("检测工作台", "完成输入选择、参数调整、检测处理、结果查看与批量任务管理。"),
    "history": ("历史记录", "管理系统历史检测记录，支持搜索、筛选、回看和导出。"),
    "analytics": ("数据分析", "基于真实记录生成统计卡片和图表，用于展示模型结果与工程价值。"),
    "settings": ("系统设置", "统一配置模型、推理参数、输出策略、主题风格与显示方案。"),
}


def confidence_text(value: float) -> str:
    return f"{float(value) * 100:.1f}%"


def ms_text(value: float) -> str:
    return f"{round(float(value), 2)} ms"


def first_available_image(*paths: str):
    for path in paths:
        if not path:
            continue
        image = read_image(path)
        if image is not None:
            return image
    return None


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config(CONFIG_PATH)
        self.runtime_manager = RuntimeStateManager()
        self.engine = DetectionEngine()
        self.repository: Optional[RecordRepository] = None
        self.history_records: List[DetectionRecord] = []
        self.filtered_history_records: List[DetectionRecord] = []

        self.current_input_type = ""
        self.current_input_path = ""
        self.current_input_name = ""
        self.current_image = None
        self.current_result_image = None
        self.current_detections: List[DetectionItem] = []
        self.current_record: Optional[DetectionRecord] = None
        self.pending_files: List[str] = []
        self.pending_total = 0
        self.current_index = 0
        self.video_capture = None

        self.process_timer = QtCore.QTimer(self)
        self.process_timer.timeout.connect(self.process_next_step)
        self.clock_timer = QtCore.QTimer(self)
        self.clock_timer.timeout.connect(self.refresh_clock)
        self.clock_timer.start(1000)

        self.setup_window()
        self.setup_ui()
        self.connect_signals()
        self.apply_current_theme()
        self.refresh_clock()
        self.initialize_system()

    def setup_window(self):
        self.setWindowTitle(self.config["APP"]["system_title"])
        self.resize(1680, 980)
        self.setMinimumSize(1500, 920)
        self.setStatusBar(QtWidgets.QStatusBar(self))

    def setup_ui(self):
        central = QtWidgets.QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        root = QtWidgets.QHBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(14)

        self.sidebar = QtWidgets.QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        apply_shadow(self.sidebar, blur_radius=18, offset_y=6)
        sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 18, 16, 18)
        sidebar_layout.setSpacing(12)

        self.brand_title = QtWidgets.QLabel(self.config["APP"]["system_title"])
        self.brand_title.setObjectName("BrandTitle")
        self.brand_title.setWordWrap(True)
        self.brand_subtitle = QtWidgets.QLabel(self.config["APP"]["system_subtitle"])
        self.brand_subtitle.setObjectName("BrandSubtitle")
        self.brand_subtitle.setWordWrap(True)
        sidebar_layout.addWidget(self.brand_title)
        sidebar_layout.addWidget(self.brand_subtitle)

        self.nav_buttons: Dict[str, QtWidgets.QPushButton] = {}
        for key in ("overview", "workbench", "history", "analytics", "settings"):
            button = QtWidgets.QPushButton(PAGE_INFO[key][0])
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            sidebar_layout.addWidget(button)
            self.nav_buttons[key] = button

        self.sidebar_session = QtWidgets.QLabel("当前会话：-")
        self.sidebar_session.setObjectName("SidebarInfo")
        self.sidebar_session.setWordWrap(True)
        self.sidebar_records = QtWidgets.QLabel("累计记录：0")
        self.sidebar_records.setObjectName("SidebarInfo")
        self.sidebar_runtime = QtWidgets.QLabel("运行状态：空闲")
        self.sidebar_runtime.setObjectName("SidebarInfo")
        sidebar_layout.addWidget(self.sidebar_session)
        sidebar_layout.addWidget(self.sidebar_records)
        sidebar_layout.addWidget(self.sidebar_runtime)
        sidebar_layout.addStretch(1)

        footer = QtWidgets.QLabel("小麦麦穗检测识别系统")
        footer.setObjectName("SidebarFooter")
        footer.setWordWrap(True)
        sidebar_layout.addWidget(footer)

        content = QtWidgets.QVBoxLayout()
        content.setSpacing(8)

        # Simple page title without frame
        self.topbar = QtWidgets.QWidget()
        self.topbar.setObjectName("PageTitleBar")
        topbar_layout = QtWidgets.QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(4, 8, 4, 8)
        topbar_layout.setSpacing(0)

        self.page_title = QtWidgets.QLabel("系统总览")
        self.page_title.setObjectName("PageTitleText")
        self.page_title.setStyleSheet("""
            font-size: 20px;
            font-weight: 800;
            color: #1A2820;
            background: transparent;
            padding: 0;
            margin: 0;
        """)
        topbar_layout.addWidget(self.page_title)
        topbar_layout.addStretch(1)
        
        # Hidden elements for compatibility
        self.page_subtitle = QtWidgets.QLabel("")
        self.page_subtitle.setVisible(False)
        self.topbar_model_chip = QtWidgets.QLabel("")
        self.topbar_model_chip.setVisible(False)
        self.topbar_device_chip = QtWidgets.QLabel("")
        self.topbar_device_chip.setVisible(False)
        self.topbar_session_chip = QtWidgets.QLabel("")
        self.topbar_session_chip.setVisible(False)
        self.global_datetime = QtWidgets.QLabel("")
        self.global_datetime.setVisible(False)
        self.global_status = QtWidgets.QLabel("")
        self.global_status.setVisible(False)
        self.global_message = QtWidgets.QLabel("")
        self.global_message.setVisible(False)

        self.stack = QtWidgets.QStackedWidget()
        self.overview_page = OverviewPage(
            self.config["APP"]["system_title"],
            self.config["APP"]["system_subtitle"],
            self.config["APP"]["overview_description"],
        )
        self.workbench_page = WorkbenchPage()
        self.history_page = HistoryPage()
        self.analytics_page = AnalyticsPage()
        self.settings_page = SettingsPage()
        self.stack.addWidget(self.overview_page)
        self.stack.addWidget(self.workbench_page)
        self.stack.addWidget(self.history_page)
        self.stack.addWidget(self.analytics_page)
        self.stack.addWidget(self.settings_page)

        content.addWidget(self.topbar)
        self.topbar.setVisible(False)  # 首页默认隐藏标题栏
        content.addWidget(self.stack, 1)
        root.addWidget(self.sidebar)
        root.addLayout(content, 1)

    def connect_signals(self):
        self.nav_buttons["overview"].clicked.connect(lambda: self.switch_page("overview"))
        self.nav_buttons["workbench"].clicked.connect(lambda: self.switch_page("workbench"))
        self.nav_buttons["history"].clicked.connect(lambda: self.switch_page("history"))
        self.nav_buttons["analytics"].clicked.connect(lambda: self.switch_page("analytics"))
        self.nav_buttons["settings"].clicked.connect(lambda: self.switch_page("settings"))

        self.overview_page.start_detection_requested.connect(lambda: self.switch_page("workbench"))
        self.overview_page.history_requested.connect(lambda: self.switch_page("history"))
        self.overview_page.analytics_requested.connect(lambda: self.switch_page("analytics"))
        self.overview_page.settings_requested.connect(lambda: self.switch_page("settings"))
        self.overview_page.load_demo_requested.connect(self.load_demo_image)

        self.workbench_page.select_image_requested.connect(self.select_image)
        self.workbench_page.select_folder_requested.connect(self.select_folder)
        self.workbench_page.select_video_requested.connect(self.select_video)
        self.workbench_page.connect_camera_requested.connect(self.toggle_camera_connection)
        self.workbench_page.start_requested.connect(self.start_task)
        self.workbench_page.pause_requested.connect(self.pause_task)
        self.workbench_page.resume_requested.connect(self.resume_task)
        self.workbench_page.stop_requested.connect(self.stop_task)
        self.workbench_page.clear_requested.connect(self.clear_current_session)
        self.workbench_page.export_requested.connect(self.export_current_session)
        self.workbench_page.load_demo_requested.connect(self.load_demo_image)
        self.workbench_page.result_table.cellClicked.connect(self.show_selected_session_record)

        self.history_page.refresh_requested.connect(self.refresh_history)
        self.history_page.export_selected_requested.connect(self.export_selected_history_record)
        self.history_page.export_all_requested.connect(self.export_all_history_records)
        self.history_page.delete_selected_requested.connect(self.delete_selected_history_record)
        self.history_page.clear_session_requested.connect(self.clear_current_session)
        self.history_page.open_result_dir_requested.connect(self.open_selected_result_directory)
        self.history_page.filters_changed.connect(self.apply_history_filters)
        self.history_page.history_table.cellClicked.connect(self.show_selected_history_record)

        self.analytics_page.refresh_requested.connect(self.refresh_dashboard_views)

        self.settings_page.save_requested.connect(self.save_settings)
        self.settings_page.reload_model_requested.connect(self.reload_model_from_settings)
        self.settings_page.restore_default_requested.connect(self.restore_defaults)
        self.settings_page.open_output_requested.connect(self.open_output_directory)
        self.settings_page.choose_weight_requested.connect(self.choose_weight_file)
        self.settings_page.choose_output_requested.connect(self.choose_output_directory)

    def show_info(self, title: str, text: str):
        AppMessageDialog.information(self, title, text)

    def show_success(self, title: str, text: str):
        AppMessageDialog.success(self, title, text)

    def show_warning(self, title: str, text: str):
        AppMessageDialog.warning(self, title, text)

    def show_error(self, title: str, text: str):
        AppMessageDialog.error(self, title, text)

    def ask_confirm(self, title: str, text: str) -> bool:
        return AppMessageDialog.confirm(self, title, text)

    def initialize_system(self):
        self.switch_page("overview")
        self.workbench_page.apply_runtime_config(self.config)
        self.load_settings_page()
        self.refresh_history()
        self.prepare_runtime_context()
        self.set_runtime_state(RuntimeStatus.IDLE, "系统已启动，点击开始检测时将尝试加载模型")

    def prepare_runtime_context(self):
        model_info = build_model_info(self.config)
        self.engine.model_info = model_info
        if self.repository is None:
            self.repository = RecordRepository(self.config["PATHS"]["output_root"], model_info)
        self.sidebar_session.setText(f"当前会话：{self.repository.session_id}")
        self.overview_page.update_model_info(model_info)
        self.update_context_chips()

    def switch_page(self, page_key: str):
        index_map = {"overview": 0, "workbench": 1, "history": 2, "analytics": 3, "settings": 4}
        self.stack.setCurrentIndex(index_map[page_key])
        self.page_title.setText(PAGE_INFO[page_key][0])
        self.page_subtitle.setText(PAGE_INFO[page_key][1])
        # 首页不显示标题栏
        self.topbar.setVisible(page_key != "overview")
        for key, button in self.nav_buttons.items():
            button.setChecked(key == page_key)

    def refresh_clock(self):
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.global_datetime.setText(now_text)
        self.overview_page.update_datetime(now_text)

    def apply_current_theme(self):
        theme_name = self.config["DISPLAY"].get("theme", self.config["RUNTIME"].get("default_theme", "agriculture_light"))
        table_font_size = int(self.config["DISPLAY"].get("table_font_size", 10))
        self.setStyleSheet(build_stylesheet(theme_name, table_font_size))
        self.apply_display_mode()
        self.apply_chart_theme(theme_name)
        state = self.runtime_manager.state
        self.update_status_views(state.status.value, state.message)
        self.update_context_chips()
        self.update_analytics()

    def apply_display_mode(self):
        mode = self.config["DISPLAY"].get("image_view_mode", "dual")
        show_original = mode == "dual"
        if hasattr(self.workbench_page, "set_display_mode"):
            self.workbench_page.set_display_mode(mode)
        else:
            self.workbench_page.original_panel.setVisible(show_original)
        self.overview_page.sample_original.setVisible(show_original)
        self.history_page.original_panel.setVisible(show_original)

    def apply_chart_theme(self, theme_name: str):
        palette = THEMES.get(theme_name, THEMES["agriculture_light"])
        for canvas in (
            self.analytics_page.chart_class.canvas,
            self.analytics_page.chart_conf.canvas,
            self.analytics_page.chart_input.canvas,
            self.analytics_page.chart_trend.canvas,
        ):
            canvas.set_palette(palette)

    def update_context_chips(self):
        model_name = self.engine.model_info.model_name if self.engine.model_info else "未加载"
        session_id = self.repository.session_id if self.repository else "-"
        self.topbar_model_chip.setText(f"模型：{model_name}")
        self.topbar_session_chip.setText(f"会话：{session_id}")

    def update_status_views(self, status_value: str, message: str):
        theme_name = self.config["DISPLAY"].get("theme", "agriculture_light")
        badge_color = status_color(status_value, theme_name)
        badge_style = f"background:{badge_color}; color:white; border-radius:10px; padding:5px 11px; font-weight:700;"
        status_text_map = {
            "idle": "待机",
            "ready": "就绪",
            "running": "运行中",
            "paused": "已暂停",
            "finished": "已完成",
            "error": "异常",
        }
        status_text = status_text_map.get(status_value, "待机")
        self.global_status.setText(status_text)
        self.global_status.setStyleSheet(badge_style)
        self.overview_page.system_status_badge.setStyleSheet(badge_style)
        self.workbench_page.run_status_badge.set_status(status_text, badge_color)
        self.sidebar_runtime.setText(f"运行状态：{status_text}")
        self.overview_page.update_status(status_text)
        self.statusBar().showMessage(message)

    def set_runtime_state(self, status: RuntimeStatus, message: str, **kwargs):
        if status == RuntimeStatus.IDLE:
            state = self.runtime_manager.set_idle(message)
        elif status == RuntimeStatus.READY:
            state = self.runtime_manager.set_ready(
                source_type=kwargs.get("source_type", ""),
                source_name=kwargs.get("source_name", ""),
                source_path=kwargs.get("source_path", ""),
                message=message,
            )
        elif status == RuntimeStatus.RUNNING:
            state = self.runtime_manager.set_running(
                source_type=kwargs.get("source_type", ""),
                source_name=kwargs.get("source_name", ""),
                source_path=kwargs.get("source_path", ""),
                current_file_name=kwargs.get("current_file_name", ""),
                progress_current=kwargs.get("progress_current", 0),
                progress_total=kwargs.get("progress_total", 0),
                message=message,
                current_fps=kwargs.get("current_fps", 0.0),
            )
        elif status == RuntimeStatus.PAUSED:
            state = self.runtime_manager.set_paused(message)
        elif status == RuntimeStatus.FINISHED:
            state = self.runtime_manager.set_finished(message)
        else:
            state = self.runtime_manager.set_error(message, kwargs.get("error_message", ""))
        self.update_status_views(state.status.value, state.message)
        self.workbench_page.update_runtime(state)

    def build_runtime_model_info(self):
        config = deepcopy(self.config)
        params = self.workbench_page.current_param_values()
        config["MODEL"]["conf"] = params["conf"]
        config["MODEL"]["imgsize"] = params["imgsize"]
        config["MODEL"]["device"] = params["device"]
        config["MODEL"]["classes"] = params["classes"]
        return build_model_info(config)

    def load_model(self):
        self.set_runtime_state(RuntimeStatus.IDLE, "正在加载模型")
        try:
            model_info = build_model_info(self.config)
            self.engine.load(model_info)
            self.repository = RecordRepository(self.config["PATHS"]["output_root"], model_info)
            self.sidebar_session.setText(f"当前会话：{self.repository.session_id}")
            self.overview_page.update_model_info(model_info)
            self.update_context_chips()
            self.set_runtime_state(RuntimeStatus.IDLE, "模型加载完成，系统就绪")
            self.refresh_dashboard_views()
        except Exception as error:
            self.set_runtime_state(RuntimeStatus.ERROR, f"模型加载失败：{error}", error_message=str(error))
            self.show_error("模型加载失败", str(error))

    def load_settings_page(self):
        candidates = scan_weight_candidates(self.config)
        self.settings_page.set_weight_candidates(candidates, str(self.config["MODEL"].get("weight", "")))
        self.settings_page.load_config(self.config)

    def refresh_dashboard_views(self):
        self.refresh_history()
        self.update_overview()
        self.update_workbench_session_summary()
        self.update_analytics()
        self.load_settings_page()

    def update_overview(self):
        total_records = len(self.history_records)
        total_targets = sum(record.target_count for record in self.history_records)
        average_ms = round(sum(record.inference_ms for record in self.history_records) / total_records, 2) if total_records else 0.0
        latest_time = self.history_records[0].timestamp if self.history_records else "--"
        self.overview_page.update_system_stats(
            {
                "records": str(total_records),
                "targets": str(total_targets),
                "avg_time": ms_text(average_ms),
                "latest_time": latest_time,
            }
        )

        sample_original = None
        sample_result = None
        original_note = "默认展示最新历史记录的原图，若无历史则展示系统示例图。"
        result_note = "默认展示最新历史记录的结果图。"
        if self.current_image is not None and self.current_result_image is not None:
            sample_original = self.current_image
            sample_result = self.current_result_image
            original_note = f"当前任务：{self.current_input_name or '示例图像'}"
            result_note = "当前检测结果"
        elif self.history_records:
            record = self.history_records[0]
            sample_original = first_available_image(record.original_path, record.source_path)
            sample_result = read_image(record.result_path)
            original_note = f"历史记录：{record.source_name}"
            result_note = f"历史结果：{record.result_summary}"
        else:
            demo_path = self.find_demo_image()
            if demo_path:
                sample_original = read_image(demo_path)
                sample_result = sample_original
                original_note = f"系统示例：{Path(demo_path).name}"
                result_note = "暂无历史结果，当前展示示例图像。"
        self.overview_page.update_samples(sample_original, sample_result, original_note, result_note)

    def update_workbench_session_summary(self):
        if not self.repository:
            self.workbench_page.update_session_summary("当前会话尚未初始化。")
            return
        summary = self.repository.build_session_summary()
        lines = [
            f"当前会话 ID：{summary.session_id}",
            f"会话检测次数：{summary.record_count}",
            f"累计目标数：{summary.total_targets}",
            f"平均每条记录目标数：{summary.average_targets_per_record}",
            f"平均推理耗时：{summary.average_inference_ms} ms",
            f"输入类型分布：{json.dumps(summary.input_type_counts, ensure_ascii=False)}",
        ]
        self.workbench_page.update_session_summary("\n".join(lines))
        rows = []
        for record in self.repository.session_records:
            rows.append(
                [
                    record.record_id,
                    format_source_type(record.source_type),
                    record.source_name,
                    record.timestamp,
                    record.result_summary,
                    record.target_count,
                    confidence_text(record.average_confidence),
                    ms_text(record.inference_ms),
                    record.result_path,
                ]
            )
        self.workbench_page.update_result_table(rows)

    def show_selected_session_record(self, row: int, column: int):
        if not self.repository or row < 0 or row >= len(self.repository.session_records):
            return
        record = self.repository.session_records[row]
        original_image = first_available_image(record.original_path, record.source_path)
        result_image = read_image(record.result_path)
        if original_image is None:
            original_image = self.current_image
        if result_image is None:
            result_image = self.current_result_image
        self.workbench_page.update_previews(
            original_image,
            result_image,
            f"会话记录：{record.source_name}",
            f"结果摘要：{record.result_summary}",
        )
        self.workbench_page.update_detection_summary(
            format_source_type(record.source_type),
            record.target_count,
            confidence_text(record.average_confidence),
            confidence_text(record.max_confidence),
            ms_text(record.inference_ms),
            "\n".join(
                [
                    f"记录编号：{record.record_uid}",
                    f"检测时间：{record.timestamp}",
                    f"结果摘要：{record.result_summary}",
                    f"保存路径：{record.result_path or '未保存'}",
                ]
            ),
        )
        self.workbench_page.update_current_detection_items(record.detections)

    def update_analytics(self):
        summary = build_analysis_summary(self.history_records, self.repository.session_id if self.repository else None)
        session_record_count = summary.session_summary.record_count if summary.session_summary else 0
        self.analytics_page.update_header(summary.latest_timestamp or "--")
        self.analytics_page.update_cards(
            {
                "records": str(summary.total_records),
                "targets": str(summary.total_targets),
                "avg_conf": confidence_text(summary.average_confidence),
                "avg_time": ms_text(summary.average_inference_ms),
                "session_records": str(session_record_count),
            }
        )
        class_series = build_class_series(self.history_records)
        conf_values = build_confidence_histogram(self.history_records)
        input_series = build_input_type_series(self.history_records)
        trend_series = build_recent_target_series(self.history_records)
        self.analytics_page.chart_class.canvas.plot_bar(class_series["labels"], class_series["values"], "类别统计")
        self.analytics_page.chart_conf.canvas.plot_hist(conf_values, "置信度分布")
        self.analytics_page.chart_input.canvas.plot_pie(input_series["labels"], input_series["values"], "输入类型构成")
        self.analytics_page.chart_trend.canvas.plot_line(trend_series["labels"], trend_series["values"], "最近记录目标数")

        if summary.session_summary:
            session_lines = [
                f"当前会话 ID：{summary.session_summary.session_id}",
                f"当前会话检测次数：{summary.session_summary.record_count}",
                f"当前会话目标总数：{summary.session_summary.total_targets}",
                f"平均每条记录目标数：{summary.session_summary.average_targets_per_record}",
                f"平均推理耗时：{summary.session_summary.average_inference_ms} ms",
                f"输入类型统计：{json.dumps(summary.session_summary.input_type_counts, ensure_ascii=False)}",
            ]
            self.analytics_page.session_text.setPlainText("\n".join(session_lines))
        else:
            self.analytics_page.session_text.setPlainText("当前会话暂无统计数据。")

        most_common_type = max(summary.input_type_counts.items(), key=lambda item: item[1])[0] if summary.input_type_counts else "暂无"
        most_common_class = max(summary.class_counts.items(), key=lambda item: item[1])[0] if summary.class_counts else "暂无"
        lines = [
            f"1. 历史累计检测 {summary.total_records} 次，累计识别目标 {summary.total_targets} 个。",
            f"2. 平均置信度为 {confidence_text(summary.average_confidence)}，平均推理耗时为 {ms_text(summary.average_inference_ms)}。",
            f"3. 当前最常见输入类型为“{most_common_type}”。",
            f"4. 检测频次最高的类别为“{most_common_class}”。",
            f"5. 最近一次检测时间：{summary.latest_timestamp or '暂无'}。",
        ]
        self.analytics_page.summary_text.setPlainText("\n".join(lines))

    def refresh_history(self):
        limit = int(self.config["RUNTIME"].get("history_limit", 2000))
        self.history_records = RecordRepository.scan_history(self.config["PATHS"]["output_root"], limit=limit)
        if self.repository is not None:
            existing_ids = {record.record_uid for record in self.history_records}
            for record in reversed(self.repository.session_records):
                if record.record_uid not in existing_ids:
                    self.history_records.insert(0, record)
        self.sidebar_records.setText(f"累计记录：{len(self.history_records)}")
        self.apply_history_filters()

    def apply_history_filters(self):
        filters = self.history_page.filter_values()
        records = list(self.history_records)
        search_text = filters["search"].lower()
        if search_text:
            records = [record for record in records if search_text in record.source_name.lower()]
        source_filter = filters["source_type"]
        if source_filter != "全部类型":
            records = [record for record in records if format_source_type(record.source_type) == source_filter]
        reverse = filters["sort"] == "时间降序"
        records.sort(key=lambda item: item.timestamp, reverse=reverse)
        self.filtered_history_records = records
        rows = []
        for index, record in enumerate(records, start=1):
            rows.append(
                {
                    "record_uid": record.record_uid,
                    "display_id": record.record_id or index,
                    "timestamp": record.timestamp,
                    "source_type": format_source_type(record.source_type),
                    "source_name": record.source_name,
                    "source_path": record.source_path,
                    "target_count": record.target_count,
                    "average_confidence": confidence_text(record.average_confidence),
                    "inference_ms": ms_text(record.inference_ms),
                    "model_name": record.model_name,
                    "session_id": record.session_id,
                }
            )
        self.history_page.update_table(rows)
        self.history_page.update_summary(len(self.history_records), len(records))

    def find_demo_image(self) -> str:
        sample_dir = resolve_path(self.config["PATHS"].get("sample_dir", "./img"))
        if not sample_dir.exists():
            return ""
        for file_path in sorted(sample_dir.iterdir()):
            if file_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}:
                return str(file_path)
        return ""

    def load_demo_image(self):
        demo_path = self.find_demo_image()
        if not demo_path:
            self.show_info("提示", "未找到示例图像。")
            return
        self.load_image_source(demo_path)

    def select_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择图片文件",
            str(resolve_path(".")),
            "Image Files (*.jpg *.jpeg *.png *.bmp *.tif *.tiff)",
        )
        if path:
            self.load_image_source(path)

    def load_image_source(self, path: str):
        image = read_image(path)
        if image is None:
            self.show_warning("读取失败", "无法读取图像文件。")
            return
        self.stop_task(silent=True)
        self.current_input_type = "image"
        self.current_input_path = path
        self.current_input_name = Path(path).name
        self.current_image = image
        self.current_result_image = image.copy()
        self.current_detections = []
        self.current_record = None
        self.workbench_page.set_source_info("单张图像", path)
        self.workbench_page.update_previews(image, image.copy(), f"当前图像：{Path(path).name}", "点击开始检测后显示结果图。")
        self.workbench_page.update_detection_summary("单张图像", 0, "--", "--", "--", "当前尚未开始检测。")
        self.set_runtime_state(
            RuntimeStatus.READY,
            "图片已载入，等待开始检测。",
            source_type="单张图像",
            source_name=self.current_input_name,
            source_path=path,
        )
        self.switch_page("workbench")

    def select_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "选择图像文件夹", str(resolve_path(".")))
        if not folder:
            return
        files = [
            str(item)
            for item in sorted(Path(folder).iterdir())
            if item.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
        ]
        if not files:
            self.show_info("提示", "文件夹中没有可识别图像。")
            return
        self.stop_task(silent=True)
        self.pending_files = files
        self.pending_total = len(files)
        self.current_index = 0
        self.current_input_type = "folder"
        self.current_input_path = folder
        self.current_input_name = Path(folder).name
        first_image = read_image(files[0])
        self.current_image = first_image
        self.current_result_image = first_image.copy() if first_image is not None else None
        self.workbench_page.set_source_info("图像文件夹", folder)
        self.workbench_page.update_previews(
            first_image,
            first_image.copy() if first_image is not None else None,
            f"首张预览：{Path(files[0]).name}",
            "点击开始后批量处理文件夹。",
        )
        self.set_runtime_state(
            RuntimeStatus.READY,
            "文件夹已载入，等待批量检测。",
            source_type="图像文件夹",
            source_name=self.current_input_name,
            source_path=folder,
        )
        self.switch_page("workbench")

    def select_video(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            str(resolve_path(".")),
            "Video Files (*.mp4 *.avi *.mov *.mkv)",
        )
        if not path:
            return
        capture = cv2.VideoCapture(path)
        ok, frame = capture.read()
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        capture.release()
        if not ok:
            self.show_warning("读取失败", "无法读取视频文件。")
            return
        self.stop_task(silent=True)
        self.current_input_type = "video"
        self.current_input_path = path
        self.current_input_name = Path(path).name
        self.current_image = frame
        self.current_result_image = frame.copy()
        self.pending_total = total_frames
        self.current_index = 0
        self.workbench_page.set_source_info("视频文件", path)
        self.workbench_page.update_previews(frame, frame.copy(), f"视频预览：{Path(path).name}", "点击开始后逐帧处理视频。")
        self.set_runtime_state(
            RuntimeStatus.READY,
            "视频已载入，等待开始检测。",
            source_type="视频文件",
            source_name=self.current_input_name,
            source_path=path,
        )
        self.switch_page("workbench")

    def toggle_camera_connection(self):
        if self.current_input_type == "camera" and self.video_capture is not None:
            self.stop_task(silent=True)
            self.video_capture.release()
            self.video_capture = None
            self.current_input_type = ""
            self.current_input_path = ""
            self.current_input_name = ""
            self.workbench_page.set_source_info("未选择", "请选择图片、文件夹、视频或摄像头。")
            self.set_runtime_state(RuntimeStatus.IDLE, "摄像头已断开")
            return

        camera_index = int(self.config["RUNTIME"].get("camera_index", 0))
        capture = cv2.VideoCapture(camera_index)
        ok, frame = capture.read()
        if not ok:
            capture.release()
            self.set_runtime_state(RuntimeStatus.ERROR, "摄像头连接失败", error_message=f"无法打开摄像头索引 {camera_index}")
            self.show_warning("连接失败", f"无法打开摄像头索引 {camera_index}")
            return
        self.stop_task(silent=True)
        self.video_capture = capture
        self.current_input_type = "camera"
        self.current_input_path = f"camera:{camera_index}"
        self.current_input_name = f"camera_{camera_index}"
        self.current_image = frame
        self.current_result_image = frame.copy()
        self.current_index = 0
        self.pending_total = 0
        self.workbench_page.set_source_info("实时摄像头", self.current_input_path)
        self.workbench_page.update_previews(frame, frame.copy(), f"摄像头索引：{camera_index}", "点击开始后进行实时检测。")
        self.set_runtime_state(
            RuntimeStatus.READY,
            "摄像头已连接，等待开始检测。",
            source_type="实时摄像头",
            source_name=self.current_input_name,
            source_path=self.current_input_path,
        )
        self.switch_page("workbench")

    def start_task(self):
        if not self.engine.is_ready():
            self.load_model()
            if not self.engine.is_ready():
                self.show_warning("模型未就绪", "模型尚未成功加载，请检查权重与运行环境。")
                return
        if not self.current_input_type:
            self.show_info("提示", "请先选择输入源。")
            return

        model_info = self.build_runtime_model_info()
        self.engine.model_info = model_info
        self.overview_page.update_model_info(model_info)

        if self.current_input_type == "image":
            self.process_single_image()
            return

        if self.current_input_type == "video":
            if self.video_capture is not None:
                self.video_capture.release()
            self.video_capture = cv2.VideoCapture(self.current_input_path)

        self.process_timer.start(int(self.config["RUNTIME"].get("playback_interval_ms", 80)))
        self.set_runtime_state(
            RuntimeStatus.RUNNING,
            "任务运行中",
            source_type=format_source_type(self.current_input_type),
            source_name=self.current_input_name,
            source_path=self.current_input_path,
            current_file_name=self.current_input_name,
            progress_current=self.current_index,
            progress_total=self.pending_total,
            current_fps=0.0,
        )

    def pause_task(self):
        if self.process_timer.isActive():
            self.process_timer.stop()
            self.set_runtime_state(RuntimeStatus.PAUSED, "任务已暂停")

    def resume_task(self):
        if self.current_input_type in {"folder", "video", "camera"} and not self.process_timer.isActive():
            self.process_timer.start(int(self.config["RUNTIME"].get("playback_interval_ms", 80)))
            self.set_runtime_state(
                RuntimeStatus.RUNNING,
                "任务继续运行",
                source_type=format_source_type(self.current_input_type),
                source_name=self.current_input_name,
                source_path=self.current_input_path,
                current_file_name=self.current_input_name,
                progress_current=self.current_index,
                progress_total=self.pending_total,
                current_fps=self.runtime_manager.state.current_fps,
            )

    def stop_task(self, silent: bool = False):
        self.process_timer.stop()
        if self.video_capture is not None and self.current_input_type in {"video", "camera"}:
            self.video_capture.release()
            self.video_capture = None
        if not silent:
            self.set_runtime_state(RuntimeStatus.FINISHED, "任务已停止")

    def clear_current_session(self):
        if self.repository is None:
            return
        if not self.ask_confirm("确认清空", "确定清空当前会话的结构化记录吗？"):
            return
        self.repository.clear_session_records()
        self.current_record = None
        self.workbench_page.update_result_table([])
        self.refresh_dashboard_views()

    def process_single_image(self):
        if self.current_image is None:
            return
        self.set_runtime_state(
            RuntimeStatus.RUNNING,
            "单张图片检测中",
            source_type="单张图像",
            source_name=self.current_input_name,
            source_path=self.current_input_path,
            current_file_name=self.current_input_name,
            progress_current=1,
            progress_total=1,
            current_fps=0.0,
        )
        self.handle_detection_result(self.current_image.copy(), self.current_input_path, self.current_input_name, 1, 1)
        self.finish_batch_task("图片检测完成")

    def process_next_step(self):
        if self.current_input_type == "folder":
            if self.current_index >= len(self.pending_files):
                self.finish_batch_task("文件夹批量检测完成")
                return
            file_path = self.pending_files[self.current_index]
            self.current_index += 1
            image = read_image(file_path)
            if image is None:
                return
            self.handle_detection_result(image, file_path, Path(file_path).name, self.current_index, self.pending_total)
            return

        if self.current_input_type == "video":
            if self.video_capture is None:
                self.finish_batch_task("视频检测结束")
                return
            ok, frame = self.video_capture.read()
            if not ok:
                self.finish_batch_task("视频检测完成")
                return
            self.current_index += 1
            total = self.pending_total or int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            name = f"{Path(self.current_input_path).stem}_frame_{self.current_index:04d}.jpg"
            self.handle_detection_result(frame, self.current_input_path, name, self.current_index, total)
            return

        if self.current_input_type == "camera":
            if self.video_capture is None:
                self.finish_batch_task("摄像头任务结束")
                return
            ok, frame = self.video_capture.read()
            if not ok:
                self.finish_batch_task("摄像头读取失败")
                return
            self.current_index += 1
            name = f"camera_frame_{self.current_index:04d}.jpg"
            self.handle_detection_result(frame, self.current_input_path, name, self.current_index, 0)

    def handle_detection_result(self, image, source_path: str, source_name: str, progress_current: int, progress_total: int):
        try:
            result = self.engine.infer(image, self.config.get("CLASS_MAP", {}))
        except Exception as error:
            self.set_runtime_state(RuntimeStatus.ERROR, f"检测失败：{error}", error_message=str(error))
            self.show_error("检测失败", str(error))
            self.stop_task(silent=True)
            return

        detections: List[DetectionItem] = result["detections"]
        result_image = result["result_image"]
        inference_ms = float(result["inference_ms"])
        average_confidence = round(sum(item.confidence for item in detections) / len(detections), 4) if detections else 0.0
        max_confidence = max((item.confidence for item in detections), default=0.0)
        result_summary = build_result_summary(detections, self.config["LABELS"]["no_target"])
        top_class = build_top_class(detections, self.config["LABELS"]["no_target"])
        record_id = len(self.repository.session_records) + 1 if self.repository else 1
        model_info = self.engine.model_info
        record = DetectionRecord(
            record_uid=f"structured::{self.repository.session_id if self.repository else 'session'}::{record_id}",
            record_id=record_id,
            session_id=self.repository.session_id if self.repository else "",
            timestamp=current_time_text(),
            source_type=self.current_input_type,
            source_name=source_name,
            source_path=source_path,
            original_path="",
            result_path="",
            target_count=len(detections),
            average_confidence=average_confidence,
            max_confidence=max_confidence,
            inference_ms=inference_ms,
            result_summary=result_summary,
            top_class=top_class,
            class_counts=build_class_counts(detections),
            detections=detections,
            model_name=model_info.model_name if model_info else "",
            model_weight=model_info.weight_name if model_info else "",
            progress_current=progress_current,
            progress_total=max(progress_total, 1) if progress_total else 0,
        )
        if self.repository:
            self.repository.append_record(
                record,
                image,
                result_image,
                auto_save_result_image=bool(self.config["FEATURES"].get("auto_save_result_image", True)),
                auto_save_structured_record=bool(self.config["FEATURES"].get("auto_save_structured_record", True)),
            )

        self.current_image = image
        self.current_result_image = result_image
        self.current_detections = detections
        self.current_record = record
        fps = 1000.0 / inference_ms if inference_ms else 0.0
        self.set_runtime_state(
            RuntimeStatus.RUNNING,
            "任务运行中",
            source_type=format_source_type(self.current_input_type),
            source_name=self.current_input_name,
            source_path=self.current_input_path,
            current_file_name=source_name,
            progress_current=progress_current,
            progress_total=progress_total,
            current_fps=fps,
        )
        self.workbench_page.update_previews(image, result_image, f"当前输入：{source_name}", f"结果摘要：{result_summary}")
        self.workbench_page.update_detection_summary(
            format_source_type(self.current_input_type),
            len(detections),
            confidence_text(average_confidence) if detections else "0.0%",
            confidence_text(max_confidence) if detections else "0.0%",
            ms_text(inference_ms),
            "\n".join(
                [
                    f"文件名称：{source_name}",
                    f"结果摘要：{result_summary}",
                    f"主要类别：{top_class}",
                    f"目标数量：{len(detections)}",
                    f"平均置信度：{confidence_text(average_confidence) if detections else '0.0%'}",
                    f"最大置信度：{confidence_text(max_confidence) if detections else '0.0%'}",
                    f"推理耗时：{ms_text(inference_ms)}",
                    f"保存路径：{record.result_path or '未保存'}",
                ]
            ),
        )
        self.workbench_page.update_current_detection_items(detections)
        self.refresh_dashboard_views()

    def finish_batch_task(self, message: str):
        self.process_timer.stop()
        if self.video_capture is not None and self.current_input_type in {"video", "camera"}:
            self.video_capture.release()
            self.video_capture = None
        self.set_runtime_state(RuntimeStatus.FINISHED, message)
        summary = self.repository.build_session_summary() if self.repository else None
        if summary and self.config["FEATURES"].get("auto_export_session_summary", False):
            summary_path = Path(self.repository.session_dir) / "session_summary.json"
            with open(summary_path, "w", encoding="utf-8") as summary_file:
                json.dump(summary.to_dict(), summary_file, ensure_ascii=False, indent=2)
        self.show_success(
            "任务完成",
            f"{message}\n\n当前会话累计检测 {summary.record_count if summary else 0} 次，识别目标 {summary.total_targets if summary else 0} 个。",
        )
        self.refresh_dashboard_views()

    def show_selected_history_record(self, row: int, column: int):
        record_uid = self.history_page.selected_record_uid()
        if not record_uid:
            return
        record = next((item for item in self.filtered_history_records if item.record_uid == record_uid), None)
        if record is None:
            return
        original_image = first_available_image(record.original_path, record.source_path)
        result_image = read_image(record.result_path)
        self.history_page.update_previews(
            original_image,
            result_image,
            f"来源文件：{record.source_name}",
            f"结果摘要：{record.result_summary}",
        )
        detail_lines = [
            f"记录编号：{record.record_uid}",
            f"检测时间：{record.timestamp}",
            f"输入类型：{format_source_type(record.source_type)}",
            f"原始文件名：{record.source_name}",
            f"原始路径：{record.source_path}",
            f"目标数：{record.target_count}",
            f"平均置信度：{confidence_text(record.average_confidence)}",
            f"最大置信度：{confidence_text(record.max_confidence)}",
            f"推理耗时：{ms_text(record.inference_ms)}",
            f"结果图路径：{record.result_path}",
            f"使用模型：{record.model_name}",
            f"权重文件：{record.model_weight}",
            f"会话 ID：{record.session_id}",
        ]
        self.history_page.update_detail("\n".join(detail_lines))

    def export_current_session(self):
        if not self.repository or not self.repository.session_records:
            self.show_info("提示", "当前会话暂无可导出记录。")
            return
        self.export_records(self.repository.session_records)

    def export_selected_history_record(self):
        record_uid = self.history_page.selected_record_uid()
        record = next((item for item in self.filtered_history_records if item.record_uid == record_uid), None)
        if record is None:
            self.show_info("提示", "请先选择一条历史记录。")
            return
        self.export_records([record])

    def export_all_history_records(self):
        self.export_records(self.filtered_history_records or self.history_records)

    def export_records(self, records: List[DetectionRecord]):
        if not records:
            self.show_info("提示", "当前没有可导出的记录。")
            return
        save_path, file_type = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "导出检测记录",
            str(resolve_path("./output")),
            "Excel 工作簿 (*.xls);;CSV 文件 (*.csv)",
        )
        if not save_path:
            return
        export_type = "xls" if file_type == "Excel 工作簿 (*.xls)" else "csv"
        if self.repository is not None:
            self.repository.export_records(records, save_path, export_type)
        else:
            temp_repo = RecordRepository(self.config["PATHS"]["output_root"], build_model_info(self.config))
            temp_repo.export_records(records, save_path, export_type)
        self.show_success("导出完成", "记录已成功导出。")

    def delete_selected_history_record(self):
        record_uid = self.history_page.selected_record_uid()
        if not record_uid:
            self.show_info("提示", "请先选择要删除的记录。")
            return
        if not self.ask_confirm("确认删除", "确定删除当前选中的历史记录吗？"):
            return
        if self.repository and self.repository.delete_record(record_uid):
            self.refresh_dashboard_views()
            return
        self.show_info("提示", "当前选中记录可能为旧版兼容记录，无法直接删除。")

    def open_selected_result_directory(self):
        record_uid = self.history_page.selected_record_uid()
        record = next((item for item in self.filtered_history_records if item.record_uid == record_uid), None)
        if record is None:
            self.show_info("提示", "请先选择一条历史记录。")
            return
        path_value = record.result_path or record.original_path
        if not path_value:
            return
        path_obj = resolve_path(path_value) if str(path_value).startswith(".") else Path(path_value)
        if path_obj.exists():
            os.startfile(str(path_obj.parent))

    def save_settings(self, show_message: bool = True):
        patch = self.settings_page.build_config_patch()
        self.config = deep_merge(self.config, patch)
        save_config(self.config, CONFIG_PATH)
        self.apply_current_theme()
        self.load_settings_page()
        self.workbench_page.apply_runtime_config(self.config)
        if show_message:
            self.show_success("保存成功", "系统配置已保存。")

    def reload_model_from_settings(self):
        self.save_settings(show_message=False)
        self.load_model()

    def restore_defaults(self):
        if not self.ask_confirm("恢复默认", "确定恢复默认配置吗？"):
            return
        self.config = restore_default_config(CONFIG_PATH)
        self.apply_current_theme()
        self.workbench_page.apply_runtime_config(self.config)
        self.load_settings_page()
        self.load_model()

    def choose_weight_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择模型权重",
            str(resolve_path(self.config["PATHS"].get("weights_root", "./weights"))),
            "Model Weights (*.pt)",
        )
        if not path:
            return
        current_candidates = scan_weight_candidates(self.config)
        try:
            project_relative = f"./{Path(path).resolve().relative_to(Path(__file__).resolve().parent.parent).as_posix()}"
        except Exception:
            project_relative = path
        self.settings_page.set_weight_candidates(current_candidates + [project_relative], project_relative)

    def choose_output_directory(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            str(resolve_path(self.config["PATHS"].get("output_root", "./output/sessions"))),
        )
        if folder:
            self.settings_page.output_edit.setText(folder)

    def open_output_directory(self):
        output_root = resolve_path(self.settings_page.output_edit.text().strip())
        output_root.mkdir(parents=True, exist_ok=True)
        os.startfile(str(output_root))


