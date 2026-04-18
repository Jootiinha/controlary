"""Tela inicial com indicadores agregados."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.charts import year_expense_evolution
from app.services import dashboard_service
from app.ui.widgets.card import KpiCard
from app.ui.widgets.chart_canvas import ChartCanvas
from app.utils.formatting import format_currency, format_month_br


class DashboardView(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.lbl_title = QLabel("Dashboard")
        self.lbl_title.setObjectName("PageTitle")
        self.lbl_subtitle = QLabel("Visão geral do mês corrente")
        self.lbl_subtitle.setObjectName("PageSubtitle")

        self.card_gasto_mes = KpiCard("Gasto no mês", compact=True)
        self.card_previsto = KpiCard(
            "Previsto do mês",
            subtitle="Assinaturas + parcelas + fixos pendentes",
            compact=True,
        )
        self.card_assinaturas = KpiCard("Assinaturas ativas", compact=True)
        self.card_parcelamentos = KpiCard("Parcelamentos ativos", compact=True)
        self.card_saldo_devedor = KpiCard(
            "Saldo devedor", subtitle="Parcelamentos ativos", compact=True
        )
        self.card_parcelas_mes = KpiCard("Parcelas do mês", compact=True)
        self.card_fixos_mes = KpiCard(
            "Fixos pendentes",
            subtitle="Competência atual",
            compact=True,
        )
        self.card_fixos_ano = KpiCard(
            "Fixos — restante do ano",
            subtitle="Pendentes até dez.",
            compact=True,
        )

        grid = QGridLayout()
        grid.setSpacing(10)
        for c in range(4):
            grid.setColumnStretch(c, 1)
        grid.addWidget(self.card_gasto_mes, 0, 0)
        grid.addWidget(self.card_previsto, 0, 1)
        grid.addWidget(self.card_parcelas_mes, 0, 2)
        grid.addWidget(self.card_fixos_mes, 0, 3)
        grid.addWidget(self.card_assinaturas, 1, 0)
        grid.addWidget(self.card_parcelamentos, 1, 1)
        grid.addWidget(self.card_saldo_devedor, 1, 2)
        grid.addWidget(self.card_fixos_ano, 1, 3)

        self.chart_year = ChartCanvas(
            year_expense_evolution.plot,
            width=10.0,
            height=2.8,
            dpi=100,
        )
        self.chart_year.setMinimumHeight(160)
        self.chart_year.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        lbl_chart = QLabel("Evolução das despesas no ano")
        lbl_chart.setObjectName("PageSubtitle")

        chart_box = QWidget()
        chart_lay = QVBoxLayout(chart_box)
        chart_lay.setContentsMargins(0, 0, 0, 0)
        chart_lay.setSpacing(8)
        chart_lay.addWidget(lbl_chart)
        chart_lay.addWidget(self.chart_year, 1)

        self.tbl_contas = self._make_table(["Conta", "Total do mês"])
        self.tbl_formas = self._make_table(["Forma de pagamento", "Total do mês"])

        breakdown_box = QHBoxLayout()
        breakdown_box.setSpacing(14)
        breakdown_box.addWidget(self._titled("Gastos por conta", self.tbl_contas), 1)
        breakdown_box.addWidget(
            self._titled("Gastos por forma de pagamento", self.tbl_formas), 1
        )

        inner = QVBoxLayout(self)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(12)
        inner.addWidget(self.lbl_title)
        inner.addWidget(self.lbl_subtitle)
        inner.addLayout(grid, 0)
        inner.addWidget(chart_box, 2)
        inner.addLayout(breakdown_box, 1)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.reload()

    def _make_table(self, headers: list[str]) -> QTableWidget:
        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setSelectionMode(QAbstractItemView.NoSelection)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.setMinimumHeight(88)
        tbl.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        return tbl

    def _titled(self, title: str, widget: QWidget) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        lbl = QLabel(title)
        lbl.setObjectName("PageSubtitle")
        layout.addWidget(lbl)
        layout.addWidget(widget, 1)
        return wrapper

    def reload(self) -> None:
        data = dashboard_service.load()
        self.lbl_subtitle.setText(f"Referência: {format_month_br(data.mes_referencia)}")

        self.card_gasto_mes.set_value(format_currency(data.total_gasto_mes))
        self.card_previsto.set_value(format_currency(data.previsto_mes))
        self.card_assinaturas.set_value(
            f"{data.assinaturas_ativas_qtd} ativas"
        )
        self.card_assinaturas.set_subtitle(
            f"Total mensal: {format_currency(data.assinaturas_ativas_valor)}"
        )
        self.card_parcelamentos.set_value(f"{data.parcelamentos_ativos_qtd} ativos")
        self.card_saldo_devedor.set_value(format_currency(data.saldo_devedor_total))
        self.card_parcelas_mes.set_value(format_currency(data.parcelas_mes_atual))
        self.card_fixos_mes.set_value(format_currency(data.fixos_pendentes_mes))
        self.card_fixos_mes.set_subtitle(
            f"{format_month_br(data.mes_referencia)} · {data.fixos_ativos_qtd} ativos"
        )
        self.card_fixos_ano.set_value(format_currency(data.fixos_restante_ano))

        self._fill_table(self.tbl_contas, data.gastos_por_conta)
        self._fill_table(self.tbl_formas, data.gastos_por_forma)

        self.chart_year.refresh()

    def _fill_table(self, tbl: QTableWidget, rows: list[tuple[str, float]]) -> None:
        if not rows:
            tbl.setRowCount(1)
            tbl.setItem(0, 0, QTableWidgetItem("Sem lançamentos no mês"))
            tbl.setItem(0, 1, QTableWidgetItem("—"))
            return
        tbl.setRowCount(len(rows))
        for i, (label, value) in enumerate(rows):
            tbl.setItem(i, 0, QTableWidgetItem(label))
            tbl.setItem(i, 1, QTableWidgetItem(format_currency(value)))
