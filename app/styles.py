from __future__ import annotations


THEMES = {
    "agriculture_light": {
        "bg": "#F4F6F2",
        "surface": "#FFFFFF",
        "surface_soft": "#EEF2EC",
        "surface_tint": "#F8FAF7",
        "sidebar_top": "#16402B",
        "sidebar_bottom": "#1E5236",
        "primary": "#1D7A4A",
        "primary_hover": "#2A9060",
        "primary_pressed": "#165F38",
        "accent": "#C47D1A",
        "accent_hover": "#D9901F",
        "accent_pressed": "#A86615",
        "accent_soft": "#FDF0D8",
        "text": "#1A2820",
        "muted": "#5E7268",
        "border": "#D5DDD8",
        "border_strong": "#B8C6BE",
        "success": "#1D7A4A",
        "warning": "#C47D1A",
        "error": "#C23B35",
        "disabled_bg": "#E8EDE9",
        "disabled_text": "#9AADA2",
    },
    "dark": {
        "bg": "#0D1610",
        "surface": "#141F17",
        "surface_soft": "#1A2820",
        "surface_tint": "#1F3025",
        "sidebar_top": "#090F0B",
        "sidebar_bottom": "#111A14",
        "primary": "#3DAF72",
        "primary_hover": "#4DC882",
        "primary_pressed": "#2E9058",
        "accent": "#D4982A",
        "accent_hover": "#E8AB38",
        "accent_pressed": "#B87E20",
        "accent_soft": "#3A2D12",
        "text": "#E8F2EA",
        "muted": "#8BA896",
        "border": "#243529",
        "border_strong": "#364D3C",
        "success": "#3DAF72",
        "warning": "#D4982A",
        "error": "#E05A52",
        "disabled_bg": "#182210",
        "disabled_text": "#5A7A62",
    },
    "wheat_gold": {
        "bg": "#F5EFE0",
        "surface": "#FFFCF5",
        "surface_soft": "#F8F0DC",
        "surface_tint": "#FDF7EC",
        "sidebar_top": "#4A3818",
        "sidebar_bottom": "#6B5228",
        "primary": "#7A6424",
        "primary_hover": "#8E7530",
        "primary_pressed": "#68551C",
        "accent": "#BE7D18",
        "accent_hover": "#D08E20",
        "accent_pressed": "#A66C12",
        "accent_soft": "#F5E4B8",
        "text": "#2A2010",
        "muted": "#6A5A3A",
        "border": "#E0CCA0",
        "border_strong": "#CEB888",
        "success": "#4A8840",
        "warning": "#BE7D18",
        "error": "#B83030",
        "disabled_bg": "#EDE0C8",
        "disabled_text": "#A09070",
    },
    # New premium dark theme
    "obsidian_field": {
        "bg": "#0A0F0C",
        "surface": "#111811",
        "surface_soft": "#162019",
        "surface_tint": "#1C2920",
        "sidebar_top": "#040806",
        "sidebar_bottom": "#0E1810",
        "primary": "#4CBF7A",
        "primary_hover": "#5FD48E",
        "primary_pressed": "#3AA362",
        "accent": "#E6A832",
        "accent_hover": "#F5BE48",
        "accent_pressed": "#C88E22",
        "accent_soft": "#3A2C0E",
        "text": "#D8EFE0",
        "muted": "#7A9E85",
        "border": "#1E3025",
        "border_strong": "#2E4838",
        "success": "#4CBF7A",
        "warning": "#E6A832",
        "error": "#E85050",
        "disabled_bg": "#141E16",
        "disabled_text": "#456050",
    },
}


def status_color(status: str, theme_name: str) -> str:
    palette = THEMES.get(theme_name, THEMES["agriculture_light"])
    mapping = {
        "idle": palette["muted"],
        "ready": palette["primary"],
        "running": palette["success"],
        "paused": palette["warning"],
        "finished": palette["accent"],
        "error": palette["error"],
    }
    return mapping.get(status, palette["muted"])


def build_stylesheet(theme_name: str = "agriculture_light", table_font_size: int = 10) -> str:
    palette = THEMES.get(theme_name, THEMES["agriculture_light"])
    is_dark = theme_name in ("dark", "obsidian_field")

    sidebar_text = "#E8F8EC" if is_dark else "#F0FFF4"
    sidebar_muted = "rgba(232,248,236,0.60)" if is_dark else "rgba(240,255,244,0.65)"
    sidebar_badge_bg = "rgba(255,255,255,0.06)" if is_dark else "rgba(255,255,255,0.10)"
    sidebar_badge_border = "rgba(255,255,255,0.10)" if is_dark else "rgba(255,255,255,0.14)"
    hero_overlay = "rgba(0,0,0,0.12)" if is_dark else "rgba(0,0,0,0.06)"

    return f"""
    * {{
        font-family: "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
        color: {palette["text"]};
        outline: none;
    }}
    QMainWindow {{
        background: {palette["bg"]};
    }}
    QWidget {{
        background: transparent;
    }}
    QWidget#CentralWidget, QWidget#PageSurface, QWidget#ScrollContent {{
        background: {palette["bg"]};
    }}
    QWidget#OverviewPageSurface, QWidget#OverviewScrollContent {{
        background: {palette["bg"]};
    }}
    QStackedWidget, QScrollArea {{
        background: transparent;
        border: none;
    }}
    QLabel {{
        background: transparent;
    }}
    QTextBrowser, QPlainTextEdit {{
        background: transparent;
    }}
    QAbstractScrollArea::viewport {{
        background: transparent;
    }}
    QToolTip {{
        background: {palette["surface"]};
        color: {palette["text"]};
        border: 1px solid {palette["border_strong"]};
        padding: 7px 10px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: 600;
    }}

    /* ── Sidebar ─────────────────────────────────────────────── */
    QFrame#Sidebar {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 {palette["sidebar_top"]},
                                    stop:1 {palette["sidebar_bottom"]});
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.05);
    }}
    QLabel#BrandTitle {{
        color: {sidebar_text};
        font-size: 20px;
        font-weight: 900;
        letter-spacing: 0.5px;
    }}
    QLabel#BrandSubtitle {{
        color: {sidebar_muted};
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.8px;
    }}
    QLabel#SidebarInfo {{
        color: {sidebar_text};
        font-size: 11px;
        font-weight: 600;
        background: {sidebar_badge_bg};
        border: 1px solid {sidebar_badge_border};
        border-radius: 11px;
        padding: 9px 12px;
        line-height: 1.5;
    }}
    QLabel#SidebarFooter {{
        color: {sidebar_muted};
        font-size: 10px;
        font-weight: 600;
        padding-top: 6px;
    }}
    QPushButton#NavButton {{
        background: transparent;
        border: none;
        border-radius: 12px;
        color: {sidebar_text};
        text-align: left;
        padding: 10px 14px;
        font-size: 13px;
        font-weight: 700;
        min-height: 38px;
    }}
    QPushButton#NavButton:hover {{
        background: rgba(255,255,255,0.09);
    }}
    QPushButton#NavButton:pressed {{
        background: rgba(255,255,255,0.14);
    }}
    QPushButton#NavButton:checked {{
        background: {palette["primary"]};
        color: #FFFFFF;
        padding-left: 16px;
    }}
    QPushButton#NavButton:checked:hover {{
        background: {palette["primary_hover"]};
    }}

    /* ── Card Surfaces ───────────────────────────────────────── */
    QFrame#TopBar, QFrame#SectionCard, QFrame#StatsCard,
    QFrame#PreviewPanelFrame, QFrame#ChartCard {{
        background: {palette["surface"]};
        border: 1px solid {palette["border"]};
        border-radius: 16px;
    }}
    QFrame#TopBar {{
        border-radius: 16px;
    }}
    QFrame#StatsCard {{
        border-radius: 14px;
    }}
    QFrame#OverviewStatsCard {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 rgba(255,255,255,0.85),
                                    stop:1 rgba(255,255,255,0.75));
        border: 1px solid rgba(213,221,216,0.6);
        border-radius: 14px;
    }}

    /* ── Hero ────────────────────────────────────────────────── */
    QFrame#HeroCard {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                    stop:0   #164530,
                                    stop:0.5 #1E6040,
                                    stop:1   #A87020);
        border-radius: 22px;
        border: none;
    }}
    QFrame#HeroAside {{
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
    }}
    QFrame#OverviewHeroCard {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 rgba(255,255,255,0.92),
                                    stop:0.5 rgba(255,255,255,0.88),
                                    stop:1 rgba(22,69,48,0.15));
        border: 1px solid {palette["border"]};
        border-radius: 28px;
    }}
    QFrame#OverviewSearchPanel {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 rgba(255,255,255,0.90),
                                    stop:1 rgba(255,255,255,0.80));
        border: 1px solid rgba(184,198,190,0.7);
        border-radius: 20px;
    }}

    /* ── Overview Page (首页统一模块) ─────────────────────────── */
    QFrame#OverviewMainCard {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 rgba(255,255,255,0.95),
                                    stop:0.4 rgba(255,255,255,0.92),
                                    stop:1 rgba(240,248,242,0.88));
        border: 1px solid rgba(213,221,216,0.8);
        border-radius: 24px;
        margin: 0px;
    }}
    QFrame#OverviewActionPanel {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 rgba(255,255,255,0.95),
                                    stop:1 rgba(255,255,255,0.90));
        border: 2px solid rgba(29,122,74,0.35);
        border-radius: 20px;
    }}
    QFrame#OverviewStatsCard {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 rgba(255,255,255,0.85),
                                    stop:1 rgba(248,250,247,0.80));
        border: 1px solid rgba(213,221,216,0.6);
        border-radius: 14px;
    }}
    QLabel#OverviewBadge {{
        background: rgba(248,250,247,0.9);
        border: 1px solid rgba(213,221,216,0.7);
        border-radius: 8px;
        padding: 5px 10px;
        color: {palette["muted"]};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.2px;
    }}
    QLabel#OverviewStatusBadge {{
        background: rgba(29,122,74,0.15);
        color: {palette["primary"]};
        border: 1px solid rgba(29,122,74,0.3);
        border-radius: 10px;
        padding: 5px 12px;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }}
    QLabel#OverviewKicker {{
        color: {palette["primary"]};
        font-size: 10px;
        font-weight: 900;
        letter-spacing: 2px;
    }}
    QLabel#OverviewTitle {{
        color: {palette["text"]};
        font-size: 34px;
        font-weight: 900;
        letter-spacing: -0.6px;
        line-height: 1.15;
    }}
    QLabel#OverviewSubtitle {{
        color: {palette["text"]};
        font-size: 15px;
        font-weight: 600;
        line-height: 1.55;
    }}
    QLabel#OverviewActionTitle {{
        color: {palette["text"]};
        font-size: 18px;
        font-weight: 800;
        letter-spacing: -0.2px;
    }}
    QLabel#OverviewActionHint {{
        color: {palette["muted"]};
        font-size: 13px;
        font-weight: 500;
        line-height: 1.6;
    }}
    QLabel#OverviewStatsTitle {{
        color: {palette["muted"]};
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.8px;
    }}
    QLabel#OverviewStatsValue {{
        color: {palette["primary"]};
        font-size: 26px;
        font-weight: 900;
        letter-spacing: -0.5px;
        line-height: 1.1;
    }}
    QLabel#OverviewStatsSubtitle {{
        color: {palette["muted"]};
        font-size: 11px;
        font-weight: 500;
        line-height: 1.45;
    }}
    QLabel#OverviewFootnote {{
        color: {palette["muted"]};
        font-size: 12px;
        font-weight: 500;
        line-height: 1.7;
    }}

    /* ── Typography ──────────────────────────────────────────── */
    QLabel#PageTitle {{
        font-size: 22px;
        font-weight: 900;
        letter-spacing: -0.3px;
    }}
    QLabel#PageSubtitle {{
        color: {palette["muted"]};
        font-size: 13px;
        font-weight: 500;
        line-height: 1.5;
    }}
    QLabel#PanelTitle {{
        font-size: 15px;
        font-weight: 800;
        letter-spacing: -0.2px;
    }}
    QLabel#PanelSubtitle, QLabel#MetaText {{
        color: {palette["muted"]};
        font-size: 12px;
        font-weight: 500;
        line-height: 1.55;
    }}
    QLabel#HeroTitle {{
        color: #FFFFFF;
        font-size: 32px;
        font-weight: 900;
        letter-spacing: -0.5px;
        line-height: 1.15;
    }}
    QLabel#HeroSubtitle {{
        color: rgba(255,255,255,0.92);
        font-size: 14px;
        font-weight: 700;
        line-height: 1.5;
    }}
    QLabel#HeroDescription {{
        color: rgba(255,255,255,0.80);
        font-size: 12px;
        font-weight: 500;
        line-height: 1.7;
    }}
    QLabel#HeroPointTitle {{
        color: #FFFFFF;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.2px;
    }}
    QLabel#HeroPointText {{
        color: rgba(255,255,255,0.75);
        font-size: 11px;
        font-weight: 500;
        line-height: 1.55;
    }}
    QLabel#OverviewHeroKicker {{
        color: {palette["primary"]};
        font-size: 10px;
        font-weight: 900;
        letter-spacing: 1.8px;
    }}
    QLabel#OverviewHeroTitle {{
        color: {palette["text"]};
        font-size: 32px;
        font-weight: 900;
        letter-spacing: -0.6px;
        line-height: 1.15;
    }}
    QLabel#OverviewHeroSubtitle {{
        color: {palette["text"]};
        font-size: 15px;
        font-weight: 700;
        line-height: 1.55;
    }}
    QLabel#OverviewHeroFootnote {{
        color: {palette["muted"]};
        font-size: 12px;
        font-weight: 500;
        line-height: 1.7;
    }}
    QLabel#OverviewSearchTitle {{
        color: {palette["text"]};
        font-size: 14px;
        font-weight: 800;
        letter-spacing: -0.2px;
    }}
    QLabel#OverviewSearchHint {{
        color: {palette["muted"]};
        font-size: 12px;
        font-weight: 500;
        line-height: 1.6;
    }}
    QLabel#OverviewImageTitle {{
        color: {palette["text"]};
        font-size: 13px;
        font-weight: 800;
        letter-spacing: -0.2px;
    }}
    QLabel#OverviewImageSubtitle {{
        color: {palette["muted"]};
        font-size: 11px;
        font-weight: 500;
        line-height: 1.55;
    }}

    /* ── Stats Cards ─────────────────────────────────────────── */
    QLabel#StatsCardTitle {{
        color: {palette["muted"]};
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.8px;
    }}
    QLabel#StatsCardValue {{
        color: {palette["primary"]};
        font-size: 26px;
        font-weight: 900;
        letter-spacing: -0.5px;
        line-height: 1.1;
    }}
    QLabel#StatsCardSubtitle {{
        color: {palette["muted"]};
        font-size: 11px;
        font-weight: 500;
        line-height: 1.45;
    }}

    /* ── Badges ──────────────────────────────────────────────── */
    QLabel#InfoBadge {{
        background: {palette["surface_tint"]};
        border: 1px solid {palette["border"]};
        border-radius: 8px;
        padding: 5px 10px;
        color: {palette["muted"]};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.2px;
    }}
    QLabel#StatusBadge {{
        background: {palette["accent_soft"]};
        color: {palette["accent"]};
        border: 1px solid {palette["accent"]};
        border-radius: 10px;
        padding: 5px 12px;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }}
    QFrame#HeroCard QLabel#InfoBadge {{
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.15);
        color: rgba(255,255,255,0.90);
    }}
    QFrame#HeroCard QLabel#StatusBadge {{
        background: rgba(255,255,255,0.16);
        color: #FFFFFF;
        border: 1px solid rgba(255,255,255,0.25);
    }}

    /* ── Info Rows ───────────────────────────────────────────── */
    QLabel#InfoRowLabel {{
        color: {palette["muted"]};
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.3px;
        min-width: 90px;
    }}
    QLabel#InfoRowValue {{
        color: {palette["text"]};
        font-size: 12px;
        font-weight: 600;
        line-height: 1.45;
    }}
    QFrame#MetricTile {{
        background: {palette["surface_soft"]};
        border: 1px solid {palette["border"]};
        border-radius: 10px;
    }}
    QLabel#MetricLabel {{
        color: {palette["muted"]};
        font-size: 9px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }}
    QLabel#MetricValue {{
        color: {palette["text"]};
        font-size: 18px;
        font-weight: 900;
        letter-spacing: -0.3px;
        line-height: 1.1;
    }}
    QLabel#MetricFoot {{
        color: {palette["muted"]};
        font-size: 9px;
        font-weight: 500;
        line-height: 1.4;
    }}

    /* ── Image Stage ─────────────────────────────────────────── */
    QLabel#ImageStage {{
        background: {palette["surface_soft"]};
        border: 1.5px dashed {palette["border_strong"]};
        border-radius: 14px;
        color: {palette["muted"]};
        font-size: 13px;
        font-weight: 700;
        padding: 16px;
    }}

    /* ── Buttons ─────────────────────────────────────────────── */
    QPushButton {{
        background: {palette["surface_tint"]};
        border: 1px solid {palette["border"]};
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 700;
        color: {palette["text"]};
        letter-spacing: 0.1px;
    }}
    QPushButton:hover {{
        background: {palette["surface_soft"]};
        border: 1px solid {palette["border_strong"]};
    }}
    QPushButton:pressed {{
        background: {palette["surface_soft"]};
        padding-top: 7px;
    }}
    QPushButton:disabled {{
        background: {palette["disabled_bg"]};
        color: {palette["disabled_text"]};
        border: 1px solid {palette["border"]};
    }}
    QPushButton#SecondaryButton {{
        background: {palette["surface_tint"]};
    }}
    QPushButton#SecondaryButton:hover {{
        background: {palette["surface_soft"]};
    }}
    QPushButton#SecondaryButton:checked {{
        background: {palette["primary"]};
        color: #FFFFFF;
        border: none;
    }}
    QPushButton#SecondaryButton:checked:hover {{
        background: {palette["primary_hover"]};
    }}
    QPushButton#PrimaryButton {{
        background: {palette["primary"]};
        color: #FFFFFF;
        border: none;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.2px;
    }}
    QPushButton#PrimaryButton:hover {{
        background: {palette["primary_hover"]};
    }}
    QPushButton#PrimaryButton:pressed {{
        background: {palette["primary_pressed"]};
    }}
    QPushButton#PrimaryButton:disabled {{
        background: {palette["disabled_bg"]};
        color: {palette["disabled_text"]};
    }}
    QPushButton#AccentButton {{
        background: {palette["accent"]};
        color: #FFFFFF;
        border: none;
        font-size: 13px;
        font-weight: 800;
    }}
    QPushButton#AccentButton:hover {{
        background: {palette["accent_hover"]};
    }}
    QPushButton#AccentButton:pressed {{
        background: {palette["accent_pressed"]};
    }}
    QPushButton#DangerButton {{
        background: {palette["error"]};
        color: #FFFFFF;
        border: none;
        font-weight: 800;
    }}
    QPushButton#DangerButton:hover {{
        background: #D44848;
    }}
    QPushButton#DangerButton:pressed {{
        background: #B83535;
    }}

    /* ── Inputs ──────────────────────────────────────────────── */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextBrowser {{
        background: {palette["surface_tint"]};
        border: 1px solid {palette["border"]};
        border-radius: 10px;
        padding: 8px 11px;
        selection-background-color: {palette["accent_soft"]};
        selection-color: {palette["text"]};
        font-size: 12px;
        font-weight: 600;
    }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        min-height: 18px;
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {{
        background: {palette["surface"]};
        border: 1.5px solid {palette["primary"]};
    }}
    QPlainTextEdit[readOnly="true"], QTextBrowser {{
        background: transparent;
        border: none;
        padding: 0;
    }}
    QTextBrowser#SummaryBrowser {{
        background: transparent;
        border: none;
        font-size: 12px;
        line-height: 1.65;
    }}
    QTextBrowser {{
        line-height: 1.60;
    }}
    QComboBox {{
        padding-right: 22px;
    }}
    QComboBox::drop-down {{
        width: 20px;
        border: none;
        background: transparent;
    }}
    QComboBox QAbstractItemView {{
        background: {palette["surface"]};
        border: 1px solid {palette["border_strong"]};
        border-radius: 8px;
        selection-background-color: {palette["accent_soft"]};
        selection-color: {palette["text"]};
        outline: none;
        padding: 4px;
    }}
    QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{
        width: 18px;
        border: none;
        background: transparent;
    }}

    /* ── Checkbox ────────────────────────────────────────────── */
    QCheckBox {{
        spacing: 8px;
        font-size: 12px;
        font-weight: 600;
    }}
    QCheckBox::indicator {{
        width: 15px;
        height: 15px;
        border-radius: 4px;
        border: 1.5px solid {palette["border_strong"]};
        background: {palette["surface"]};
    }}
    QCheckBox::indicator:checked {{
        background: {palette["primary"]};
        border: 1.5px solid {palette["primary"]};
    }}

    /* ── Table ───────────────────────────────────────────────── */
    QTableWidget {{
        background: {palette["surface"]};
        border: 1px solid {palette["border"]};
        border-radius: 10px;
        gridline-color: transparent;
        selection-background-color: {palette["accent_soft"]};
        selection-color: {palette["text"]};
        alternate-background-color: {palette["surface_tint"]};
        font-size: {table_font_size}px;
        font-weight: 500;
        outline: none;
    }}
    QTableWidget::item {{
        padding: 8px 12px;
        border: none;
        border-bottom: 1px solid {palette["border"]};
    }}
    QTableWidget::item:hover {{
        background: {palette["surface_soft"]};
    }}
    QTableWidget::item:selected {{
        background: {palette["accent_soft"]};
        color: {palette["text"]};
    }}
    QTableWidget::item:focus {{
        outline: none;
        border: none;
    }}
    QTableWidget#CompactTable {{
        font-size: {max(table_font_size - 1, 9)}px;
        border-radius: 8px;
    }}
    QTableWidget#CompactTable::item {{
        padding: 6px 10px;
    }}
    QHeaderView {{
        background: transparent;
    }}
    QHeaderView::section {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 {palette["surface_soft"]},
                                    stop:1 {palette["surface_tint"]});
        color: {palette["muted"]};
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        border: none;
        border-bottom: 2px solid {palette["primary"]};
        padding: 10px 12px;
    }}
    QHeaderView::section:hover {{
        background: {palette["surface_soft"]};
        color: {palette["text"]};
    }}
    QHeaderView::section:first {{
        border-top-left-radius: 10px;
    }}
    QHeaderView::section:last {{
        border-top-right-radius: 10px;
    }}
    QTableCornerButton::section {{
        background: {palette["surface_soft"]};
        border: none;
        border-bottom: 2px solid {palette["primary"]};
        border-top-left-radius: 10px;
    }}

    /* ── Progress Bar ────────────────────────────────────────── */
    QProgressBar {{
        background: {palette["surface_soft"]};
        border: none;
        border-radius: 8px;
        text-align: center;
        min-height: 14px;
        max-height: 14px;
        color: transparent;
    }}
    QProgressBar::chunk {{
        border-radius: 7px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 {palette["primary"]},
                                    stop:1 {palette["accent"]});
    }}

    /* ── Dialog ──────────────────────────────────────────────── */
    QDialog#AppMessageDialog {{
        background: transparent;
    }}
    QFrame#DialogCard {{
        background: {palette["surface"]};
        border: 1px solid {palette["border_strong"]};
        border-radius: 18px;
    }}
    QLabel#DialogTitle {{
        font-size: 16px;
        font-weight: 900;
        color: {palette["text"]};
        letter-spacing: -0.2px;
    }}
    QLabel#DialogBody {{
        font-size: 13px;
        font-weight: 500;
        line-height: 1.65;
        color: {palette["muted"]};
    }}

    /* ── Status Bar & Scrollbar ──────────────────────────────── */
    QStatusBar {{
        background: {palette["bg"]};
        color: {palette["muted"]};
        font-size: 11px;
        font-weight: 600;
    }}
    QScrollBar:vertical {{
        background: {palette["surface_tint"]};
        width: 10px;
        margin: 2px 2px 2px 0;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {palette["border_strong"]};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {palette["primary"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        height: 0px;
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background: {palette["surface_tint"]};
        height: 10px;
        margin: 0 2px 2px 2px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal {{
        background: {palette["border_strong"]};
        border-radius: 5px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {palette["primary"]};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        width: 0px;
        background: transparent;
    }}
    
    /* ── Table Scrollbar ─────────────────────────────────────── */
    QTableWidget QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 4px 2px 4px 0;
    }}
    QTableWidget QScrollBar::handle:vertical {{
        background: {palette["border_strong"]};
        border-radius: 4px;
        min-height: 24px;
    }}
    QTableWidget QScrollBar::handle:vertical:hover {{
        background: {palette["primary"]};
    }}
    QTableWidget QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0 4px 2px 4px;
    }}
    QTableWidget QScrollBar::handle:horizontal {{
        background: {palette["border_strong"]};
        border-radius: 4px;
        min-width: 24px;
    }}
    QTableWidget QScrollBar::handle:horizontal:hover {{
        background: {palette["primary"]};
    }}

    /* ── Form Layout ─────────────────────────────────────────── */
    QFormLayout QLabel {{
        font-size: 12px;
        font-weight: 700;
        color: {palette["muted"]};
        letter-spacing: 0.2px;
    }}

    /* ── Group Box ───────────────────────────────────────────── */
    QGroupBox {{
        font-size: 12px;
        font-weight: 800;
        color: {palette["muted"]};
        letter-spacing: 0.4px;
        border: 1px solid {palette["border"]};
        border-radius: 10px;
        margin-top: 8px;
        padding-top: 6px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 6px;
        background: {palette["bg"]};
    }}

    /* ── Splitter ────────────────────────────────────────────── */
    QSplitter::handle {{
        background: {palette["border"]};
        width: 1px;
        height: 1px;
    }}
    """
