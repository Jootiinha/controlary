"""Rendas avulsas podem repetir o nome (índice único só para não-avulsas)."""
from __future__ import annotations

from pathlib import Path

import pytest

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


def test_two_avulsas_same_name_same_month_blocked_by_default(test_db_path: Path) -> None:
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
        mes_referencia="2026-04",
    )
    income_sources_service.create(a1)
    with pytest.raises(income_sources_service.DuplicateAvulsaIncomeError):
        income_sources_service.create(a2)
    i2 = income_sources_service.create(a2, allow_duplicate_avulsa=True)
    assert i2 > 0


def test_two_avulsas_same_name_same_month_case_insensitive(test_db_path: Path) -> None:
    income_sources_service.create(
        IncomeSource(
            id=None,
            nome="Extra",
            valor_mensal=10.0,
            ativo=True,
            dia_recebimento=1,
            tipo="avulsa",
            mes_referencia="2026-06",
        )
    )
    with pytest.raises(income_sources_service.DuplicateAvulsaIncomeError):
        income_sources_service.create(
            IncomeSource(
                id=None,
                nome="extra",
                valor_mensal=20.0,
                ativo=True,
                dia_recebimento=1,
                tipo="avulsa",
                mes_referencia="2026-06",
            )
        )
