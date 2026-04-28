"""Tela inicial com indicadores agregados."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.charts import monthly_expenses, month_compare
from app.services import calendar_service, dashboard_service, investments_service
from app.services.calendar_service import CalendarEvent
from app.services.dashboard_service import DashboardData
from app.ui.ui_wait import wait_cursor
from app.ui.widgets.card import KpiCard
from app.ui.widgets.chart_canvas import ChartCanvas
from app.ui.widgets.readonly_table import ReadOnlyTable
from app.utils.formatting import current_month, format_currency, format_date_br


_CARD_MIN_W = 168
_KPI_COLS = 4

_VENC_TIPO_MAP = {
    "assinatura": "Assinatura",
    "fixo": "Gasto fixo",
    "parcela": "Parcelamento",
    "fatura": "Fatura cartão",
}


class DashboardView(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.lbl_title = QLabel("Dashboard")
        self.lbl_title.setObjectName("PageTitle")
        self.lbl_subtitle = QLabel(
            "Saldo, compromissos e análises do mês (detalhes abaixo podem ser recolhidos)."
        )
        self.lbl_subtitle.setObjectName("PageSubtitle")

        self._attention_strip = QWidget()
        self._attention_lay = QHBoxLayout(self._attention_strip)
        self._attention_lay.setContentsMargins(0, 0, 0, 0)
        self._attention_lay.setSpacing(10)
        self._attention_strip.hide()

        self._hero_saldo = KpiCard(
            "Saldo em contas",
            "-",
            subtitle="Saldo inicial + movimentações até hoje",
            variant="hero",
            delta_text="",
        )
        self._hero_saldo.setToolTip(
            "Soma dos saldos atuais de todas as contas cadastradas."
        )
        self.card_saldo_fim_mes = KpiCard(
            "Saldo fim do mês (est.)",
            "—",
            subtitle="Mês corrente",
            compact=True,
        )
        self.card_saldo_fim_mes.setToolTip(
            "No mês corrente: saldos em conta hoje, mais renda ainda não marcada como "
            "recebida, menos o gasto previsto (faturas em aberto, assinaturas e parcelas "
            "em conta não pagas, fixos pendentes e lançamentos em conta sem débito no "
            "livro-caixa). Evita dupla contagem com o que já entrou no saldo."
        )

        self._pb_renda_vs_previsto = QProgressBar()
        self._pb_renda_vs_previsto.setRange(0, 100)
        self._pb_renda_vs_previsto.setFormat("Gasto sobre renda (previsto): %p%%")
        self._pb_renda_vs_previsto.setTextVisible(True)
        self._lbl_mes_glance = QLabel("Mês em um olhar")
        self._lbl_mes_glance.setObjectName("PageSubtitle")
        mes_glance = QWidget()
        mgl = QVBoxLayout(mes_glance)
        mgl.setContentsMargins(0, 0, 0, 0)
        mgl.setSpacing(6)
        mgl.addWidget(self._lbl_mes_glance)
        mgl.addWidget(self._pb_renda_vs_previsto, 1)

        hero_row = QWidget()
        hero_lay = QHBoxLayout(hero_row)
        hero_lay.setContentsMargins(0, 0, 0, 0)
        hero_lay.setSpacing(16)
        hero_lay.addWidget(self._hero_saldo, 2)
        right_col = QWidget()
        rcl = QVBoxLayout(right_col)
        rcl.setContentsMargins(0, 0, 0, 0)
        rcl.setSpacing(12)
        rcl.addWidget(self.card_saldo_fim_mes)
        rcl.addWidget(mes_glance, 1)
        hero_lay.addWidget(right_col, 1)

        self._dt_mes = QDateEdit()
        self._dt_mes.setDisplayFormat("MM/yyyy")
        self._dt_mes.setCalendarPopup(True)
        self._dt_mes.setDate(QDate.currentDate())
        self._dt_mes.dateChanged.connect(lambda: self.reload())
        row_mes = QHBoxLayout()
        row_mes.addWidget(QLabel("Competência (gráficos e tabelas detalhadas):"))
        row_mes.addWidget(self._dt_mes)
        row_mes.addStretch()
        self._mes_ref_row = QWidget()
        self._mes_ref_row.setLayout(row_mes)

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
            "Assinaturas",
            subtitle="Total mensal (ativas)",
            compact=True,
        )

        flux_grid = QGridLayout()
        flux_grid.setContentsMargins(0, 0, 0, 0)
        flux_grid.setHorizontalSpacing(12)
        flux_grid.setVerticalSpacing(12)
        for c in range(_KPI_COLS):
            flux_grid.setColumnMinimumWidth(c, _CARD_MIN_W)
            flux_grid.setColumnStretch(c, 1)
        align = Qt.AlignmentFlag.AlignTop
        flux_grid.addWidget(self.card_renda, 0, 0, 1, 1, align)
        flux_grid.addWidget(self.card_gasto_previsto_mes, 0, 1, 1, 2, align)
        flux_grid.addWidget(self.card_margem_previsto, 0, 3, 1, 1, align)

        comp_grid = QGridLayout()
        comp_grid.setContentsMargins(0, 0, 0, 0)
        comp_grid.setHorizontalSpacing(12)
        comp_grid.setVerticalSpacing(12)
        for c in range(_KPI_COLS):
            comp_grid.setColumnMinimumWidth(c, _CARD_MIN_W)
            comp_grid.setColumnStretch(c, 1)
        comp_grid.addWidget(self.card_invest, 0, 0, 1, 1, align)
        comp_grid.addWidget(self.card_fixos_mes, 0, 1, 1, 1, align)
        comp_grid.addWidget(self.card_assinaturas, 0, 2, 1, 2, align)

        grp_fluxo = QGroupBox("Fluxo e patrimônio (resumo)")
        grp_fluxo.setLayout(flux_grid)
        grp_comp = QGroupBox("Compromissos recorrentes")
        grp_comp.setLayout(comp_grid)

        kpi_outer = QVBoxLayout()
        kpi_outer.setContentsMargins(0, 0, 0, 0)
        kpi_outer.setSpacing(12)
        kpi_outer.addWidget(grp_fluxo)
        kpi_outer.addWidget(grp_comp)

        kpi_wrap = QWidget()
        kpi_wrap.setLayout(kpi_outer)
        kpi_wrap.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.tbl_compromissos = ReadOnlyTable(
            [
                "Data",
                "Direção",
                "Tipo",
                "Descrição",
                "Valor",
            ],
            min_height=200,
            size_policy=(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            ),
        )
        comp_wrap = self._titled(
            f"Compromissos próximos (até {calendar_service.UPCOMING_HORIZON_DAYS} dias)",
            self.tbl_compromissos,
        )
        comp_wrap.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

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
        bottom_section.setMinimumHeight(400)
        bottom_col = QVBoxLayout(bottom_section)
        bottom_col.setContentsMargins(0, 0, 0, 0)
        bottom_col.setSpacing(16)

        self._grp_detalhes = QGroupBox("Análises detalhadas (competência)")
        self._grp_detalhes.setCheckable(True)
        self._grp_detalhes.setChecked(False)
        det_inner = QVBoxLayout(self._grp_detalhes)
        det_inner.setContentsMargins(12, 20, 12, 12)
        det_inner.setSpacing(14)
        det_inner.addWidget(self._mes_ref_row)
        det_inner.addWidget(chart_box, 1)
        det_inner.addWidget(tables_row, 0)
        bottom_col.addWidget(self._grp_detalhes, 1)

        content = QWidget()
        content.setObjectName("DashboardContent")
        inner = QVBoxLayout(content)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(16)
        inner.addWidget(self.lbl_title)
        inner.addWidget(self.lbl_subtitle)
        inner.addWidget(self._attention_strip, 0)
        inner.addWidget(hero_row, 0)
        inner.addWidget(kpi_wrap, 0)
        inner.addWidget(comp_wrap, 0)
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

    def _ano_mes(self) -> str:
        d = self._dt_mes.date()
        return f"{d.year():04d}-{d.month():02d}"

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
        with wait_cursor():
            self._reload_impl()

    def _reload_impl(self) -> None:
        ym = self._ano_mes()
        data = dashboard_service.load(mes=ym)

        self.card_renda.set_value(format_currency(data.renda_mensal_total))
        self.card_gasto_previsto_mes.set_value(format_currency(data.previsto_mes))
        self.card_gasto_previsto_mes.set_subtitle(
            f"Saídas no livro-caixa no mês: {format_currency(data.total_gasto_mes)}"
        )
        self.card_gasto_previsto_mes.setToolTip(
            "Previsto estruturado-first: faturas de cartão em aberto (valor ou sugerido), "
            "assinaturas em conta ainda não pagas no mês, parcelas em conta pendentes, "
            "fixos pendentes e apenas lançamentos em conta sem débito correspondente "
            "no livro-caixa (evita duplicar com o que já saiu do saldo)."
        )
        self.card_margem_previsto.set_value(format_currency(data.margem_apos_previsto))

        self._hero_saldo.set_value(format_currency(data.saldo_em_contas))
        if data.mes_referencia == current_month():
            proj = data.saldo_projetado_fim_mes
            delta = proj - data.saldo_em_contas
            sign = "+" if delta >= 0 else ""
            self._hero_saldo.set_delta(
                f"Projeção fim do mês: {format_currency(proj)} ({sign}{format_currency(delta)})"
            )
            self.card_saldo_fim_mes.set_value(format_currency(data.saldo_projetado_fim_mes))
            self.card_saldo_fim_mes.setToolTip(
                "No mês corrente: saldos em conta hoje, mais renda ainda não marcada como "
                "recebida, menos o gasto previsto (faturas em aberto, assinaturas e parcelas "
                "em conta não pagas, fixos pendentes e lançamentos em conta sem débito no "
                "livro-caixa). Evita dupla contagem com o que já entrou no saldo."
            )
        else:
            self._hero_saldo.set_delta("")
            self.card_saldo_fim_mes.set_value("—")
            self.card_saldo_fim_mes.setToolTip(
                "Projeção de saldo ao fim do mês só está disponível para o mês de referência "
                "corrente (saldo em contas reflete a data de hoje)."
            )

        if data.renda_mensal_total > 0.005:
            pct = min(
                100,
                int(round(100.0 * data.previsto_mes / data.renda_mensal_total)),
            )
            self._pb_renda_vs_previsto.setValue(pct)
        else:
            self._pb_renda_vs_previsto.setValue(0)

        entradas = calendar_service.upcoming_receivables(
            calendar_service.UPCOMING_HORIZON_DAYS
        )
        self._refresh_attention(data.proximos_vencimentos, data)
        self._fill_compromissos_list(data.proximos_vencimentos, entradas)

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
            format_currency(data.assinaturas_kpi_valor_mensal)
        )
        self.card_assinaturas.set_subtitle(
            f"{data.assinaturas_kpi_qtd} ativas "
            f"({data.assinaturas_kpi_em_conta_qtd} em conta · "
            f"{data.assinaturas_kpi_no_cartao_qtd} no cartão)"
        )
        self.card_assinaturas.setToolTip(
            "Soma do valor mensal de todas as assinaturas com status ativa. "
            "No gasto previsto do mês, as debitadas em conta entram como linha de "
            "assinaturas; as ligadas a cartão entram na fatura prevista do cartão."
        )

        self._fill_table(data.gastos_por_conta, self.tbl_contas)
        self._fill_table(data.gastos_por_forma, self.tbl_formas)

        self.chart_month_compare.set_renderer(
            lambda ax, m=ym: month_compare.plot(ax, ref=m)
        )
        self.chart_month_compare.refresh()
        self.chart_cost_12m.set_renderer(
            lambda ax, m=ym: monthly_expenses.plot(ax, end_ym=m)
        )
        self.chart_cost_12m.refresh()

    def _refresh_attention(
        self, venc: list[CalendarEvent], data: DashboardData
    ) -> None:
        while self._attention_lay.count():
            item = self._attention_lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        today = date.today()
        n_over = sum(1 for ev in venc if ev.data < today and not ev.pago)
        if n_over > 0:
            b = QPushButton(
                f"{n_over} compromisso(s) atrasado(s) — confira na tabela de compromissos"
            )
            b.setFlat(True)
            self._attention_lay.addWidget(b)
            self._attention_strip.show()
        elif data.fixos_pendentes_mes > 0.005:
            lbl = QLabel(
                f"Fixos pendentes no mês: {format_currency(data.fixos_pendentes_mes)}"
            )
            lbl.setObjectName("PageSubtitle")
            self._attention_lay.addWidget(lbl)
            self._attention_strip.show()
        else:
            self._attention_strip.hide()

    def _fill_compromissos_list(
        self, venc: list[CalendarEvent], entradas: list[CalendarEvent]
    ) -> None:
        combined: list[tuple[CalendarEvent, str]] = []
        for ev in venc:
            combined.append((ev, "Saída"))
        for ev in entradas:
            combined.append((ev, "Entrada"))
        combined.sort(key=lambda t: (t[0].data, t[1], t[0].titulo.casefold()))
        tbl = self.tbl_compromissos
        if not combined:
            tbl.set_rows(
                [],
                empty_message="Nada neste período — cadastre despesas e rendas para ver o calendário.",
            )
            return
        tipo_lbl = {**_VENC_TIPO_MAP, "renda": "Renda", "pagamento": "Pagamento"}
        rows: list[list[str]] = []
        sk: list[list[object]] = []
        for ev, direc in combined:
            tipo = tipo_lbl.get(ev.tipo, ev.tipo)
            rows.append([
                format_date_br(ev.data),
                direc,
                tipo,
                ev.titulo,
                format_currency(ev.valor),
            ])
            sk.append([
                ev.data,
                direc.casefold(),
                str(tipo).casefold(),
                ev.titulo.casefold(),
                float(ev.valor),
            ])
        tbl.set_rows(rows, sort_keys=sk)

    def _fill_table(
        self, rows: list[tuple[str, float]], tbl: ReadOnlyTable
    ) -> None:
        if not rows:
            tbl.set_rows([], empty_message="Sem lançamentos no mês")
            return
        tbl.set_rows(
            [[label, format_currency(value)] for label, value in rows],
            sort_keys=[
                [label.casefold(), float(value)] for label, value in rows
            ],
        )

