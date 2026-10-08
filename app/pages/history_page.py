from __future__ import annotations

from typing import Dict, List

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt

from app.widgets import NoWheelComboBox, PreviewPanel, SectionCard, ToolbarButton


class HistoryPage(QtWidgets.QWidget):
    refresh_requested = QtCore.pyqtSignal()
    export_selected_requested = QtCore.pyqtSignal()
    export_all_requested = QtCore.pyqtSignal()
    delete_selected_requested = QtCore.pyqtSignal()
    clear_session_requested = QtCore.pyqtSignal()
    open_result_dir_requested = QtCore.pyqtSignal()
    filters_changed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PageSurface")
        self._build_ui()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # ── Toolbar Card ───────────────────────────────────────────
        toolbar_card = SectionCard("历史记录管理", with_bg=True)

        filter_row = QtWidgets.QHBoxLayout()
        filter_row.setSpacing(10)
        self.summary_badge = QtWidgets.QLabel("历史记录：0 条")
        self.summary_badge.setObjectName("InfoBadge")
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("按文件名搜索")
        self.search_edit.setMaximumWidth(200)
        self.source_filter = NoWheelComboBox()
        self.source_filter.addItems(["全部类型", "单张图像", "图像文件夹", "视频文件", "实时摄像头"])
        self.sort_combo = NoWheelComboBox()
        self.sort_combo.addItems(["时间降序", "时间升序"])
        filter_row.addWidget(self.summary_badge)
        filter_row.addStretch(1)
        filter_row.addWidget(QtWidgets.QLabel("搜索"))
        filter_row.addWidget(self.search_edit)
        filter_row.addWidget(QtWidgets.QLabel("类型"))
        filter_row.addWidget(self.source_filter)
        filter_row.addWidget(QtWidgets.QLabel("排序"))
        filter_row.addWidget(self.sort_combo)
        toolbar_card.layout.addLayout(filter_row)

        button_row = QtWidgets.QHBoxLayout()
        button_row.setSpacing(8)
        self.btn_refresh = ToolbarButton("刷新")
        self.btn_export_selected = ToolbarButton("导出所选")
        self.btn_export_all = ToolbarButton("导出全部")
        self.btn_delete = ToolbarButton("删除所选", role="danger")
        self.btn_clear_session = ToolbarButton("清空会话", role="danger")
        self.btn_open_dir = ToolbarButton("打开目录")
        for button in (
            self.btn_refresh,
            self.btn_export_selected,
            self.btn_export_all,
            self.btn_delete,
            self.btn_clear_session,
            self.btn_open_dir,
        ):
            button_row.addWidget(button)
        button_row.addStretch(1)
        toolbar_card.layout.addLayout(button_row)
        root.addWidget(toolbar_card)

        # ── History Table ──────────────────────────────────────────
        table_card = SectionCard("历史记录表", with_bg=True)
        self.history_table = QtWidgets.QTableWidget(0, 10)
        self.history_table.setHorizontalHeaderLabels(
            ["编号", "时间", "输入类型", "文件名", "原始路径", "目标数", "平均置信度", "耗时", "模型", "会话 ID"]
        )
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.verticalHeader().setDefaultSectionSize(36)
        self.history_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.history_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.history_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setWordWrap(False)
        self.history_table.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        header = self.history_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QtWidgets.QHeaderView.ResizeToContents)
        table_card.layout.addWidget(self.history_table)
        root.addWidget(table_card, 2)

        # ── Bottom Row: Preview + Detail ───────────────────────────
        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.setSpacing(12)

        preview_card = SectionCard("结果回看", with_bg=True)
        preview_row = QtWidgets.QHBoxLayout()
        preview_row.setSpacing(12)
        self.original_panel = PreviewPanel("历史原图", "", minimum_height=220)
        self.result_panel = PreviewPanel("历史结果图", "", minimum_height=220)
        preview_row.addWidget(self.original_panel, 1)
        preview_row.addWidget(self.result_panel, 1)
        preview_card.layout.addLayout(preview_row)
        bottom_row.addWidget(preview_card, 3)

        detail_card = SectionCard("记录详情", with_bg=True)
        self.detail_text = QtWidgets.QTextBrowser()
        self.detail_text.setObjectName("SummaryBrowser")
        self.detail_text.setText("请选择一条历史记录查看详细信息。")
        detail_card.layout.addWidget(self.detail_text)
        bottom_row.addWidget(detail_card, 2)

        root.addLayout(bottom_row, 1)

        # Connect signals
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        self.btn_export_selected.clicked.connect(self.export_selected_requested.emit)
        self.btn_export_all.clicked.connect(self.export_all_requested.emit)
        self.btn_delete.clicked.connect(self.delete_selected_requested.emit)
        self.btn_clear_session.clicked.connect(self.clear_session_requested.emit)
        self.btn_open_dir.clicked.connect(self.open_result_dir_requested.emit)
        self.search_edit.textChanged.connect(self.filters_changed.emit)
        self.source_filter.currentIndexChanged.connect(self.filters_changed.emit)
        self.sort_combo.currentIndexChanged.connect(self.filters_changed.emit)

    def filter_values(self) -> Dict[str, str]:
        return {
            "search": self.search_edit.text().strip(),
            "source_type": self.source_filter.currentText(),
            "sort": self.sort_combo.currentText(),
        }

    def update_summary(self, total_count: int, filtered_count: int):
        self.summary_badge.setText(f"历史记录：{filtered_count} / {total_count} 条")

    def update_table(self, rows: List[Dict]):
        self.history_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row.get("display_id", row_index + 1),
                row.get("timestamp", ""),
                row.get("source_type", ""),
                row.get("source_name", ""),
                row.get("source_path", ""),
                row.get("target_count", 0),
                row.get("average_confidence", ""),
                row.get("inference_ms", ""),
                row.get("model_name", ""),
                row.get("session_id", ""),
            ]
            for col_index, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, row.get("record_uid", ""))
                align = Qt.AlignCenter if col_index in {0, 1, 2, 5, 6, 7, 8, 9} else Qt.AlignVCenter | Qt.AlignLeft
                item.setTextAlignment(align)
                self.history_table.setItem(row_index, col_index, item)

    def selected_record_uid(self) -> str:
        selected_rows = self.history_table.selectionModel().selectedRows()
        if not selected_rows:
            return ""
        row = selected_rows[0].row()
        item = self.history_table.item(row, 0)
        return item.data(Qt.UserRole) if item else ""

    def update_previews(self, original_image, result_image, original_note: str, result_note: str):
        self.original_panel.set_image(original_image, original_note)
        self.result_panel.set_image(result_image, result_note)

    def update_detail(self, text: str):
        self.detail_text.setText(text.replace("\n", "<br/>"))
