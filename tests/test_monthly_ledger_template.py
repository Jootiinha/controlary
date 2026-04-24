from __future__ import annotations

import pytest

from app.services._monthly_ledger import MonthlyLedgerService, data_iso_no_mes
from app.services.competencia_ledger import data_iso_no_mes as data_iso_public
from app.utils.mes_ano import MesAno


def test_data_iso_no_mes() -> None:
    assert data_iso_no_mes("2025-02", 31) == "2025-02-28"
    assert data_iso_no_mes("2024-02", 30) == "2024-02-29"
    assert data_iso_no_mes("2025-06", 5) == "2025-06-05"


def test_data_iso_no_mes_accepts_mes_ano() -> None:
    assert data_iso_no_mes(MesAno(2025, 2), 31) == "2025-02-28"
    assert data_iso_public(MesAno(2025, 6), 5) == "2025-06-05"


def test_monthly_ledger_service_is_abc() -> None:
    with pytest.raises(TypeError):
        MonthlyLedgerService()  # type: ignore[misc, call-arg]
