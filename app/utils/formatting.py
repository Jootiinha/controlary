"""Helpers de formatação de valores e datas."""
from __future__ import annotations

import re
from datetime import date, datetime

_RE_DD_MM_YYYY = re.compile(r"^\d{2}/\d{2}/\d{4}$")
_RE_MM_YYYY = re.compile(r"^\d{1,2}/\d{4}$")


def format_currency(value: float | int | None) -> str:
    if value is None:
        return "R$ 0,00"
    formatted = f"{float(value):,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def format_currency_short(value: float | int | None) -> str:
    """Rótulos compactos para gráficos (ex.: R$ 1,2k, R$ 12k, R$ 1,2M).

    Negativos no mesmo padrão que ``format_currency`` (``R$ -…``), não ``-R$ …``.
    """
    if value is None:
        return "R$ 0"
    v = float(value)
    neg = v < 0
    x = abs(v)
    if x >= 1_000_000:
        s = f"{x / 1_000_000:.1f}".replace(".", ",").rstrip("0").rstrip(",")
        if s == "":
            s = "0"
        return f"R$ -{s}M" if neg else f"R$ {s}M"
    if x >= 1000:
        s = f"{x / 1000:.1f}".replace(".", ",").rstrip("0").rstrip(",")
        if s == "":
            s = "0"
        return f"R$ -{s}k" if neg else f"R$ {s}k"
    n = int(round(x))
    thousands = f"{n:,}".replace(",", ".")
    return f"R$ -{thousands}" if neg else f"R$ {thousands}"


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


def try_parse_currency_br_display(text: str) -> float | None:
    """Interpreta texto no estilo ``format_currency`` (ex.: ``R$ 1.234,56``)."""
    s = (text or "").strip()
    neg_prefix = False
    if s.startswith("-R$"):
        neg_prefix = True
        s = "R$" + s[3:].lstrip()
    if not s.startswith("R$"):
        return None
    rest = s[2:].strip()
    neg = neg_prefix
    if rest.startswith("-"):
        neg = True
        rest = rest[1:].strip()
    if not rest:
        return 0.0
    if "," in rest:
        intpart, frac = rest.rsplit(",", 1)
        intpart = intpart.replace(".", "")
        if not intpart.isdigit() or not frac.isdigit():
            return None
        try:
            v = float(f"{intpart}.{frac}")
        except ValueError:
            return None
    else:
        digits = rest.replace(".", "")
        if not digits.isdigit():
            return None
        try:
            v = float(digits)
        except ValueError:
            return None
    return -v if neg else v


def try_parse_dd_mm_yyyy(text: str) -> date | None:
    s = (text or "").strip()
    if not _RE_DD_MM_YYYY.match(s):
        return None
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except ValueError:
        return None


def try_parse_mm_yyyy_br(text: str) -> tuple[int, int] | None:
    """Ordenação para rótulos ``MM/YYYY`` ou ``M/YYYY``."""
    s = (text or "").strip()
    if not _RE_MM_YYYY.match(s):
        return None
    parts = s.split("/")
    try:
        month, year = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return None
    if not (1 <= month <= 12):
        return None
    return year, month


def compare_sort_display_values(a: str, b: str) -> int | None:
    """
    Comparação para ordenação de células formatadas.
    Retorna -1/0/1 se regra específica se aplica; None para comparar por texto (locale).
    """
    ca = try_parse_currency_br_display(a)
    cb = try_parse_currency_br_display(b)
    if ca is not None and cb is not None:
        if ca < cb:
            return -1
        if ca > cb:
            return 1
        return 0
    da = try_parse_dd_mm_yyyy(a)
    db = try_parse_dd_mm_yyyy(b)
    if da is not None and db is not None:
        if da < db:
            return -1
        if da > db:
            return 1
        return 0
    ma = try_parse_mm_yyyy_br(a)
    mb = try_parse_mm_yyyy_br(b)
    if ma is not None and mb is not None:
        if ma < mb:
            return -1
        if ma > mb:
            return 1
        return 0
    return None
