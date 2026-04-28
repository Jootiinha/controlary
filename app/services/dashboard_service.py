"""Agregações para o dashboard."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import List, Optional

from app.database.connection import use
from app.repositories import dashboard_repo
from app.models.income_source import installment_month_applies
from app.services import (
    accounts_service,
    calendar_service,
    card_invoices_service,
    cards_service,
    fixed_expenses_service,
    income_sources_service,
    investments_service,
)
from app.services.calendar_service import CalendarEvent
from app.utils.formatting import current_month


def _parcelas_conta_pendentes_no_mes(conn, ano_mes: str) -> float:
    rows = conn.execute(
        """
        SELECT i.id, i.valor_parcela, i.mes_referencia, i.total_parcelas
          FROM installments i
         WHERE i.status = 'ativo'
           AND i.cartao_id IS NULL
        """
    ).fetchall()
    total = 0.0
    for r in rows:
        if not installment_month_applies(
            str(r["mes_referencia"]),
            int(r["total_parcelas"] or 0),
            ano_mes,
        ):
            continue
        paid = conn.execute(
            """
            SELECT 1 FROM installment_months im
             WHERE im.installment_id = ?
               AND im.ano_mes = ?
               AND im.status = 'pago'
            """,
            (int(r["id"]), ano_mes),
        ).fetchone()
        if paid:
            continue
        total += float(r["valor_parcela"] or 0)
    return total


@dataclass
class DashboardData:
    mes_referencia: str
    total_gasto_mes: float = 0.0
    # Parcela de assinaturas em conta no previsto do mês (cartão entra em previsto_faturas).
    assinaturas_ativas_qtd: int = 0
    assinaturas_ativas_valor: float = 0.0
    # KPI do card: todas as assinaturas ativas (alinha à página Assinaturas).
    assinaturas_kpi_qtd: int = 0
    assinaturas_kpi_valor_mensal: float = 0.0
    assinaturas_kpi_em_conta_qtd: int = 0
    assinaturas_kpi_no_cartao_qtd: int = 0
    parcelamentos_ativos_qtd: int = 0
    saldo_devedor_total: float = 0.0
    parcelas_mes_atual: float = 0.0
    fixos_pendentes_mes: float = 0.0
    fixos_restante_ano: float = 0.0
    fixos_ativos_qtd: int = 0
    previsto_mes: float = 0.0
    previsto_faturas: float = 0.0
    gastos_avulsos_mes: float = 0.0
    renda_mensal_total: float = 0.0
    margem_apos_previsto: float = 0.0
    margem_apos_gasto: float = 0.0
    gastos_por_conta: List[tuple[str, float]] = field(default_factory=list)
    gastos_por_forma: List[tuple[str, float]] = field(default_factory=list)
    proximos_vencimentos: List[CalendarEvent] = field(default_factory=list)
    total_investido: float = 0.0
    saldo_em_contas: float = 0.0
    saldo_projetado_fim_mes: float = 0.0


def cost_of_living(
    ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> float:
    """Comprometimento do mês (previsto): avulsos em conta, faturas de cartão (sem somar compras
    duas vezes), parcelas e assinaturas em conta pendentes na competência, fixos ativos ainda não
    pagos no mês. Inclui todos os pagamentos em conta do mês (tabela ``payments``), não exclui
    quem já tem espelho no livro-caixa — o ``previsto_breakdown`` é que evita duplicar com o
    livro para o card de previsto."""
    with use(conn) as c:
        avulsos_conta = dashboard_repo.sum_payments_conta_in_month(c, ano_mes)
        assinaturas_conta = dashboard_repo.sum_subscriptions_conta_pending_month(
            c, ano_mes
        )
        parcelas_conta = _parcelas_conta_pendentes_no_mes(c, ano_mes)

    fixos = fixed_expenses_service.sum_unpaid_for_month(ano_mes)

    with use(conn) as c:
        faturas_cartao = 0.0
        for cid in dashboard_repo.list_card_ids(c):
            inv = dashboard_repo.fetch_invoice_valor_status(c, cid, ano_mes)
            vt = float(inv["vt"]) if inv else 0.0
            st = str(inv["status"]) if inv else "aberta"
            if vt > 0 and st != "paga":
                faturas_cartao += vt
                continue
            v = card_invoices_service.suggested_total(cid, ano_mes)
            if v > 0:
                faturas_cartao += v

        total = (
            avulsos_conta
            + assinaturas_conta
            + parcelas_conta
            + fixos
            + faturas_cartao
        )
        return round(total, 2)


@dataclass(frozen=True)
class PrevistoMesBreakdown:
    previsto_faturas: float
    assinaturas_conta_valor: float
    parcelas_conta_mes: float
    fixos_pendentes_mes: float
    gastos_avulsos_mes: float

    def total(self) -> float:
        return round(
            self.previsto_faturas
            + self.assinaturas_conta_valor
            + self.parcelas_conta_mes
            + self.fixos_pendentes_mes
            + self.gastos_avulsos_mes,
            2,
        )


def previsto_breakdown_for(
    ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> PrevistoMesBreakdown:
    previsto_faturas = 0.0
    for card in cards_service.list_all():
        if card.id is None:
            continue
        inv = card_invoices_service.get(card.id, ano_mes)
        if inv is not None and inv.status == "paga":
            continue
        sug = card_invoices_service.suggested_total(card.id, ano_mes)
        v = float(inv.valor_total) if inv is not None and inv.valor_total > 0 else sug
        if v <= 0:
            continue
        previsto_faturas += v

    with use(conn) as c:
        assinaturas_conta = dashboard_repo.sum_subscriptions_conta_pending_month(
            c, ano_mes
        )
        parcelas_conta = _parcelas_conta_pendentes_no_mes(c, ano_mes)
        avulsos = dashboard_repo.sum_payments_conta_month_without_ledger_mirror(
            c, ano_mes
        )

    fixos_pend = fixed_expenses_service.sum_unpaid_for_month(ano_mes)

    return PrevistoMesBreakdown(
        previsto_faturas=previsto_faturas,
        assinaturas_conta_valor=assinaturas_conta,
        parcelas_conta_mes=parcelas_conta,
        fixos_pendentes_mes=fixos_pend,
        gastos_avulsos_mes=avulsos,
    )


def previsto_mes_for(
    ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> float:
    return previsto_breakdown_for(ano_mes, conn=conn).total()


def load(
    mes: str | None = None, conn: Optional[sqlite3.Connection] = None
) -> DashboardData:
    mes = mes or current_month()
    data = DashboardData(mes_referencia=mes)

    with use(conn) as c:
        deb = accounts_service.sum_debits_in_month(mes, conn=c)
        data.total_gasto_mes = round(-deb, 2) if deb < 0 else round(deb, 2)

        data.assinaturas_ativas_qtd = dashboard_repo.count_subscriptions_ativas_conta(
            c
        )

        row = dashboard_repo.row_subscriptions_kpi(c)
        data.assinaturas_kpi_qtd = int(row["qtd"] or 0)
        data.assinaturas_kpi_valor_mensal = float(row["total"] or 0)
        data.assinaturas_kpi_em_conta_qtd = int(row["em_conta"] or 0)
        data.assinaturas_kpi_no_cartao_qtd = int(row["no_cartao"] or 0)

        data.parcelamentos_ativos_qtd = dashboard_repo.count_installments_ativos(c)
        data.saldo_devedor_total = dashboard_repo.sum_saldo_devedor_parcelas(c)

        data.fixos_restante_ano = fixed_expenses_service.sum_unpaid_rest_of_calendar_year()
        data.fixos_ativos_qtd = fixed_expenses_service.count_active()

    bd = previsto_breakdown_for(mes, conn=conn)
    data.previsto_faturas = round(bd.previsto_faturas, 2)
    data.parcelas_mes_atual = round(bd.parcelas_conta_mes, 2)
    data.fixos_pendentes_mes = round(bd.fixos_pendentes_mes, 2)
    data.gastos_avulsos_mes = round(bd.gastos_avulsos_mes, 2)
    data.assinaturas_ativas_valor = round(bd.assinaturas_conta_valor, 2)
    data.previsto_mes = bd.total()

    data.renda_mensal_total = income_sources_service.sum_for_month(mes)
    data.margem_apos_previsto = round(
        data.renda_mensal_total - data.previsto_mes, 2
    )
    data.margem_apos_gasto = round(
        data.renda_mensal_total - data.total_gasto_mes, 2
    )

    with use(conn) as c:
        rows = dashboard_repo.gastos_por_conta_rows(c, mes)
        data.gastos_por_conta = [(r["nome_origem"], float(r["total"])) for r in rows]
        rows = dashboard_repo.gastos_por_forma_rows(c, mes)
        data.gastos_por_forma = [(r["forma_pagamento"], float(r["total"])) for r in rows]

    data.proximos_vencimentos = calendar_service.upcoming_payables(
        calendar_service.UPCOMING_HORIZON_DAYS
    )

    data.total_investido = investments_service.total_aplicado()

    data.saldo_em_contas = accounts_service.sum_balances()
    if mes == current_month():
        renda_pendente = income_sources_service.sum_expected_receipts_rest_of_month(mes)
        data.saldo_projetado_fim_mes = round(
            data.saldo_em_contas + renda_pendente - data.previsto_mes,
            2,
        )
    else:
        # Saldo em contas é até hoje; misturar com previsto/renda de outro mês distorce o KPI.
        data.saldo_projetado_fim_mes = 0.0

    return data
