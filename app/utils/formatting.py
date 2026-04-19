"""Helpers de formatação de valores e datas."""
from __future__ import annotations

from datetime import date, datetime


def format_currency(value: float | int | None) -> str:
    if value is None:
        return "R$ 0,00"
    formatted = f"{float(value):,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def format_currency_short(value: float | int | None) -> str:
    """Rótulos compactos para gráficos (ex.: R$ 1,2k, R$ 12k, R$ 1,2M)."""
    if value is None:
        return "R$ 0"
    x = abs(float(value))
    sign = "-" if float(value) < 0 else ""
    if x >= 1_000_000:
        s = f"{x / 1_000_000:.1f}".replace(".", ",").rstrip("0").rstrip(",")
        if s == "":
            s = "0"
        return f"{sign}R$ {s}M"
    if x >= 1000:
        s = f"{x / 1000:.1f}".replace(".", ",").rstrip("0").rstrip(",")
        if s == "":
            s = "0"
        return f"{sign}R$ {s}k"
    n = int(round(x))
    return f"{sign}R$ {n:,}".replace(",", ".")


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def format_date_br(value: str | date | None) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, str):
        value = parse_date(value)
    return value.strftime("%d/%m/%Y")


def current_month() -> str:
    return datetime.now().strftime("%Y-%m")


def format_month_br(value: str | None) -> str:
    """Converte ``YYYY-MM`` em ``MM/YYYY``."""
    if not value:
        return ""
    try:
        year, month = value.split("-")
        return f"{month}/{year}"
    except ValueError:
        return value
