"""Investimentos e snapshots de valor."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from app.database.connection import transaction
from app.models.investment import Investment, InvestmentSnapshot

_DAYS_PER_YEAR = 365.25


def list_all(include_inactive: bool = False) -> List[Investment]:
    with transaction() as conn:
        q = """
            SELECT i.*, a.nome AS banco_nome, cat.nome AS categoria_nome
              FROM investments i
              JOIN accounts a ON a.id = i.banco_id
              LEFT JOIN categories cat ON cat.id = i.category_id
        """
        if not include_inactive:
            q += " WHERE i.ativo = 1"
        q += " ORDER BY i.nome COLLATE NOCASE"
        rows = conn.execute(q).fetchall()
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


def _cagr_percent_aa(v_ini: float, d_ini: str, v_fim: float, d_fim: str) -> Optional[float]:
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


def _recalculate_rendimento_aa_conn(conn, inv_id: int) -> None:
    row = conn.execute(
        """
        SELECT valor_aplicado, data_aplicacao
          FROM investments
         WHERE id = ?
        """,
        (inv_id,),
    ).fetchone()
    if row is None:
        return
    snap_rows = conn.execute(
        """
        SELECT data, valor_atual
          FROM investment_snapshots
         WHERE investment_id = ?
         ORDER BY date(data)
        """,
        (inv_id,),
    ).fetchall()
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
    conn.execute(
        "UPDATE investments SET rendimento_percentual_aa = ? WHERE id = ?",
        (pct, inv_id),
    )


def get(inv_id: int) -> Optional[Investment]:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT i.*, a.nome AS banco_nome, cat.nome AS categoria_nome
              FROM investments i
              JOIN accounts a ON a.id = i.banco_id
              LEFT JOIN categories cat ON cat.id = i.category_id
             WHERE i.id = ?
            """,
            (inv_id,),
        ).fetchone()
    return Investment.from_row(row) if row else None


def create(inv: Investment) -> int:
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO investments (
                banco_id, nome, tipo, valor_aplicado, rendimento_percentual_aa,
                data_aplicacao, data_vencimento, category_id, observacao, ativo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inv.banco_id,
                inv.nome.strip(),
                inv.tipo,
                inv.valor_aplicado,
                inv.rendimento_percentual_aa,
                inv.data_aplicacao,
                inv.data_vencimento,
                inv.category_id,
                inv.observacao,
                1 if inv.ativo else 0,
            ),
        )
        return int(cur.lastrowid)


def update(inv: Investment) -> None:
    if inv.id is None:
        raise ValueError("Investimento sem id")
    with transaction() as conn:
        conn.execute(
            """
            UPDATE investments
               SET banco_id = ?, nome = ?, tipo = ?, valor_aplicado = ?,
                   rendimento_percentual_aa = ?, data_aplicacao = ?, data_vencimento = ?,
                   category_id = ?, observacao = ?, ativo = ?
             WHERE id = ?
            """,
            (
                inv.banco_id,
                inv.nome.strip(),
                inv.tipo,
                inv.valor_aplicado,
                inv.rendimento_percentual_aa,
                inv.data_aplicacao,
                inv.data_vencimento,
                inv.category_id,
                inv.observacao,
                1 if inv.ativo else 0,
                inv.id,
            ),
        )
        _recalculate_rendimento_aa_conn(conn, inv.id)


def delete(inv_id: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM investments WHERE id = ?", (inv_id,))


def total_aplicado() -> float:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor_aplicado), 0) AS t
              FROM investments
             WHERE ativo = 1
            """
        ).fetchone()
    return float(row["t"] or 0)


def add_snapshot(inv_id: int, data: str, valor_atual: float) -> None:
    with transaction() as conn:
        conn.execute(
            """
            DELETE FROM investment_snapshots
             WHERE investment_id = ? AND data = ?
            """,
            (inv_id, data),
        )
        conn.execute(
            """
            INSERT INTO investment_snapshots (investment_id, data, valor_atual)
            VALUES (?, ?, ?)
            """,
            (inv_id, data, valor_atual),
        )
        _recalculate_rendimento_aa_conn(conn, inv_id)


def list_snapshots(inv_id: int) -> List[InvestmentSnapshot]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT investment_id, data, valor_atual
              FROM investment_snapshots
             WHERE investment_id = ?
             ORDER BY date(data)
            """,
            (inv_id,),
        ).fetchall()
    return [InvestmentSnapshot.from_row(r) for r in rows]
