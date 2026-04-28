"""Página CRUD genérica: título, toolbar, busca, totais opcionais e tabela."""
from __future__ import annotations

from typing import List

from collections.abc import Callable

from PySide6.QtCore import (
    QAbstractTableModel,
    QCollator,
    QLocale,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.readonly_table import apply_default_header_resize_modes
from app.ui.widgets.wrapping_header import WrappingHeaderView
from app.utils.formatting import compare_sort_display_values


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


class _MultiColumnFilterProxyModel(QSortFilterProxyModel):
    """Filtro por substring em qualquer coluna (case-insensitive)."""

    def __init__(self) -> None:
        super().__init__()
        self._needle = ""

    def set_filter_needle(self, text: str) -> None:
        self._needle = text.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex
    ) -> bool:
        if not self._needle:
            return True
        model = self.sourceModel()
        if model is None:
            return True
        for c in range(model.columnCount(source_parent)):
            idx = model.index(source_row, c, source_parent)
            text = (model.data(idx, Qt.DisplayRole) or "").lower()
            if self._needle in text:
                return True
        return False

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        model = self.sourceModel()
        if model is None:
            return super().lessThan(left, right)
        if left.column() != right.column():
            return super().lessThan(left, right)
        a = str(model.data(left, Qt.DisplayRole) or "").strip()
        b = str(model.data(right, Qt.DisplayRole) or "").strip()
        cmp = compare_sort_display_values(a, b)
        if cmp is not None:
            return cmp < 0
        collator = QCollator(QLocale(QLocale.Portuguese, QLocale.Brazil))
        return collator.compare(a, b) < 0


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
        self.btn_add.setToolTip("Incluir um novo registro")
        self.btn_edit = QPushButton("Editar")
        self.btn_edit.setToolTip("Alterar o registro selecionado na tabela")
        self.btn_delete = QPushButton("Excluir")
        self.btn_delete.setObjectName("DangerButton")
        self.btn_delete.setToolTip("Remover permanentemente o registro selecionado")
        self.btn_refresh = QPushButton("Atualizar")
        self.btn_refresh.setToolTip("Recarregar dados da tabela a partir do banco")

        self.btn_primary_extra: QPushButton | None = None

        self.ed_search = QLineEdit()
        self.ed_search.setPlaceholderText("Buscar…")
        self.ed_search.setClearButtonEnabled(True)

        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.addWidget(self.btn_add)
        self.toolbar_layout.addWidget(self.btn_edit)
        self.toolbar_layout.addWidget(self.btn_delete)
        self.toolbar_layout.addWidget(self.ed_search)
        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.btn_refresh)

        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        header_box.addWidget(lbl_title)
        header_box.addWidget(lbl_subtitle)

        self.model = SimpleTableModel(headers)
        self._proxy = _MultiColumnFilterProxyModel()
        self._proxy.setSourceModel(self.model)

        self.table = QTableView()
        self.table.setHorizontalHeader(WrappingHeaderView(self.table))
        self.table.setModel(self._proxy)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        apply_default_header_resize_modes(hdr, len(headers))
        if len(headers) >= 2:
            hdr.setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(lambda _: self.btn_edit.click())
        self.table.setMinimumHeight(120)
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        self.totals_wrap = QWidget()
        self.totals_bar = QHBoxLayout(self.totals_wrap)
        self.totals_bar.setContentsMargins(0, 0, 0, 0)
        self.totals_wrap.setVisible(False)

        self.footer_frame = QFrame()
        self.footer_frame.setObjectName("CrudFooter")
        footer_lay = QHBoxLayout(self.footer_frame)
        footer_lay.setContentsMargins(8, 6, 8, 6)
        self.lbl_footer_left = QLabel("")
        self.lbl_footer_left.setObjectName("PageSubtitle")
        self.lbl_footer_right = QLabel("")
        self.lbl_footer_right.setObjectName("PageSubtitle")
        footer_lay.addWidget(self.lbl_footer_left)
        footer_lay.addStretch()
        footer_lay.addWidget(self.lbl_footer_right)
        self.footer_frame.setVisible(False)

        self.ed_search.textChanged.connect(self._on_search_changed)

        outer = QVBoxLayout(self)
        self._main_layout = outer
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)
        outer.addLayout(header_box)
        outer.addLayout(self.toolbar_layout)
        self._filter_wrap = QWidget()
        self._filter_layout = QHBoxLayout(self._filter_wrap)
        self._filter_layout.setContentsMargins(0, 0, 0, 0)
        self._filter_layout.setSpacing(8)
        self._filter_wrap.setVisible(False)
        self._filter_chip_group: list[QPushButton] = []
        outer.addWidget(self._filter_wrap)
        outer.addWidget(self.totals_wrap)
        outer.addWidget(self.table, 1)
        outer.addWidget(self.footer_frame)

    def _on_search_changed(self, text: str) -> None:
        self._proxy.set_filter_needle(text)
        self.refresh_totals()

    def visible_row_ids(self) -> list[int]:
        ids: list[int] = []
        for row in range(self._proxy.rowCount()):
            src = self._proxy.mapToSource(self._proxy.index(row, 0))
            if not src.isValid():
                continue
            rid = self.model.row_id(src.row())
            if rid is not None:
                ids.append(rid)
        return ids

    def refresh_totals(self) -> None:
        self.compute_totals(self.visible_row_ids())

    def compute_totals(self, visible_ids: list[int]) -> None:
        pass

    def set_footer_text(self, left: str, right: str = "") -> None:
        self.lbl_footer_left.setText(left)
        self.lbl_footer_right.setText(right)
        self.footer_frame.setVisible(bool(left or right))

    def selected_id(self) -> int | None:
        idx = self.table.currentIndex()
        if not idx.isValid():
            return None
        src = self._proxy.mapToSource(idx)
        if not src.isValid():
            return None
        return self.model.row_id(src.row())

    def set_primary_action(self, text: str, slot: Callable[[], None]) -> None:
        if self.btn_primary_extra is not None:
            self.toolbar_layout.removeWidget(self.btn_primary_extra)
            self.btn_primary_extra.deleteLater()
            self.btn_primary_extra = None
        btn = QPushButton(text)
        btn.clicked.connect(slot)
        self.toolbar_layout.insertWidget(1, btn)
        self.btn_primary_extra = btn

    def add_filter_chips(self, specs: list[tuple[str, str]]) -> None:
        while self._filter_layout.count():
            item = self._filter_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._filter_chip_group.clear()
        first = True
        for cid, label in specs:
            b = QPushButton(label)
            b.setCheckable(True)
            b.setObjectName("ChipFilter")
            b.setProperty("chipId", cid)
            if first:
                b.setChecked(True)
                first = False
            b.clicked.connect(lambda _c=False, btn=b: self._on_chip_clicked(btn))
            self._filter_layout.addWidget(b)
            self._filter_chip_group.append(b)
        self._filter_layout.addStretch()
        self._filter_wrap.setVisible(bool(specs))

    def _on_chip_clicked(self, clicked: QPushButton) -> None:
        if not clicked.isChecked():
            clicked.setChecked(True)
            return
        for b in self._filter_chip_group:
            if b is not clicked:
                b.setChecked(False)
        cid = clicked.property("chipId")
        self.on_filter_chip_selected(str(cid) if cid is not None else "")

    def on_filter_chip_selected(self, chip_id: str) -> None:
        pass
