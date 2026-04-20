"""Rendas avulsas podem repetir o nome (índice único só para não-avulsas)."""
from __future__ import annotations

from pathlib import Path

from app.models.income_source import IncomeSource
from app.services import income_sources_service


def test_two_avulsas_same_name_different_months(test_db_path: Path) -> None:
    a1 = IncomeSource(
        id=None,
        nome="Bônus",
        valor_mensal=100.0,
        ativo=True,
        dia_recebimento=10,
        tipo="avulsa",
        mes_referencia="2026-04",
    )
    a2 = IncomeSource(
        id=None,
        nome="Bônus",
        valor_mensal=200.0,
        ativo=True,
        dia_recebimento=10,
        tipo="avulsa",
        mes_referencia="2026-05",
    )
    i1 = income_sources_service.create(a1)
    i2 = income_sources_service.create(a2)
    assert i1 != i2
    assert income_sources_service.get(i1) is not None
    assert income_sources_service.get(i2) is not None
