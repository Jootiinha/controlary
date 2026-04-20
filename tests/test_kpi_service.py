"""KPIs canônicos por mês."""
from __future__ import annotations

from pathlib import Path

from app.services import kpi_service


def test_kpi_service_empty_month(test_db_path: Path) -> None:
    k = kpi_service.for_month("2026-05")
    assert k.ano_mes == "2026-05"
    assert k.renda_esperada == 0.0
    assert k.renda_recebida == 0.0
    assert k.despesa_prevista == 0.0
