"""Combo de categoria + botão para nova categoria."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

from app.events import app_events
from app.services import categories_service


class CategoryPicker(QWidget):
    """Seletor de categoria global (somente lista cadastrada)."""

    category_changed = Signal()

    def __init__(self, parent=None, allow_empty: bool = True) -> None:
        super().__init__(parent)
        self._allow_empty = allow_empty
        self._combo = QComboBox()
        self._combo.setEditable(False)
        self._btn_new = QPushButton("Nova…")
        self._btn_new.setToolTip("Cadastrar nova categoria")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.addWidget(self._combo, 1)
        lay.addWidget(self._btn_new)
        self._reload_options()
        self._combo.currentIndexChanged.connect(self._on_combo_index_changed)

    def _on_combo_index_changed(self, _index: int) -> None:
        self.category_changed.emit()

    def _reload_options(self) -> None:
        self._combo.blockSignals(True)
        cur = self.current_category_id()
        self._combo.clear()
        if self._allow_empty:
            self._combo.addItem("(Nenhuma)", None)
        for c in categories_service.list_all():
            if c.id is not None:
                self._combo.addItem(c.nome, c.id)
        if cur is not None:
            self.set_category_id(cur)
        self._combo.blockSignals(False)

    def current_category_id(self) -> Optional[int]:
        d = self._combo.currentData()
        return int(d) if d is not None else None

    def set_category_id(self, cat_id: Optional[int]) -> None:
        if cat_id is None:
            if self._allow_empty:
                self._combo.setCurrentIndex(0)
            return
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == cat_id:
                self._combo.setCurrentIndex(i)
                return
        self._reload_options()
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == cat_id:
                self._combo.setCurrentIndex(i)
                return

    def reload_from_db(self) -> None:
        self._reload_options()

    def connect_new_button(self, slot) -> None:
        self._btn_new.clicked.connect(slot)


def emit_parent_view_data_changed(widget: QWidget) -> None:
    """Propaga criação de categoria (``categories_service`` já emite ``categories_changed``)."""
    app_events().categories_changed.emit()
