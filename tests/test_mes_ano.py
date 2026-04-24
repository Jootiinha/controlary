from __future__ import annotations

import pytest

from app.utils.mes_ano import MesAno


def test_from_str_and_str() -> None:
    m = MesAno.from_str("2025-01")
    assert str(m) == "2025-01"
    assert m.ano == 2025 and m.mes == 1


def test_from_str_single_digit_month() -> None:
    m = MesAno.from_str("2025-9")
    assert m.mes == 9
    assert str(m) == "2025-09"


def test_invalid_month_raises() -> None:
    with pytest.raises(ValueError):
        MesAno(2025, 13)


def test_with_day_caps_february() -> None:
    m = MesAno(2025, 2)
    d = m.with_day(31)
    assert d.day == 28


def test_next_previous() -> None:
    assert str(MesAno(2025, 12).next()) == "2026-01"
    assert str(MesAno(2025, 1).previous()) == "2024-12"


def test_iter_until() -> None:
    a = MesAno(2025, 11)
    b = MesAno(2026, 1)
    assert [str(x) for x in a.iter_until(b)] == ["2025-11", "2025-12", "2026-01"]
