"""Tabela somente leitura com configuração padrão e cabeçalho com quebra de linha."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
)

from app.ui.widgets.wrapping_header import WrappingHeaderView


class SortableTableWidgetItem(QTableWidgetItem):
    """Item que ordena por ``UserRole`` quando ambos têm chave; senão por texto."""

    def __lt__(self, other: QTableWidgetItem) -> bool:
        if not isinstance(other, QTableWidgetItem):
            return NotImplemented
        k1 = self.data(Qt.ItemDataRole.UserRole)
        k2 = other.data(Qt.ItemDataRole.UserRole)
        if k1 is not None and k2 is not None:
            try:
                return bool(k1 < k2)
            except TypeError:
                pass
        return (self.text() or "").casefold() < (other.text() or "").casefold()


class ReadOnlyTable(QTableWidget):
    ALIGN_LEFT = int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
    ALIGN_CENTER = int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
    ALIGN_RIGHT = int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

    def __init__(
        self,
        headers: list[str],
        *,
        selectable: bool = False,
        selection_behavior: QAbstractItemView.SelectionBehavior = (
            QAbstractItemView.SelectionBehavior.SelectItems
        ),
        wrapping_header: bool = True,
        column_aligns: list[int] | None = None,
        fixed_height: int | None = None,
        min_height: int | None = None,
        stretch_mode: QHeaderView.ResizeMode = QHeaderView.ResizeMode.Stretch,
        section_resize_modes: list[QHeaderView.ResizeMode] | None = None,
        alternating_row_colors: bool = False,
        show_grid: bool = False,
        word_wrap: bool = True,
        vertical_header_default_section_size: int | None = None,
        column_widths: dict[int, int] | None = None,
        header_default_alignment: Qt.AlignmentFlag | None = None,
        stretch_last_section: bool | None = None,
        size_policy: tuple[QSizePolicy.Policy, QSizePolicy.Policy] | None = None,
        sorting_enabled: bool = True,
    ) -> None:
        super().__init__(0, len(headers))
        self._column_aligns = column_aligns
        self._sorting_enabled = sorting_enabled
        if wrapping_header:
            self.setHorizontalHeader(WrappingHeaderView(self))
        self.setHorizontalHeaderLabels(headers)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
            if selectable
            else QAbstractItemView.SelectionMode.NoSelection
        )
        self.setSelectionBehavior(selection_behavior)
        self.setAlternatingRowColors(alternating_row_colors)
        self.setShowGrid(show_grid)
        self.setWordWrap(word_wrap)

        th = self.horizontalHeader()
        if header_default_alignment is not None:
            th.setDefaultAlignment(header_default_alignment)
        if stretch_last_section is not None:
            th.setStretchLastSection(stretch_last_section)

        if section_resize_modes is not None:
            if len(section_resize_modes) != len(headers):
                raise ValueError("section_resize_modes deve ter o mesmo tamanho que headers")
            for i, mode in enumerate(section_resize_modes):
                th.setSectionResizeMode(i, mode)
        else:
            th.setSectionResizeMode(stretch_mode)

        if vertical_header_default_section_size is not None:
            self.verticalHeader().setDefaultSectionSize(vertical_header_default_section_size)

        if column_widths:
            for col, w in column_widths.items():
                self.setColumnWidth(col, w)

        if fixed_height is not None:
            self.setFixedHeight(fixed_height)
        if min_height is not None:
            self.setMinimumHeight(min_height)

        if size_policy is not None:
            pol_h, pol_v = size_policy
            self.setSizePolicy(pol_h, pol_v)

        self.setSortingEnabled(self._sorting_enabled)

    def set_rows(
        self,
        rows: list[list[str]],
        *,
        empty_message: str | None = None,
        empty_row: list[str] | None = None,
        sort_keys: list[list[Any | None]] | None = None,
    ) -> None:
        ncols = self.columnCount()
        if sort_keys is not None and len(sort_keys) != len(rows):
            raise ValueError("sort_keys deve ter uma entrada por linha em rows")
        if sort_keys is not None:
            for rk in sort_keys:
                if len(rk) != ncols:
                    raise ValueError("cada sort_keys[r] deve ter uma entrada por coluna")

        if self._sorting_enabled:
            self.setSortingEnabled(False)
        try:
            if not rows:
                if empty_row is not None:
                    if len(empty_row) != ncols:
                        raise ValueError("empty_row deve ter uma célula por coluna")
                    self.setRowCount(1)
                    for c, text in enumerate(empty_row):
                        self.setItem(0, c, self._make_item(c, text, None))
                    return
                if empty_message is not None:
                    self.setRowCount(1)
                    self.setItem(0, 0, self._make_item(0, empty_message, None))
                    for c in range(1, ncols):
                        self.setItem(0, c, self._make_item(c, "—", None))
                    return
                self.setRowCount(0)
                return

            self.setRowCount(len(rows))
            for r, row in enumerate(rows):
                if len(row) != ncols:
                    raise ValueError("cada linha deve ter uma célula por coluna")
                for c, text in enumerate(row):
                    sk = None
                    if sort_keys is not None:
                        sk = sort_keys[r][c]
                    self.setItem(r, c, self._make_item(c, text, sk))
        finally:
            if self._sorting_enabled:
                self.setSortingEnabled(True)

    def _make_item(
        self,
        column: int,
        text: str,
        sort_key: Any | None,
    ) -> QTableWidgetItem:
        if self._sorting_enabled:
            it: QTableWidgetItem = SortableTableWidgetItem(text)
            if sort_key is not None:
                it.setData(Qt.ItemDataRole.UserRole, sort_key)
        else:
            it = QTableWidgetItem(text)
        if self._column_aligns is not None and column < len(self._column_aligns):
            it.setTextAlignment(self._column_aligns[column])
        return it
