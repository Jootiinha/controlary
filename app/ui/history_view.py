"""Tela de histórico consolidado (transações e mapeamentos)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.services import categories_service, payments_service
from app.ui.ui_wait import wait_cursor
from app.ui.widgets.readonly_table import ReadOnlyTable
from app.utils.formatting import format_currency, format_date_br


class HistoryView(QWidget):
    def __init__(self) -> None:
        super().__init__()

        lbl_title = QLabel("Histórico")
        lbl_title.setObjectName("PageTitle")
        lbl_sub = QLabel(
            "Lista de transações e regras de categorização das despesas."
        )
        lbl_sub.setObjectName("PageSubtitle")

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_history_tab(), "Transações")
        self.tabs.addTab(self._build_expense_categories_tab(), "Despesas por categoria")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sub)
        layout.addWidget(self.tabs)

    def _build_history_tab(self) -> QWidget:
        self.tbl_history = ReadOnlyTable(
            ["Data", "Descrição", "Origem", "Categoria", "Forma", "Valor"],
            selectable=True,
        )

        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(self.tbl_history)
        return wrapper

    def _build_expense_categories_tab(self) -> QWidget:
        self.tbl_expense_categories = ReadOnlyTable(
            ["Tipo", "Despesa", "Categoria", "Detalhe"],
            selectable=True,
        )
        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(self.tbl_expense_categories)
        return wrapper

    def reload(self) -> None:
        with wait_cursor():
            self._reload_impl()

    def _reload_impl(self) -> None:
        payments = payments_service.list_all()
        rows = []
        sort_keys: list[list[object]] = []
        for p in payments:
            orig = p.conta_nome or p.cartao_nome or "—"
            rows.append(
                [
                    format_date_br(p.data),
                    p.descricao,
                    orig,
                    p.categoria_nome or "—",
                    p.forma_pagamento,
                    format_currency(p.valor),
                ]
            )
            sort_keys.append(
                [
                    p.data,
                    (p.descricao or "").casefold(),
                    orig.casefold(),
                    (p.categoria_nome or "—").casefold(),
                    (p.forma_pagamento or "").casefold(),
                    float(p.valor),
                ]
            )
        self.tbl_history.set_rows(rows, sort_keys=sort_keys)

        mappings = categories_service.list_expense_category_mappings()
        ec_rows = []
        ec_keys: list[list[object]] = []
        for tipo, nome, cat, det in mappings:
            ec_rows.append([tipo, nome, cat, det])
            ec_keys.append(
                [tipo.casefold(), nome.casefold(), cat.casefold(), det.casefold()]
            )
        self.tbl_expense_categories.set_rows(ec_rows, sort_keys=ec_keys)
