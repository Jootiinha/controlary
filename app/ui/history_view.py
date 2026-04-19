"""Tela de histórico consolidado + gráficos."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.charts import (
    category_month_views,
    comprometimento_renda,
    debt_evolution,
    fluxo_acumulado,
    investments_overview,
    invoice_evolution,
    monthly_expenses,
    renda_vs_despesa,
)
from app.services import payments_service
from app.ui.widgets.chart_canvas import ChartCanvas
from app.ui.widgets.readonly_table import ReadOnlyTable
from app.utils.formatting import format_currency, format_date_br


class HistoryView(QWidget):
    def __init__(self) -> None:
        super().__init__()

        lbl_title = QLabel("Histórico e análises")
        lbl_title.setObjectName("PageTitle")
        lbl_sub = QLabel(
            "Transações, projeções e indicadores consolidados (renda, gastos, categorias, investimentos)."
        )
        lbl_sub.setObjectName("PageSubtitle")

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_history_tab(), "Transações")
        self.tabs.addTab(self._build_chart_tab(renda_vs_despesa.plot), "Renda vs despesa")
        self.tabs.addTab(self._build_chart_tab(fluxo_acumulado.plot), "Fluxo acumulado")
        self.tabs.addTab(
            self._build_chart_tab(comprometimento_renda.plot), "Comprometimento %"
        )
        self.tabs.addTab(self._build_chart_tab(monthly_expenses.plot), "Custo de vida")
        self.tabs.addTab(self._build_chart_tab(invoice_evolution.plot), "Evolução da fatura")
        self.tabs.addTab(self._build_categories_tab(), "Categorias")
        self.tabs.addTab(self._build_chart_tab(debt_evolution.plot), "Saldo devedor")
        self.tabs.addTab(
            self._build_chart_tab(investments_overview.plot), "Investimentos"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
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

    def _build_chart_tab(self, renderer) -> QWidget:
        canvas = ChartCanvas(renderer)
        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(canvas)
        wrapper._canvas = canvas  # type: ignore[attr-defined]
        return wrapper

    def _build_categories_tab(self) -> QWidget:
        c1 = ChartCanvas(category_month_views.make_plot_ledger(), height=3.2)
        c2 = ChartCanvas(category_month_views.make_plot_cost_of_living(), height=3.2)
        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(c1)
        lay.addWidget(c2)
        wrapper._canvases = [c1, c2]  # type: ignore[attr-defined]
        return wrapper

    def reload(self) -> None:
        payments = payments_service.list_all()
        rows = []
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
        self.tbl_history.set_rows(rows)

        for i in range(1, self.tabs.count()):
            tab = self.tabs.widget(i)
            multi = getattr(tab, "_canvases", None)
            if multi:
                for c in multi:
                    c.refresh()
                continue
            canvas = getattr(tab, "_canvas", None)
            if canvas is not None:
                canvas.refresh()
