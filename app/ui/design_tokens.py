"""Tokens de espaçamento, tipografia e paleta (claro/escuro) para UI e QSS gerado."""
from __future__ import annotations

from typing import Final

from PySide6.QtGui import QColor

# Espaçamento (px)
SP_XS: Final[int] = 4
SP_S: Final[int] = 8
SP_M: Final[int] = 12
SP_L: Final[int] = 16
SP_XL: Final[int] = 24
SP_XXL: Final[int] = 32

# Raios (px)
R_SM: Final[int] = 6
R_MD: Final[int] = 10
R_LG: Final[int] = 14

# Tipografia (pt)
FONT_DISPLAY_PT: Final[int] = 28
FONT_TITLE_PT: Final[int] = 20
FONT_SUBTITLE_PT: Final[int] = 14
FONT_BODY_PT: Final[int] = 13
FONT_CAPTION_PT: Final[int] = 11

# Cores semânticas (hex) — alinhadas a theme.py + style.qss
LIGHT: Final[dict[str, str]] = {
    "window_bg": "#F5F7FA",
    "surface_card": "#FFFFFF",
    "surface_muted": "#F3F4F6",
    "surface_alt": "#F9FAFB",
    "border": "#E5E7EB",
    "border_strong": "#D1D5DB",
    "text": "#111827",
    "text_secondary": "#374151",
    "text_muted": "#6B7280",
    "accent": "#4C8BF5",
    "accent_strong": "#2563EB",
    "accent_hover": "#1D4ED8",
    "sidebar_bg": "#111827",
    "sidebar_text": "#D1D5DB",
    "sidebar_title": "#F9FAFB",
    "sidebar_muted": "#9CA3AF",
    "sidebar_hover": "#1F2937",
    "sidebar_border_sel": "#4C8BF5",
    "sidebar_border_focus": "#93C5FD",
    "success": "#15803d",
    "danger": "#b91c1c",
    "danger_soft": "#FCA5A5",
    "danger_bg_hover": "#FEF2F2",
    "info_sel_bg": "#BFDBFE",
    "combo_sel_bg": "#DBEAFE",
    "dialog_bg": "#F0F4F8",
    "scrollbar_track": "#EEF2F7",
    "scrollbar_handle": "#CBD5E1",
    "scrollbar_handle_hover": "#94A3B8",
    "positive_delta": "#15803d",
    "negative_delta": "#b91c1c",
}

DARK: Final[dict[str, str]] = {
    "window_bg": "#0F172A",
    "surface_card": "#1E293B",
    "surface_muted": "#162032",
    "surface_alt": "#162032",
    "border": "#334155",
    "border_strong": "#475569",
    "text": "#F1F5F9",
    "text_secondary": "#CBD5E1",
    "text_muted": "#94A3B8",
    "accent": "#60A5FA",
    "accent_strong": "#3B82F6",
    "accent_hover": "#2563EB",
    "sidebar_bg": "#020617",
    "sidebar_text": "#CBD5E1",
    "sidebar_title": "#F8FAFC",
    "sidebar_muted": "#94A3B8",
    "sidebar_hover": "#0F172A",
    "sidebar_border_sel": "#60A5FA",
    "sidebar_border_focus": "#93C5FD",
    "success": "#4ADE80",
    "danger": "#F87171",
    "danger_soft": "#7F1D1D",
    "danger_bg_hover": "#450A0A",
    "info_sel_bg": "#1E40AF",
    "combo_sel_bg": "#1E40AF",
    "dialog_bg": "#0F172A",
    "scrollbar_track": "#1E293B",
    "scrollbar_handle": "#475569",
    "scrollbar_handle_hover": "#64748B",
    "positive_delta": "#4ADE80",
    "negative_delta": "#F87171",
}


def palette_dict(theme: str) -> dict[str, str]:
    return DARK if theme == "dark" else LIGHT


def qcolor(theme: str, key: str) -> QColor:
    return QColor(palette_dict(theme)[key])


def density_scale_pt() -> int:
    from PySide6.QtCore import QSettings

    q = QSettings()
    base = 0
    if q.value("ui/density", "comfortable") == "compact":
        base -= 1
    if q.value("ui/font_scale", "normal") == "large":
        base += 1
    return base


def extra_stylesheet(theme: str) -> str:
    """QSS adicional para widgets novos (toast, chips, hero, paleta, seções)."""
    c = palette_dict(theme)
    r_md = R_MD
    r_lg = R_LG
    sp_s = SP_S
    sp_m = SP_M
    sp_l = SP_L
    return f"""
QLabel#FormSectionTitle {{
    color: {c["text_secondary"]};
    font-size: 13px;
    margin-top: 4px;
}}
QFrame#ToastHost {{
    background-color: transparent;
}}
QFrame#Toast {{
    background-color: {c["surface_card"]};
    border: 1px solid {c["border"]};
    border-radius: {r_md}px;
    padding: {sp_m}px {sp_l}px;
}}
QLabel#ToastMessage {{
    color: {c["text"]};
    font-size: {FONT_BODY_PT}px;
}}
QPushButton#ToastAction {{
    background-color: transparent;
    border: none;
    color: {c["accent_strong"]};
    font-weight: 600;
    padding: {sp_s}px {sp_m}px;
}}
QPushButton#ChipFilter {{
    background-color: {c["surface_muted"]};
    border: 1px solid {c["border"]};
    border-radius: {R_SM}px;
    padding: {sp_s}px {sp_m}px;
    color: {c["text"]};
}}
QPushButton#ChipFilter:checked {{
    background-color: {c["accent_strong"]};
    color: #FFFFFF;
    border-color: {c["accent_strong"]};
}}
QFrame#HeroKpi {{
    background-color: {c["surface_card"]};
    border: 1px solid {c["border"]};
    border-radius: {r_lg}px;
    padding: {SP_XL}px;
}}
QLabel#HeroKpiValue {{
    color: {c["text"]};
    font-size: 32px;
    font-weight: 700;
}}
QLabel#HeroKpiDelta {{
    font-size: {FONT_SUBTITLE_PT}px;
    font-weight: 600;
}}
QFrame#AttentionCard {{
    background-color: {c["surface_card"]};
    border: 1px solid {c["border_strong"]};
    border-radius: {r_md}px;
    padding: {sp_m}px;
}}
QFrame#AttentionCard:hover {{
    border-color: {c["accent"]};
}}
QWidget#SectionTabs QTabBar::tab {{
    min-width: 88px;
}}
QLineEdit#CommandPaletteSearch {{
    font-size: {FONT_SUBTITLE_PT}px;
    padding: {sp_m}px;
}}
QListWidget#CommandPaletteList {{
    border: none;
    background: {c["surface_card"]};
}}
QPushButton#SidebarToggle {{
    background-color: transparent;
    border: none;
    color: {c["sidebar_muted"]};
    padding: {sp_s}px;
    font-size: 16px;
}}
QPushButton#SidebarToggle:hover {{
    color: {c["sidebar_title"]};
}}
QToolBar#MainToolBar {{
    background-color: {c["surface_card"]};
    border-bottom: 1px solid {c["border"]};
    spacing: {sp_m}px;
    padding: {sp_s}px {sp_l}px;
}}
"""
