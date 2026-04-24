"""Ícones da barra lateral: SVG em assets/icons/nav com fallback para ícones Qt."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle

from app.utils.paths import resource_path

_FALLBACK: dict[str, QStyle.StandardPixmap] = {
    "dashboard": QStyle.StandardPixmap.SP_FileDialogDetailedView,
    "calendar": QStyle.StandardPixmap.SP_FileDialogInfoView,
    "payments": QStyle.StandardPixmap.SP_DialogApplyButton,
    "installments": QStyle.StandardPixmap.SP_FileDialogListView,
    "subscriptions": QStyle.StandardPixmap.SP_BrowserReload,
    "fixed_expenses": QStyle.StandardPixmap.SP_DialogSaveButton,
    "card_invoices": QStyle.StandardPixmap.SP_FileIcon,
    "history": QStyle.StandardPixmap.SP_FileDialogContentsView,
    "charts": QStyle.StandardPixmap.SP_FileDialogDetailedView,
    "investments": QStyle.StandardPixmap.SP_ArrowUp,
    "accounts": QStyle.StandardPixmap.SP_DriveHDIcon,
    "categories": QStyle.StandardPixmap.SP_DirIcon,
    "income": QStyle.StandardPixmap.SP_DialogYesButton,
}


def nav_icon(key: str, style: QStyle) -> QIcon:
    base = Path(resource_path("assets/icons/nav"))
    path = base / f"{key}.svg"
    if path.is_file():
        icon = QIcon(str(path))
        if not icon.isNull():
            return icon
    sp = _FALLBACK.get(key, QStyle.StandardPixmap.SP_FileIcon)
    return style.standardIcon(sp)
