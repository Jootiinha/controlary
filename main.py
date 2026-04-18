"""Ponto de entrada do Controle Financeiro."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from app.database.migrations import run_migrations
from app.ui.main_window import MainWindow
from app.utils.paths import resource_path


def _apply_light_palette(app: QApplication) -> None:
    """Garante texto escuro sobre fundos claros em todos os widgets (incl. diálogos)."""
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


def _splash_pixmap() -> QPixmap:
    icon_path = Path(resource_path("assets/icon.png"))
    if icon_path.exists():
        pm = QPixmap(str(icon_path))
        return pm.scaled(
            400,
            400,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    pm = QPixmap(400, 280)
    pm.fill(QColor("#F5F7FA"))
    return pm


def main() -> int:
    run_migrations()

    app = QApplication(sys.argv)
    app.setApplicationName("Controle Financeiro")
    app.setOrganizationName("ControleFinanceiro")
    # Fusion + paleta clara evita texto claro em fundos claros no macOS (modo escuro do SO).
    app.setStyle("Fusion")
    _apply_light_palette(app)

    icon_path = Path(resource_path("assets/icon.png"))
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    qss_path = Path(resource_path("app/ui/style.qss"))
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    splash = QSplashScreen(_splash_pixmap())
    splash.show()
    app.processEvents()
    splash.showMessage(
        "Carregando…",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        QColor("#111827"),
    )
    app.processEvents()

    window = MainWindow()
    window.show()
    splash.finish(window)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
