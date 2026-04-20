"""Janela temporal comum dos gráficos da aba Cartão (Gráficos e análises)."""
from __future__ import annotations

MONTHS_PAST = 6
MONTHS_FUTURE = 12


def _parse_ym(ym: str) -> tuple[int, int]:
    y, m = ym.split("-", 1)
    return int(y), int(m)


def _ym_key(y: int, m: int) -> str:
    return f"{y:04d}-{m:02d}"


def add_months(ym: str, n: int) -> str:
    y, mo = _parse_ym(ym)
    idx = (y * 12 + mo - 1) + n
    y2 = idx // 12
    m2 = idx % 12 + 1
    return _ym_key(y2, m2)


def months_between_inclusive(start: str, end: str) -> list[str]:
    if start > end:
        return []
    out: list[str] = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur = add_months(cur, 1)
    return out


def diff_months(a: str, b: str) -> int:
    """Diferença em meses: índice de b menos índice de a (pode ser negativa)."""
    ya, ma = _parse_ym(a)
    yb, mb = _parse_ym(b)
    return (yb * 12 + mb) - (ya * 12 + ma)


def cards_window(current_ym: str) -> list[str]:
    start = add_months(current_ym, -MONTHS_PAST)
    end = add_months(current_ym, MONTHS_FUTURE)
    return months_between_inclusive(start, end)
