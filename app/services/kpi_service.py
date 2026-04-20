"""KPIs canônicos por competência (mês YYYY-MM)."""
from __future__ import annotations

from dataclasses import dataclass

from app.services import dashboard_service, expense_totals_service, income_sources_service
from app.utils.formatting import current_month


@dataclass(frozen=True)
class MonthKpis:
    ano_mes: str
    renda_esperada: float
    renda_recebida: float
    renda_pendente: float
    despesa_prevista: float
    despesa_realizada: float
    margem_previsto: float
    saldo_projetado_fim_mes: float


def income_pending_for_month(ano_mes: str) -> float:
    """Valor de renda ainda não creditado no mês (competência)."""
    cur = current_month()
    if ano_mes == cur:
        return income_sources_service.sum_expected_receipts_rest_of_month(ano_mes)
    esp = income_sources_service.sum_for_month(ano_mes)
    rec = income_sources_service.sum_received_for_month(ano_mes)
    return round(max(esp - rec, 0.0), 2)


def for_month(ano_mes: str | None = None) -> MonthKpis:
    ano_mes = ano_mes or current_month()
    data = dashboard_service.load(mes=ano_mes)
    rec = income_sources_service.sum_received_for_month(ano_mes)
    pend = income_pending_for_month(ano_mes)
    desp_real = expense_totals_service.total_despesa_mes(ano_mes)
    return MonthKpis(
        ano_mes=ano_mes,
        renda_esperada=data.renda_mensal_total,
        renda_recebida=rec,
        renda_pendente=pend,
        despesa_prevista=data.previsto_mes,
        despesa_realizada=desp_real,
        margem_previsto=data.margem_apos_previsto,
        saldo_projetado_fim_mes=data.saldo_projetado_fim_mes,
    )
