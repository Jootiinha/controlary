"""paid_remaining usa valor_efetivo e ignora inativas no parâmetro."""
from __future__ import annotations

from pathlib import Path

from app.database.connection import transaction
from app.models.income_source import IncomeSource
from app.services import income_months_service, income_sources_service


def test_paid_remaining_valor_efetivo_and_inactive(test_db_path: Path) -> None:
    src = IncomeSource(
        id=None,
        nome="Projeto",
        valor_mensal=100.0,
        ativo=True,
        dia_recebimento=5,
        tipo="avulsa",
        mes_referencia="2026-06",
    )
    sid = income_sources_service.create(src)
    income_months_service.set_month_status(sid, "2026-06", True, valor_efetivo=80.0)
    s = income_sources_service.get(sid)
    assert s is not None
    rec, rem = income_sources_service.paid_remaining(s)
    assert rec == 80.0
    assert rem == 20.0

    income_sources_service.update(
        IncomeSource(
            id=sid,
            nome=s.nome,
            valor_mensal=999.0,
            ativo=False,
            dia_recebimento=s.dia_recebimento,
            tipo="avulsa",
            mes_referencia="2026-06",
        )
    )
    s2 = income_sources_service.get(sid)
    assert s2 is not None
    r2, rem2 = income_sources_service.paid_remaining(s2, include_inactive=False)
    assert r2 == 0.0 and rem2 == 0.0


def test_is_fully_received_avulsa(test_db_path: Path) -> None:
    src = IncomeSource(
        id=None,
        nome="Serviço",
        valor_mensal=250.0,
        ativo=True,
        dia_recebimento=5,
        tipo="avulsa",
        mes_referencia="2026-08",
    )
    sid = income_sources_service.create(src)
    s0 = income_sources_service.get(sid)
    assert s0 is not None
    assert not income_sources_service.is_fully_received(s0)
    income_months_service.set_month_status(
        sid, "2026-08", recebido=True, valor_efetivo=250.0
    )
    s = income_sources_service.get(sid)
    assert s is not None
    assert income_sources_service.is_fully_received(s)
