"""Página CRUD genérica: título, toolbar e tabela."""
from __future__ import annotations

from typing import List

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class SimpleTableModel(QAbstractTableModel):
    """Modelo de tabela simples baseado em listas de strings."""

    def __init__(self, headers: List[str]) -> None:
        super().__init__()
        self._headers = headers
        self._rows: list[list[str]] = []
        self._ids: list[int] = []

    def set_rows(self, rows: list[tuple[int, list[str]]]) -> None:
        self.beginResetModel()
        self._ids = [r[0] for r in rows]
        self._rows = [r[1] for r in rows]
        self.endResetModel()

    def row_id(self, row: int) -> int | None:
        if 0 <= row < len(self._ids):
            return self._ids[row]
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._rows[index.row()][index.column()]
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignVCenter | Qt.AlignLeft)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation,  # noqa: N802
                   role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._headers[section]
        return section + 1


class CrudPage(QWidget):
    """Widget base com header e tabela. Subclasses implementam ações."""

    def __init__(self, title: str, subtitle: str, headers: List[str]) -> None:
        super().__init__()

        lbl_title = QLabel(title)
        lbl_title.setObjectName("PageTitle")
        lbl_subtitle = QLabel(subtitle)
        lbl_subtitle.setObjectName("PageSubtitle")

        self.btn_add = QPushButton("Adicionar")
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_edit = QPushButton("Editar")
        self.btn_delete = QPushButton("Excluir")
        self.btn_delete.setObjectName("DangerButton")
        self.btn_refresh = QPushButton("Atualizar")

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_refresh)

        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        header_box.addWidget(lbl_title)
        header_box.addWidget(lbl_subtitle)

        self.model = SimpleTableModel(headers)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(lambda _: self.btn_edit.click())
        self.table.setMinimumHeight(120)
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(14)
        outer.addLayout(header_box)
        outer.addLayout(toolbar)
        outer.addWidget(self.table, 1)

    def selected_id(self) -> int | None:
        idx = self.table.currentIndex()
        if not idx.isValid():
            return None
        return self.model.row_id(idx.row())
