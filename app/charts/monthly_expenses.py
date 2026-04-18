"""Custo de vida: soma dos lançamentos por mês (últimos 12 meses)."""
from __future__ import annotations

from datetime import date
from typing import Dict

from app.database.connection import transaction
from app.charts.plot_labels import annotate_bars


def _rolling_month_keys(months: int) -> tuple[list[str], str, str]:
    """Meses calendário consecutivos do mais antigo ao mais recente (últimos ``months``)."""
    today = date.today()
    y, m = today.year, today.month
    newest_first: list[str] = []
    for _ in range(months):
        newest_first.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    chronological = list(reversed(newest_first))
    return chronological, chronological[0], chronological[-1]


def fetch_data(months: int = 12) -> Dict[str, float]:
    """Soma **todos** os lançamentos em ``payments`` no mês (cartão e conta)."""
    keys, first_ym, last_ym = _rolling_month_keys(months)
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT substr(data, 1, 7) AS mes, COALESCE(SUM(valor), 0) AS total
              FROM payments
             WHERE substr(data, 1, 7) BETWEEN ? AND ?
             GROUP BY mes
            """,
            (first_ym, last_ym),
        ).fetchall()

    dados = {r["mes"]: float(r["total"] or 0) for r in rows}
    return {k: dados.get(k, 0.0) for k in keys}


def plot(ax) -> None:
    data = fetch_data()
    meses = list(data.keys())
    valores = list(data.values())
    bars = ax.bar(meses, valores, color="#4C8BF5")
    annotate_bars(ax, bars, valores, fontsize=7, dy=3)
    ax.set_title(
        "Custo de vida por mês — últimos 12 meses\n(todos os lançamentos: cartão e conta)",
        fontsize=10,
        pad=10,
    )
    ax.set_ylabel("R$")
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")
