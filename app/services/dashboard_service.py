"""Agregações para o dashboard."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from app.database.connection import transaction
from app.services import (
    calendar_service,
    card_invoices_service,
    cards_service,
    fixed_expenses_service,
    income_sources_service,
    investments_service,
)
from app.services.calendar_service import CalendarEvent
from app.utils.formatting import current_month


@dataclass
class DashboardData:
    mes_referencia: str
    total_gasto_mes: float = 0.0
    assinaturas_ativas_qtd: int = 0
    assinaturas_ativas_valor: float = 0.0
    parcelamentos_ativos_qtd: int = 0
    saldo_devedor_total: float = 0.0
    parcelas_mes_atual: float = 0.0
    fixos_pendentes_mes: float = 0.0
    fixos_restante_ano: float = 0.0
    fixos_ativos_qtd: int = 0
    previsto_mes: float = 0.0
    previsto_faturas: float = 0.0
    renda_mensal_total: float = 0.0
    margem_apos_previsto: float = 0.0
    margem_apos_gasto: float = 0.0
    gastos_por_conta: List[tuple[str, float]] = field(default_factory=list)
    gastos_por_forma: List[tuple[str, float]] = field(default_factory=list)
    proximos_vencimentos: List[CalendarEvent] = field(default_factory=list)
    total_investido: float = 0.0


def load(mes: str | None = None) -> DashboardData:
    mes = mes or current_month()
    data = DashboardData(mes_referencia=mes)

    with transaction() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(valor), 0) AS total FROM payments WHERE substr(data, 1, 7) = ?",
            (mes,),
        ).fetchone()
        data.total_gasto_mes = float(row["total"] or 0)

        row = conn.execute(
            """
            SELECT COUNT(*) AS qtd, COALESCE(SUM(valor_mensal), 0) AS total
              FROM subscriptions
             WHERE status = 'ativa'
               AND card_id IS NULL
            """
        ).fetchone()
        data.assinaturas_ativas_qtd = int(row["qtd"] or 0)
        data.assinaturas_ativas_valor = float(row["total"] or 0)

        row = conn.execute(
            "SELECT COUNT(*) AS qtd FROM installments WHERE status = 'ativo'"
        ).fetchone()
        data.parcelamentos_ativos_qtd = int(row["qtd"] or 0)

        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor_parcela * (total_parcelas - parcelas_pagas)), 0) AS saldo
              FROM installments WHERE status = 'ativo'
            """
        ).fetchone()
        data.saldo_devedor_total = float(row["saldo"] or 0)

        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor_parcela), 0) AS total
              FROM installments
             WHERE status = 'ativo'
               AND mes_referencia = ?
               AND cartao_id IS NULL
            """,
            (mes,),
        ).fetchone()
        data.parcelas_mes_atual = float(row["total"] or 0)

        data.fixos_pendentes_mes = fixed_expenses_service.sum_unpaid_for_month(mes)
        data.fixos_restante_ano = fixed_expenses_service.sum_unpaid_rest_of_calendar_year()
        data.fixos_ativos_qtd = fixed_expenses_service.count_active()

        previsto_faturas = 0.0
        for card in cards_service.list_all():
            if card.id is None:
                continue
            inv = card_invoices_service.get(card.id, mes)
            if inv is not None and inv.status == "paga":
                continue
            sug = card_invoices_service.suggested_total(card.id, mes)
            v = float(inv.valor_total) if inv is not None and inv.valor_total > 0 else sug
            if v <= 0:
                continue
            previsto_faturas += v
        data.previsto_faturas = round(previsto_faturas, 2)

        data.previsto_mes = (
            data.previsto_faturas
            + data.assinaturas_ativas_valor
            + data.parcelas_mes_atual
            + data.fixos_pendentes_mes
        )

        data.renda_mensal_total = income_sources_service.sum_active_monthly()
        data.margem_apos_previsto = data.renda_mensal_total - data.previsto_mes
        data.margem_apos_gasto = data.renda_mensal_total - data.total_gasto_mes

        rows = conn.execute(
            """
            SELECT CASE
                     WHEN p.cartao_id IS NOT NULL THEN 'Cartão · ' || COALESCE(c.nome, '?')
                     ELSE COALESCE(a.nome, p.conta, '(sem conta)')
                   END AS nome_origem,
                   COALESCE(SUM(p.valor), 0) AS total
              FROM payments p
              LEFT JOIN accounts a ON a.id = p.conta_id
              LEFT JOIN cards c ON c.id = p.cartao_id
             WHERE substr(p.data, 1, 7) = ?
             GROUP BY nome_origem
             ORDER BY total DESC
            """,
            (mes,),
        ).fetchall()
        data.gastos_por_conta = [(r["nome_origem"], float(r["total"])) for r in rows]

        rows = conn.execute(
            """
            SELECT forma_pagamento, COALESCE(SUM(valor), 0) AS total
              FROM payments
             WHERE substr(data, 1, 7) = ?
             GROUP BY forma_pagamento
             ORDER BY total DESC
            """,
            (mes,),
        ).fetchall()
        data.gastos_por_forma = [(r["forma_pagamento"], float(r["total"])) for r in rows]

    data.proximos_vencimentos = calendar_service.upcoming_payables(
        calendar_service.UPCOMING_HORIZON_DAYS
    )

    data.total_investido = investments_service.total_aplicado()

    return data
