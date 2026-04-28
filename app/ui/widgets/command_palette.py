from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


class CommandPaletteDialog(QDialog):
    def __init__(
        self,
        parent,
        actions: list[tuple[str, str, Callable[[], None]]],
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Paleta de comandos")
        self.setModal(True)
        self.resize(520, 420)
        self._actions = actions
        self._ed = QLineEdit()
        self._ed.setObjectName("CommandPaletteSearch")
        self._ed.setPlaceholderText("Buscar ação ou seção…")
        self._list = QListWidget()
        self._list.setObjectName("CommandPaletteList")
        self._list.itemActivated.connect(self._on_activate_item)
        self._list.itemDoubleClicked.connect(self._on_activate_item)
        lay = QVBoxLayout(self)
        lay.addWidget(self._ed)
        lay.addWidget(self._list, 1)
        row = QHBoxLayout()
        row.addStretch()
        close = QPushButton("Fechar")
        close.clicked.connect(self.reject)
        row.addWidget(close)
        lay.addLayout(row)
        self._ed.textChanged.connect(self._refilter)
        self._refilter("")
        self._ed.setFocus()

    def _refilter(self, text: str) -> None:
        needle = (text or "").strip().casefold()
        self._list.clear()
        for aid, label, _cb in self._actions:
            hay = f"{aid} {label}".casefold()
            if needle and needle not in hay:
                continue
            it = QListWidgetItem(label)
            it.setData(Qt.ItemDataRole.UserRole, aid)
            self._list.addItem(it)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _on_activate_item(self, item: QListWidgetItem) -> None:
        aid = item.data(Qt.ItemDataRole.UserRole)
        for a, _l, cb in self._actions:
            if a == aid:
                self.accept()
                cb()
                return

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            it = self._list.currentItem()
            if it is not None:
                self._on_activate_item(it)
            return
        super().keyPressEvent(event)
