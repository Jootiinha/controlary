"""Investimentos e snapshots de valor."""
from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import List, Optional

from app.database.connection import use
from app.events import app_events
from app.models.investment import Investment, InvestmentSnapshot
from app.repositories import investments_repo

_DAYS_PER_YEAR = 365.25


def list_all(
    include_inactive: bool = False, conn: Optional[sqlite3.Connection] = None
) -> List[Investment]:
    with use(conn) as c:
        rows = investments_repo.list_all(c, include_inactive)
    return [Investment.from_row(r) for r in rows]


def evolution_series(inv_id: int) -> list[tuple[str, float]]:
    inv = get(inv_id)
    if inv is None:
        return []
    by_date: dict[str, float] = {inv.data_aplicacao: float(inv.valor_aplicado)}
    for s in list_snapshots(inv_id):
        by_date[s.data] = s.valor_atual
    return sorted(by_date.items(), key=lambda x: x[0])


def _valor_em_data(series: list[tuple[str, float]], data_iso: str) -> float:
    last = 0.0
    for ds, val in series:
        if ds <= data_iso:
            last = float(val)
        else:
            break
    return last


def portfolio_patrimonio_series() -> list[tuple[str, float]]:
    invs = list_all()
    all_dates: set[str] = set()
    series_by_id: dict[int, list[tuple[str, float]]] = {}
    for inv in invs:
        if inv.id is None:
            continue
        ser = evolution_series(inv.id)
        series_by_id[inv.id] = ser
        for d, _ in ser:
            all_dates.add(d)
    if not all_dates:
        return []
    out: list[tuple[str, float]] = []
    for d in sorted(all_dates):
        total = 0.0
        for ser in series_by_id.values():
            total += _valor_em_data(ser, d)
        out.append((d, total))
    return out


def last_value_and_gain(inv_id: int) -> tuple[float, float]:
    inv = get(inv_id)
    if inv is None:
        return (0.0, 0.0)
    series = evolution_series(inv_id)
    va = float(inv.valor_aplicado)
    if not series:
        return (va, 0.0)
    last_v = series[-1][1]
    return (last_v, last_v - va)


def portfolio_carteira_gain_metrics() -> tuple[float, Optional[float]]:
    """Ganho agregado em R$ e variação % sobre o total aplicado (carteira ativa)."""
    invs = list_all()
    total_aplicado = 0.0
    patrimonio = 0.0
    for inv in invs:
        if inv.id is None:
            continue
        total_aplicado += float(inv.valor_aplicado)
        last_v, _ = last_value_and_gain(inv.id)
        patrimonio += last_v
    ganho = patrimonio - total_aplicado
    if total_aplicado <= 0:
        return (ganho, None)
    pct = (patrimonio / total_aplicado - 1.0) * 100.0
    return (ganho, pct)


def _parse_iso(d: str) -> date:
    return datetime.strptime(d.strip(), "%Y-%m-%d").date()


def _cagr_percent_aa(
    v_ini: float, d_ini: str, v_fim: float, d_fim: str
) -> Optional[float]:
    """Taxa composta anual implícita; ano civil médio via 365.25 dias."""
    if v_ini <= 0 or v_fim <= 0:
        return None
    t0 = _parse_iso(d_ini)
    t1 = _parse_iso(d_fim)
    days = (t1 - t0).days
    if days <= 0:
        return None
    years = days / _DAYS_PER_YEAR
    if years <= 0:
        return None
    ratio = v_fim / v_ini
    if ratio <= 0:
        return None
    try:
        return (ratio ** (1.0 / years) - 1.0) * 100.0
    except (OverflowError, ValueError, ZeroDivisionError):
        return None


def _recalculate_rendimento_aa_conn(conn: sqlite3.Connection, inv_id: int) -> None:
    row = investments_repo.fetch_valor_aplicado_data(conn, inv_id)
    if row is None:
        return
    snap_rows = investments_repo.list_snapshots_ordered(conn, inv_id)
    if not snap_rows:
        return
    v_ini = float(row["valor_aplicado"] or 0)
    d_ini = row["data_aplicacao"]
    last = snap_rows[-1]
    v_fim = float(last["valor_atual"] or 0)
    d_fim = last["data"]
    pct = _cagr_percent_aa(v_ini, d_ini, v_fim, d_fim)
    if pct is None:
        return
    investments_repo.update_rendimento_aa(conn, inv_id, pct)


def get(inv_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Investment]:
    with use(conn) as c:
        row = investments_repo.get_row(c, inv_id)
    return Investment.from_row(row) if row else None


def create(
    inv: Investment, conn: Optional[sqlite3.Connection] = None
) -> int:
    with use(conn) as c:
        pid = investments_repo.insert_investment(
            c,
            banco_id=int(inv.banco_id),
            nome=inv.nome.strip(),
            tipo=inv.tipo,
            valor_aplicado=float(inv.valor_aplicado),
            rendimento_percentual_aa=inv.rendimento_percentual_aa,
            data_aplicacao=inv.data_aplicacao,
            data_vencimento=inv.data_vencimento,
            category_id=inv.category_id,
            observacao=inv.observacao,
            ativo=1 if inv.ativo else 0,
        )
    app_events().investments_changed.emit()
    return pid


def update(
    inv: Investment, conn: Optional[sqlite3.Connection] = None
) -> None:
    if inv.id is None:
        raise ValueError("Investimento sem id")
    with use(conn) as c:
        investments_repo.update_investment(
            c,
            inv_id=int(inv.id),
            banco_id=int(inv.banco_id),
            nome=inv.nome.strip(),
            tipo=inv.tipo,
            valor_aplicado=float(inv.valor_aplicado),
            rendimento_percentual_aa=inv.rendimento_percentual_aa,
            data_aplicacao=inv.data_aplicacao,
            data_vencimento=inv.data_vencimento,
            category_id=inv.category_id,
            observacao=inv.observacao,
            ativo=1 if inv.ativo else 0,
        )
        _recalculate_rendimento_aa_conn(c, int(inv.id))
    app_events().investments_changed.emit()


def delete(inv_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    with use(conn) as c:
        investments_repo.delete_investment(c, inv_id)
    app_events().investments_changed.emit()


def total_aplicado(conn: Optional[sqlite3.Connection] = None) -> float:
    with use(conn) as c:
        return investments_repo.sum_aplicado_ativo(c)


def add_snapshot(
    inv_id: int,
    data: str,
    valor_atual: float,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    with use(conn) as c:
        investments_repo.delete_snapshot_on_date(c, inv_id, data)
        investments_repo.insert_snapshot(c, inv_id, data, valor_atual)
        _recalculate_rendimento_aa_conn(c, inv_id)
    app_events().investments_changed.emit()


def list_snapshots(
    inv_id: int, conn: Optional[sqlite3.Connection] = None
) -> List[InvestmentSnapshot]:
    with use(conn) as c:
        rows = investments_repo.list_snapshots(c, inv_id)
    return [InvestmentSnapshot.from_row(r) for r in rows]
