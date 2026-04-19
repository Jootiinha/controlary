"""Testes de parsing e comparação usados na ordenação de tabelas."""
from __future__ import annotations

from datetime import date

from app.utils.formatting import (
    compare_sort_display_values,
    try_parse_currency_br_display,
    try_parse_dd_mm_yyyy,
    try_parse_mm_yyyy_br,
)


def test_parse_currency_br() -> None:
    assert try_parse_currency_br_display("R$ 0,00") == 0.0
    assert try_parse_currency_br_display("R$ 10,50") == 10.5
    assert try_parse_currency_br_display("R$ 1.234,56") == 1234.56
    assert try_parse_currency_br_display("R$ -2,00") == -2.0
    assert try_parse_currency_br_display("10,00") is None


def test_parse_dates() -> None:
    assert try_parse_dd_mm_yyyy("31/12/2025") == date(2025, 12, 31)
    assert try_parse_dd_mm_yyyy("2025-12-31") is None
    assert try_parse_mm_yyyy_br("04/2026") == (2026, 4)
    assert try_parse_mm_yyyy_br("12/2025") == (2025, 12)


def test_compare_sort_display_values() -> None:
    assert compare_sort_display_values("R$ 2,00", "R$ 10,00") == -1
    assert compare_sort_display_values("R$ 10,00", "R$ 2,00") == 1
    assert compare_sort_display_values("R$ 1,00", "R$ 1,00") == 0
    assert compare_sort_display_values("01/01/2025", "02/01/2025") == -1
    assert compare_sort_display_values("foo", "bar") is None


def test_compare_sort_mm_yyyy() -> None:
    assert compare_sort_display_values("01/2026", "12/2025") == 1
    assert compare_sort_display_values("12/2025", "01/2026") == -1
