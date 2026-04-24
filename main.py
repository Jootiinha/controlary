"""Ponto de entrada do Controle Financeiro."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from app.database.migrations import run_migrations
from app.ui.main_window import MainWindow
from app.ui.theme import THEME_DARK, THEME_LIGHT, apply_theme
from app.utils.paths import resource_path


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
    # Fusion + tema explícito evita texto ilegível no macOS quando o SO está em modo escuro.
    app.setStyle("Fusion")
    settings = QSettings()
    theme = settings.value("ui/theme", THEME_LIGHT)
    if theme not in (THEME_LIGHT, THEME_DARK):
        theme = THEME_LIGHT
    apply_theme(app, theme)

    icon_path = Path(resource_path("assets/icon.png"))
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

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
