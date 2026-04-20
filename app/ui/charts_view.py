"""Tela de gráficos analíticos (tendências e indicadores)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.charts import (
    category_month_views,
    comprometimento_renda,
    debt_evolution,
    investments_overview,
    invoice_evolution,
    invoices_history,
    monthly_expenses,
    renda_vs_despesa,
)
from app.ui.widgets.chart_canvas import ChartCanvas


class ChartsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ChartsPage")

        lbl_title = QLabel("Gráficos e análises")
        lbl_title.setObjectName("PageTitle")
        lbl_sub = QLabel(
            "Indicadores consolidados: renda, gastos, cartão, categorias e investimentos."
        )
        lbl_sub.setObjectName("PageSubtitle")
        lbl_sub.setWordWrap(True)

        self._canvases: list[ChartCanvas] = []

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_overview_tab(), "Visão geral")
        self.tabs.addTab(self._build_card_tab(), "Cartão")
        self.tabs.addTab(self._build_categories_tab(), "Categorias")
        self.tabs.addTab(self._build_investments_tab(), "Investimentos")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sub)
        layout.addWidget(self.tabs)

    def _append_canvas(
        self,
        renderer,
        *,
        height: float | None = None,
        content_min_height: int | None = None,
    ) -> ChartCanvas:
        kw: dict[str, float] = {}
        if height is not None:
            kw["height"] = height
        canvas = ChartCanvas(renderer, **kw)
        if content_min_height is not None:
            canvas.setMinimumHeight(content_min_height)
        self._canvases.append(canvas)
        return canvas

    def _wrap_scrolled(self, inner: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setWidget(inner)
        return scroll

    def _build_overview_tab(self) -> QWidget:
        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(10, 10, 10, 10)
        min_h = 248
        lay.addWidget(self._append_canvas(renda_vs_despesa.plot, content_min_height=min_h))
        lay.addWidget(
            self._append_canvas(comprometimento_renda.plot, content_min_height=min_h)
        )
        lay.addWidget(self._append_canvas(monthly_expenses.plot, content_min_height=min_h))
        return self._wrap_scrolled(wrapper)

    def _build_card_tab(self) -> QWidget:
        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(10, 10, 10, 10)
        min_h = 248
        lay.addWidget(self._append_canvas(invoice_evolution.plot, content_min_height=min_h))
        lay.addWidget(
            self._append_canvas(invoice_evolution.plot_by_card, content_min_height=min_h)
        )
        lay.addWidget(
            self._append_canvas(invoices_history.plot, content_min_height=min_h)
        )
        lay.addWidget(self._append_canvas(debt_evolution.plot, content_min_height=min_h))
        return self._wrap_scrolled(wrapper)

    def _build_categories_tab(self) -> QWidget:
        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(10, 10, 10, 10)
        min_h = 240
        lay.addWidget(
            self._append_canvas(
                category_month_views.make_plot_ledger(),
                height=2.85,
                content_min_height=min_h,
            )
        )
        lay.addWidget(
            self._append_canvas(
                category_month_views.make_plot_cost_of_living(),
                height=2.85,
                content_min_height=min_h,
            )
        )
        return self._wrap_scrolled(wrapper)

    def _build_investments_tab(self) -> QWidget:
        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(
            self._append_canvas(investments_overview.plot, content_min_height=300)
        )
        return wrapper

    def reload(self) -> None:
        for canvas in self._canvases:
            canvas.refresh()
