from __future__ import annotations

from typing import Dict

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt

from app.widgets import ChartCard, SectionCard, StatsCard, ToolbarButton


class AnalyticsPage(QtWidgets.QWidget):
    refresh_requested = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PageSurface")
        self._build_ui()

    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        container = QtWidgets.QWidget()
        container.setObjectName("ScrollContent")
        scroll.setWidget(container)

        root = QtWidgets.QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 16)
        root.setSpacing(14)

        # ── Top control bar ────────────────────────────────────────
        top_card = SectionCard("数据分析", with_bg=True)
        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(10)
        self.latest_badge = QtWidgets.QLabel("最近更新：-")
        self.latest_badge.setObjectName("InfoBadge")
        self.scope_badge = QtWidgets.QLabel("统计范围：历史记录 + 当前会话")
        self.scope_badge.setObjectName("InfoBadge")
        self.btn_refresh = ToolbarButton("刷新分析", role="primary")
        self.btn_refresh.setMinimumWidth(100)
        top_row.addWidget(self.latest_badge)
        top_row.addWidget(self.scope_badge)
        top_row.addStretch(1)
        top_row.addWidget(self.btn_refresh)
        top_card.layout.addLayout(top_row)
        root.addWidget(top_card)

        # ── 5 Stats cards ──────────────────────────────────────────
        stats_row = QtWidgets.QHBoxLayout()
        stats_row.setSpacing(12)
        self.stats_cards = {
            "records":        StatsCard("总检测次数",  "0",  ""),
            "targets":        StatsCard("总目标数",    "0",  ""),
            "avg_conf":       StatsCard("平均置信度",  "--", ""),
            "avg_time":       StatsCard("平均耗时",    "--", ""),
            "session_records":StatsCard("当前会话",    "0",  ""),
        }
        for card in self.stats_cards.values():
            card.setMinimumHeight(100)
            stats_row.addWidget(card, 1)
        root.addLayout(stats_row)

        # ── 2 × 2 chart grid ───────────────────────────────────────
        charts_top = QtWidgets.QHBoxLayout()
        charts_top.setSpacing(14)
        self.chart_class = ChartCard("类别统计")
        self.chart_conf  = ChartCard("置信度分布")
        for chart in (self.chart_class, self.chart_conf):
            chart.setMinimumHeight(300)
            chart.canvas.setMinimumHeight(220)
            charts_top.addWidget(chart, 1)
        root.addLayout(charts_top)

        charts_bot = QtWidgets.QHBoxLayout()
        charts_bot.setSpacing(14)
        self.chart_input = ChartCard("输入类型构成")
        self.chart_trend = ChartCard("最近记录趋势")
        for chart in (self.chart_input, self.chart_trend):
            chart.setMinimumHeight(300)
            chart.canvas.setMinimumHeight(220)
            charts_bot.addWidget(chart, 1)
        root.addLayout(charts_bot)

        root.addStretch(1)

        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        
        # Hidden elements for compatibility
        self.session_text = _DummyText()
        self.summary_text = _DummyText()

    def update_header(self, latest_text: str):
        self.latest_badge.setText(f"最近更新：{latest_text or '-'}")

    def update_cards(self, stats: Dict[str, str]):
        self.stats_cards["records"].set_content(stats.get("records", "0"), "")
        self.stats_cards["targets"].set_content(stats.get("targets", "0"), "")
        self.stats_cards["avg_conf"].set_content(stats.get("avg_conf", "--"), "")
        self.stats_cards["avg_time"].set_content(stats.get("avg_time", "--"), "")
        self.stats_cards["session_records"].set_content(stats.get("session_records", "0"), "")

    def update_class_chart(self, labels, values):
        self.chart_class.canvas.plot_bar(labels, values, "类别统计")

    def update_conf_chart(self, values):
        self.chart_conf.canvas.plot_hist(values, "置信度分布")

    def update_input_chart(self, labels, values):
        self.chart_input.canvas.plot_pie(labels, values, "输入类型构成")

    def update_trend_chart(self, labels, values):
        self.chart_trend.canvas.plot_line(labels, values, "最近记录趋势")

    def update_session_summary(self, text: str):
        # No longer displaying session summary
        pass

    def update_analysis_summary(self, text: str):
        # No longer displaying analysis summary
        pass

    def apply_chart_palette(self, palette: dict):
        for card in (self.chart_class, self.chart_conf,
                     self.chart_input, self.chart_trend):
            card.canvas.set_palette(palette)


class _DummyText:
    """Dummy text widget for compatibility."""
    def setPlainText(self, *args, **kwargs):
        pass
    def setText(self, *args, **kwargs):
        pass
