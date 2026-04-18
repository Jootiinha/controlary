"""Tela inicial com indicadores agregados."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.charts import monthly_expenses, year_expense_evolution
from app.services import calendar_service, dashboard_service, investments_service
from app.services.calendar_service import CalendarEvent
from app.ui.widgets.card import KpiCard
from app.ui.widgets.chart_canvas import ChartCanvas
from app.utils.formatting import format_currency, format_date_br, format_month_br


_CARD_MIN_W = 168
_KPI_COLS = 4


class DashboardView(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.lbl_title = QLabel("Dashboard")
        self.lbl_title.setObjectName("PageTitle")
        self.lbl_subtitle = QLabel("Visão geral do mês corrente")
        self.lbl_subtitle.setObjectName("PageSubtitle")

        # Linha 1 — Fluxo do mês
        self.card_renda = KpiCard(
            "Renda mensal", subtitle="Soma das fontes ativas", compact=True
        )
        self.card_gasto_mes = KpiCard(
            "Gasto no mês", subtitle="Lançamentos em pagamentos", compact=True
        )
        self.card_previsto = KpiCard(
            "Previsto do mês",
            subtitle="Faturas + recorrentes + fixos + avulsos (conta)",
            compact=True,
        )
        self.card_margem_previsto = KpiCard(
            "Margem de fluxo", subtitle="Renda − previsto do mês", compact=True
        )

        # Linha 2 — Investimentos e compromissos recorrentes
        self.card_invest = KpiCard(
            "Total investido",
            subtitle="Soma do valor aplicado (ativos)",
            compact=True,
        )
        self.card_fixos_mes = KpiCard(
            "Fixos pendentes", subtitle="0 ativos · restante ano —", compact=True
        )
        self.card_assinaturas = KpiCard(
            "Assinaturas", subtitle="0 ativas", compact=True
        )
        self.card_proximo = KpiCard(
            "Próximo vencimento",
            subtitle="Nenhum",
            compact=True,
        )
        self.card_proximo.setToolTip(
            "Primeiro compromisso nos próximos "
            f"{calendar_service.UPCOMING_HORIZON_DAYS} dias: "
            "fatura de cartão, assinatura em conta, fixo pendente, parcela à vista."
        )

        self.card_saldo_contas = KpiCard(
            "Saldo em contas",
            subtitle="Saldo inicial + movimentações até hoje",
            compact=True,
        )
        self.card_saldo_fim_mes = KpiCard(
            "Saldo fim do mês (est.)",
            subtitle="Contas + entradas previstas − compromissos a pagar",
            compact=True,
        )
        self.card_saldo_fim_mes.setToolTip(
            "Patrimônio líquido estimado: soma dos saldos em conta corrente, "
            "mais renda ainda esperada no mês (dia ≥ hoje e não marcada como recebida), "
            "menos fixos pendentes, faturas de cartão em aberto, assinaturas em conta "
            "e parcelas em conta ainda não marcadas como pagas na competência."
        )

        line1 = (
            self.card_renda,
            self.card_gasto_mes,
            self.card_previsto,
            self.card_margem_previsto,
        )
        line2 = (
            self.card_invest,
            self.card_fixos_mes,
            self.card_assinaturas,
            self.card_proximo,
        )
        kpi_grid = QGridLayout()
        kpi_grid.setContentsMargins(0, 0, 0, 0)
        kpi_grid.setHorizontalSpacing(12)
        kpi_grid.setVerticalSpacing(12)
        for c in range(_KPI_COLS):
            kpi_grid.setColumnMinimumWidth(c, _CARD_MIN_W)
            kpi_grid.setColumnStretch(c, 1)
        align = Qt.AlignmentFlag.AlignTop
        for col, w in enumerate(line1):
            kpi_grid.addWidget(w, 0, col, align)
        for col, w in enumerate(line2):
            kpi_grid.addWidget(w, 1, col, align)
        # Terceira linha: só 2 KPIs — cada um ocupa 2 colunas para não deixar metade da faixa vazia
        kpi_grid.addWidget(self.card_saldo_contas, 2, 0, 1, 2, align)
        kpi_grid.addWidget(self.card_saldo_fim_mes, 2, 2, 1, 2, align)

        kpi_wrap = QWidget()
        kpi_wrap.setLayout(kpi_grid)
        kpi_wrap.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.lbl_venc = QLabel(
            f"Próximos vencimentos (próx. {calendar_service.UPCOMING_HORIZON_DAYS} dias)"
        )
        self.lbl_venc.setObjectName("PageSubtitle")
        self.tbl_venc = self._make_table_venc(["Data", "Tipo", "Descrição", "Valor"])

        venc_wrap = QWidget()
        venc_wrap.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        venc_lay = QVBoxLayout(venc_wrap)
        venc_lay.setContentsMargins(0, 0, 0, 0)
        venc_lay.setSpacing(6)
        venc_lay.addWidget(self.lbl_venc)
        venc_lay.addWidget(self.tbl_venc)

        self.chart_year = ChartCanvas(
            year_expense_evolution.plot,
            width=8.0,
            height=3.2,
            dpi=100,
        )
        self.chart_year.setMinimumHeight(280)
        self.chart_year.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.chart_cost_12m = ChartCanvas(
            monthly_expenses.plot,
            width=8.0,
            height=3.2,
            dpi=100,
        )
        self.chart_cost_12m.setMinimumHeight(280)
        self.chart_cost_12m.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        chart_box = QWidget()
        chart_lay = QVBoxLayout(chart_box)
        chart_lay.setContentsMargins(0, 0, 0, 0)
        chart_lay.setSpacing(10)
        chart_lay.addWidget(self.chart_year, 1)
        chart_lay.addWidget(self.chart_cost_12m, 1)

        self.tbl_contas = self._make_table(["Conta", "Total do mês"])
        self.tbl_formas = self._make_table(["Forma de pagamento", "Total do mês"])

        tables_box = QWidget()
        tables_lay = QVBoxLayout(tables_box)
        tables_lay.setContentsMargins(0, 0, 0, 0)
        tables_lay.setSpacing(10)
        tables_lay.addWidget(self._titled("Gastos por conta", self.tbl_contas), 1)
        tables_lay.addWidget(
            self._titled("Gastos por forma de pagamento", self.tbl_formas), 1
        )

        bottom_row_wrap = QWidget()
        bottom_row_wrap.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        bottom_row_wrap.setMinimumHeight(600)
        bottom_row = QHBoxLayout(bottom_row_wrap)
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(14)
        bottom_row.addWidget(chart_box, 3)
        bottom_row.addWidget(tables_box, 1)

        content = QWidget()
        content.setObjectName("DashboardContent")
        inner = QVBoxLayout(content)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(14)
        inner.addWidget(self.lbl_title)
        inner.addWidget(self.lbl_subtitle)
        inner.addWidget(kpi_wrap, 0)
        inner.addWidget(venc_wrap, 0)
        inner.addWidget(bottom_row_wrap, 1)

        scroll = QScrollArea()
        scroll.setObjectName("DashboardScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(scroll)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.reload()

    def _make_table_venc(self, headers: list[str]) -> QTableWidget:
        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setSelectionMode(QAbstractItemView.NoSelection)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.setFixedHeight(160)
        tbl.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        return tbl

    def _make_table(self, headers: list[str]) -> QTableWidget:
        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setSelectionMode(QAbstractItemView.NoSelection)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.setMinimumHeight(220)
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

        self.card_renda.set_value(format_currency(data.renda_mensal_total))
        self.card_gasto_mes.set_value(format_currency(data.total_gasto_mes))
        self.card_previsto.set_value(format_currency(data.previsto_mes))
        self.card_previsto.setToolTip(
            "Inclui faturas de cartão em aberto (valor registrado ou sugerido), "
            "assinaturas em conta, parcelas sem cartão no mês, fixos pendentes e "
            "todos os lançamentos avulsos em conta no mês (pagamentos sem cartão). "
            "Se o mesmo gasto estiver como assinatura/fixo e também lançado em Pagamentos, "
            "pode haver sobreposição."
        )
        self.card_margem_previsto.set_value(format_currency(data.margem_apos_previsto))

        self.card_saldo_contas.set_value(format_currency(data.saldo_em_contas))
        self.card_saldo_fim_mes.set_value(format_currency(data.saldo_projetado_fim_mes))

        self.card_invest.set_value(format_currency(data.total_investido))
        self.card_invest.set_subtitle(
            f"{len(investments_service.list_all())} posição(ões) ativa(s)"
        )

        self.card_fixos_mes.set_value(format_currency(data.fixos_pendentes_mes))
        self.card_fixos_mes.set_subtitle(
            f"{data.fixos_ativos_qtd} ativos · restante ano "
            f"{format_currency(data.fixos_restante_ano)}"
        )
        self.card_assinaturas.set_value(
            format_currency(data.assinaturas_ativas_valor)
        )
        self.card_assinaturas.set_subtitle(
            f"{data.assinaturas_ativas_qtd} ativas"
        )

        if data.proximos_vencimentos:
            ev = data.proximos_vencimentos[0]
            self.card_proximo.set_value(format_currency(ev.valor))
            self.card_proximo.set_subtitle(
                f"{format_date_br(ev.data)} · {ev.titulo}"
            )
        else:
            self.card_proximo.set_value("—")
            self.card_proximo.set_subtitle("Nenhum")

        self._fill_table(self.tbl_contas, data.gastos_por_conta)
        self._fill_table(self.tbl_formas, data.gastos_por_forma)
        self._fill_vencimentos(data.proximos_vencimentos)

        self.chart_year.refresh()
        self.chart_cost_12m.refresh()

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

    _VENC_TIPO = {
        "assinatura": "Assinatura",
        "fixo": "Gasto fixo",
        "parcela": "Parcelamento",
        "fatura": "Fatura cartão",
    }

    def _fill_vencimentos(self, rows: list[CalendarEvent]) -> None:
        tbl = self.tbl_venc
        if not rows:
            tbl.setRowCount(1)
            tbl.setItem(0, 0, QTableWidgetItem("—"))
            tbl.setItem(0, 1, QTableWidgetItem("—"))
            tbl.setItem(0, 2, QTableWidgetItem("Nada a vencer neste período"))
            tbl.setItem(0, 3, QTableWidgetItem("—"))
            return
        tbl.setRowCount(len(rows))
        for i, ev in enumerate(rows):
            tipo = self._VENC_TIPO.get(ev.tipo, ev.tipo)
            tbl.setItem(i, 0, QTableWidgetItem(format_date_br(ev.data)))
            tbl.setItem(i, 1, QTableWidgetItem(tipo))
            tbl.setItem(i, 2, QTableWidgetItem(ev.titulo))
            tbl.setItem(i, 3, QTableWidgetItem(format_currency(ev.valor)))
