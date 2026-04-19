"""Agregações para o dashboard."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from app.database.connection import transaction
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


def cost_of_living(ano_mes: str) -> float:
    """Custo total do mês: avulsos em conta, faturas de cartão (sem somar compras duas vezes),
    parcelas em conta, assinaturas em conta e gastos fixos ativos."""
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor), 0) AS t
              FROM payments
             WHERE substr(data, 1, 7) = ?
               AND cartao_id IS NULL
            """,
            (ano_mes,),
        ).fetchone()
        avulsos_conta = float(row["t"] or 0)

        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor_mensal), 0) AS t
              FROM subscriptions
             WHERE status = 'ativa'
               AND card_id IS NULL
            """
        ).fetchone()
        assinaturas_conta = float(row["t"] or 0)

        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor_parcela), 0) AS t
              FROM installments
             WHERE status = 'ativo'
               AND cartao_id IS NULL
               AND mes_referencia = ?
            """,
            (ano_mes,),
        ).fetchone()
        parcelas_conta = float(row["t"] or 0)

        row = conn.execute(
            "SELECT COALESCE(SUM(valor_mensal), 0) AS t FROM fixed_expenses WHERE ativo = 1"
        ).fetchone()
        fixos = float(row["t"] or 0)

        faturas_cartao = 0.0
        for cr in conn.execute("SELECT id FROM cards").fetchall():
            cid = int(cr["id"])
            inv = conn.execute(
                """
                SELECT COALESCE(valor_total, 0) AS vt
                  FROM card_invoices
                 WHERE cartao_id = ? AND ano_mes = ?
                """,
                (cid, ano_mes),
            ).fetchone()
            vt = float(inv["vt"]) if inv else 0.0
            if vt > 0:
                faturas_cartao += vt
                continue
            r1 = conn.execute(
                """
                SELECT COALESCE(SUM(valor_parcela), 0) AS t
                  FROM installments
                 WHERE status = 'ativo'
                   AND cartao_id = ?
                   AND mes_referencia = ?
                """,
                (cid, ano_mes),
            ).fetchone()
            r2 = conn.execute(
                """
                SELECT COALESCE(SUM(valor_mensal), 0) AS t
                  FROM subscriptions
                 WHERE status = 'ativa'
                   AND card_id = ?
                """,
                (cid,),
            ).fetchone()
            r3 = conn.execute(
                """
                SELECT COALESCE(SUM(valor), 0) AS t
                  FROM payments
                 WHERE cartao_id = ?
                   AND substr(data, 1, 7) = ?
                """,
                (cid, ano_mes),
            ).fetchone()
            v = float(r1["t"] or 0) + float(r2["t"] or 0) + float(r3["t"] or 0)
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


def previsto_breakdown_for(ano_mes: str) -> PrevistoMesBreakdown:
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

    with transaction() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor_mensal), 0) AS total
              FROM subscriptions
             WHERE status = 'ativa'
               AND card_id IS NULL
            """
        ).fetchone()
        assinaturas_conta = float(row["total"] or 0)

        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor_parcela), 0) AS total
              FROM installments
             WHERE status = 'ativo'
               AND cartao_id IS NULL
               AND mes_referencia = ?
            """,
            (ano_mes,),
        ).fetchone()
        parcelas_conta = float(row["total"] or 0)

        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor), 0) AS total
              FROM payments
             WHERE substr(data, 1, 7) = ?
               AND cartao_id IS NULL
            """,
            (ano_mes,),
        ).fetchone()
        avulsos = float(row["total"] or 0)

    fixos_pend = fixed_expenses_service.sum_unpaid_for_month(ano_mes)

    return PrevistoMesBreakdown(
        previsto_faturas=previsto_faturas,
        assinaturas_conta_valor=assinaturas_conta,
        parcelas_conta_mes=parcelas_conta,
        fixos_pendentes_mes=fixos_pend,
        gastos_avulsos_mes=avulsos,
    )


def previsto_mes_for(ano_mes: str) -> float:
    return previsto_breakdown_for(ano_mes).total()


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
            SELECT COUNT(*) AS qtd
              FROM subscriptions
             WHERE status = 'ativa'
               AND card_id IS NULL
            """
        ).fetchone()
        data.assinaturas_ativas_qtd = int(row["qtd"] or 0)

        row = conn.execute(
            """
            SELECT COUNT(*) AS qtd,
                   COALESCE(SUM(valor_mensal), 0) AS total,
                   COALESCE(SUM(CASE WHEN card_id IS NULL THEN 1 ELSE 0 END), 0) AS em_conta,
                   COALESCE(SUM(CASE WHEN card_id IS NOT NULL THEN 1 ELSE 0 END), 0) AS no_cartao
              FROM subscriptions
             WHERE status = 'ativa'
            """
        ).fetchone()
        data.assinaturas_kpi_qtd = int(row["qtd"] or 0)
        data.assinaturas_kpi_valor_mensal = float(row["total"] or 0)
        data.assinaturas_kpi_em_conta_qtd = int(row["em_conta"] or 0)
        data.assinaturas_kpi_no_cartao_qtd = int(row["no_cartao"] or 0)

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

        data.fixos_restante_ano = fixed_expenses_service.sum_unpaid_rest_of_calendar_year()
        data.fixos_ativos_qtd = fixed_expenses_service.count_active()

    bd = previsto_breakdown_for(mes)
    data.previsto_faturas = round(bd.previsto_faturas, 2)
    data.parcelas_mes_atual = bd.parcelas_conta_mes
    data.fixos_pendentes_mes = bd.fixos_pendentes_mes
    data.gastos_avulsos_mes = round(bd.gastos_avulsos_mes, 2)
    data.assinaturas_ativas_valor = bd.assinaturas_conta_valor
    data.previsto_mes = bd.total()

    data.renda_mensal_total = income_sources_service.sum_for_month(mes)
    data.margem_apos_previsto = data.renda_mensal_total - data.previsto_mes
    data.margem_apos_gasto = data.renda_mensal_total - data.total_gasto_mes

    with transaction() as conn:
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

    data.saldo_em_contas = accounts_service.sum_balances()
    data.saldo_projetado_fim_mes = round(
        data.renda_mensal_total + data.saldo_em_contas - data.previsto_mes,
        2,
    )

    return data
