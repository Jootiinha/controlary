"""Paleta, QSS e preferência de tema (claro / escuro)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from app.ui import design_tokens as dt
from app.utils.paths import resource_path

THEME_LIGHT = "light"
THEME_DARK = "dark"


def apply_light_palette(app: QApplication) -> None:
    c = dt.LIGHT
    p = QPalette()
    base = QColor(c["surface_card"])
    text = QColor(c["text"])
    muted = QColor(c["text_muted"])
    window_bg = QColor(c["window_bg"])
    border = QColor(c["border"])
    accent = QColor(c["accent"])

    p.setColor(QPalette.ColorRole.Window, window_bg)
    p.setColor(QPalette.ColorRole.WindowText, text)
    p.setColor(QPalette.ColorRole.Base, base)
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(c["surface_alt"]))
    p.setColor(QPalette.ColorRole.Text, text)
    p.setColor(QPalette.ColorRole.PlaceholderText, muted)
    p.setColor(QPalette.ColorRole.Button, base)
    p.setColor(QPalette.ColorRole.ButtonText, text)
    p.setColor(QPalette.ColorRole.Highlight, accent)
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    p.setColor(QPalette.ColorRole.ToolTipBase, base)
    p.setColor(QPalette.ColorRole.ToolTipText, text)
    p.setColor(QPalette.ColorRole.Mid, border)
    app.setPalette(p)


def apply_dark_palette(app: QApplication) -> None:
    c = dt.DARK
    p = QPalette()
    base = QColor(c["surface_card"])
    text = QColor(c["text"])
    muted = QColor(c["text_muted"])
    window_bg = QColor(c["window_bg"])
    border = QColor(c["border"])
    accent = QColor(c["accent"])

    p.setColor(QPalette.ColorRole.Window, window_bg)
    p.setColor(QPalette.ColorRole.WindowText, text)
    p.setColor(QPalette.ColorRole.Base, base)
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(c["surface_alt"]))
    p.setColor(QPalette.ColorRole.Text, text)
    p.setColor(QPalette.ColorRole.PlaceholderText, muted)
    p.setColor(QPalette.ColorRole.Button, QColor(c["border_strong"]))
    p.setColor(QPalette.ColorRole.ButtonText, text)
    p.setColor(QPalette.ColorRole.Highlight, accent)
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(c["window_bg"]))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(c["surface_card"]))
    p.setColor(QPalette.ColorRole.ToolTipText, text)
    p.setColor(QPalette.ColorRole.Mid, border)
    app.setPalette(p)


def apply_theme(app: QApplication, theme: str) -> None:
    if theme == THEME_DARK:
        apply_dark_palette(app)
        qss_name = "style_dark.qss"
    else:
        apply_light_palette(app)
        qss_name = "style.qss"
    path = Path(resource_path(f"app/ui/{qss_name}"))
    base = path.read_text(encoding="utf-8") if path.exists() else ""
    extra = dt.extra_stylesheet(theme)
    scale = dt.density_scale_pt()
    density_qss = ""
    if scale != 0:
        density_qss = f"* {{ font-size: {13 + scale}px; }}\n"
    app.setStyleSheet(base + "\n" + extra + "\n" + density_qss)
