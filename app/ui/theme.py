"""Paleta, QSS e preferência de tema (claro / escuro)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from app.utils.paths import resource_path

THEME_LIGHT = "light"
THEME_DARK = "dark"


def apply_light_palette(app: QApplication) -> None:
    p = QPalette()
    base = QColor("#FFFFFF")
    text = QColor("#111827")
    muted = QColor("#6B7280")
    window_bg = QColor("#F5F7FA")
    border = QColor("#E5E7EB")
    accent = QColor("#4C8BF5")

    p.setColor(QPalette.ColorRole.Window, window_bg)
    p.setColor(QPalette.ColorRole.WindowText, text)
    p.setColor(QPalette.ColorRole.Base, base)
    p.setColor(QPalette.ColorRole.AlternateBase, QColor("#F9FAFB"))
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
    p = QPalette()
    base = QColor("#1E293B")
    text = QColor("#F1F5F9")
    muted = QColor("#94A3B8")
    window_bg = QColor("#0F172A")
    border = QColor("#334155")
    accent = QColor("#60A5FA")

    p.setColor(QPalette.ColorRole.Window, window_bg)
    p.setColor(QPalette.ColorRole.WindowText, text)
    p.setColor(QPalette.ColorRole.Base, base)
    p.setColor(QPalette.ColorRole.AlternateBase, QColor("#162032"))
    p.setColor(QPalette.ColorRole.Text, text)
    p.setColor(QPalette.ColorRole.PlaceholderText, muted)
    p.setColor(QPalette.ColorRole.Button, QColor("#334155"))
    p.setColor(QPalette.ColorRole.ButtonText, text)
    p.setColor(QPalette.ColorRole.Highlight, accent)
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#0F172A"))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1E293B"))
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
    if path.exists():
        app.setStyleSheet(path.read_text(encoding="utf-8"))
    else:
        app.setStyleSheet("")
