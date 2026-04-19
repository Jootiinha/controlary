"""Tela inicial com indicadores agregados."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.charts import monthly_expenses, month_compare
from app.services import calendar_service, dashboard_service, investments_service
from app.services.calendar_service import CalendarEvent
from app.ui.widgets.card import KpiCard
from app.ui.widgets.chart_canvas import ChartCanvas
from app.ui.widgets.readonly_table import ReadOnlyTable
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
        self.card_gasto_previsto_mes = KpiCard(
            "Gasto previsto no mês",
            subtitle="Já lançado em pagamentos: —",
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

        self.card_saldo_contas = KpiCard(
            "Saldo em contas",
            subtitle="Saldo inicial + movimentações até hoje",
            compact=True,
        )
        self.card_saldo_fim_mes = KpiCard(
            "Saldo fim do mês (est.)",
            subtitle="Renda mensal + saldos em contas − gasto previsto no mês",
            compact=True,
        )
        self.card_saldo_fim_mes.setToolTip(
            "Estimativa: soma da renda mensal (fontes ativas no mês) com os saldos "
            "atuais em conta corrente, menos o gasto previsto do mês (mesmo total do "
            "card «Gasto previsto no mês»)."
        )

        kpi_grid = QGridLayout()
        kpi_grid.setContentsMargins(0, 0, 0, 0)
        kpi_grid.setHorizontalSpacing(12)
        kpi_grid.setVerticalSpacing(12)
        for c in range(_KPI_COLS):
            kpi_grid.setColumnMinimumWidth(c, _CARD_MIN_W)
            kpi_grid.setColumnStretch(c, 1)
        align = Qt.AlignmentFlag.AlignTop
        kpi_grid.addWidget(self.card_renda, 0, 0, 1, 1, align)
        kpi_grid.addWidget(self.card_gasto_previsto_mes, 0, 1, 1, 2, align)
        kpi_grid.addWidget(self.card_margem_previsto, 0, 3, 1, 1, align)
        kpi_grid.addWidget(self.card_invest, 1, 0, 1, 1, align)
        kpi_grid.addWidget(self.card_fixos_mes, 1, 1, 1, 1, align)
        kpi_grid.addWidget(self.card_assinaturas, 1, 2, 1, 2, align)
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
        self.tbl_venc = ReadOnlyTable(
            ["Data", "Tipo", "Descrição", "Valor"],
            fixed_height=160,
            size_policy=(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            ),
        )

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

        self.chart_month_compare = ChartCanvas(
            month_compare.plot,
            width=8.0,
            height=2.6,
            dpi=100,
        )
        self.chart_month_compare.setMinimumHeight(220)
        self.chart_month_compare.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.chart_cost_12m = ChartCanvas(
            monthly_expenses.plot,
            width=8.0,
            height=3.6,
            dpi=100,
        )
        self.chart_cost_12m.setMinimumHeight(320)
        self.chart_cost_12m.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        chart_box = QWidget()
        chart_lay = QVBoxLayout(chart_box)
        chart_lay.setContentsMargins(0, 0, 0, 0)
        chart_lay.setSpacing(12)
        chart_lay.addWidget(self.chart_month_compare, 0)
        chart_lay.addWidget(self.chart_cost_12m, 1)

        self.tbl_contas = ReadOnlyTable(
            ["Conta", "Total do mês"],
            min_height=220,
            size_policy=(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
        )
        self.tbl_formas = ReadOnlyTable(
            ["Forma de pagamento", "Total do mês"],
            min_height=220,
            size_policy=(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
        )

        tables_row = QWidget()
        tables_row.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        tables_row_lay = QHBoxLayout(tables_row)
        tables_row_lay.setContentsMargins(0, 0, 0, 0)
        tables_row_lay.setSpacing(14)
        tables_row_lay.addWidget(self._titled("Gastos por conta", self.tbl_contas), 1)
        tables_row_lay.addWidget(
            self._titled("Gastos por forma de pagamento", self.tbl_formas), 1
        )

        bottom_section = QWidget()
        bottom_section.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        bottom_section.setMinimumHeight(620)
        bottom_col = QVBoxLayout(bottom_section)
        bottom_col.setContentsMargins(0, 0, 0, 0)
        bottom_col.setSpacing(14)
        bottom_col.addWidget(chart_box, 1)
        bottom_col.addWidget(tables_row, 0)

        content = QWidget()
        content.setObjectName("DashboardContent")
        inner = QVBoxLayout(content)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(14)
        inner.addWidget(self.lbl_title)
        inner.addWidget(self.lbl_subtitle)
        inner.addWidget(kpi_wrap, 0)
        inner.addWidget(venc_wrap, 0)
        inner.addWidget(bottom_section, 1)

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
        self.card_gasto_previsto_mes.set_value(format_currency(data.previsto_mes))
        self.card_gasto_previsto_mes.set_subtitle(
            f"Já lançado em pagamentos: {format_currency(data.total_gasto_mes)}"
        )
        self.card_gasto_previsto_mes.setToolTip(
            "Total previsto para o mês: faturas de cartão em aberto (valor registrado "
            "ou sugerido), assinaturas em conta, parcelas sem cartão no mês, fixos "
            "pendentes e lançamentos avulsos em conta (pagamentos sem cartão). "
            "O subtítulo é a soma já lançada em Pagamentos (todos os meios). "
            "Se o mesmo gasto estiver como assinatura/fixo e também em Pagamentos, "
            "pode haver sobreposição no previsto."
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

        self._fill_table(data.gastos_por_conta, self.tbl_contas)
        self._fill_table(data.gastos_por_forma, self.tbl_formas)
        self._fill_vencimentos(data.proximos_vencimentos)

        self.chart_month_compare.refresh()
        self.chart_cost_12m.refresh()

    def _fill_table(
        self, rows: list[tuple[str, float]], tbl: ReadOnlyTable
    ) -> None:
        if not rows:
            tbl.set_rows([], empty_message="Sem lançamentos no mês")
            return
        tbl.set_rows([[label, format_currency(value)] for label, value in rows])

    _VENC_TIPO = {
        "assinatura": "Assinatura",
        "fixo": "Gasto fixo",
        "parcela": "Parcelamento",
        "fatura": "Fatura cartão",
    }

    def _fill_vencimentos(self, rows: list[CalendarEvent]) -> None:
        tbl = self.tbl_venc
        if not rows:
            tbl.set_rows(
                [],
                empty_row=["—", "—", "Nada a vencer neste período", "—"],
            )
            return
        tbl.set_rows(
            [
                [
                    format_date_br(ev.data),
                    self._VENC_TIPO.get(ev.tipo, ev.tipo),
                    ev.titulo,
                    format_currency(ev.valor),
                ]
                for ev in rows
            ]
        )
