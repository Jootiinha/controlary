"""Datas de competência no livro-caixa (evita duplicar monthrange/split)."""
from __future__ import annotations

from typing import overload

from app.utils.mes_ano import MesAno


@overload
def data_iso_no_mes(ano_mes: str, dia: int) -> str: ...


@overload
def data_iso_no_mes(ano_mes: MesAno, dia: int) -> str: ...


def data_iso_no_mes(ano_mes: str | MesAno, dia: int) -> str:
    """``ano_mes`` em ``YYYY-MM`` ou ``MesAno``; ``dia`` limitado ao último dia do mês."""
    m = ano_mes if isinstance(ano_mes, MesAno) else MesAno.from_str(ano_mes)
    return m.with_day(dia).isoformat()
