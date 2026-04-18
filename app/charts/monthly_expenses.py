"""Gráfico de gastos por mês (últimos 12 meses)."""
from __future__ import annotations

from datetime import date
from typing import Dict

from app.database.connection import transaction
from app.charts.plot_labels import annotate_bars


def fetch_data(months: int = 12) -> Dict[str, float]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT substr(data, 1, 7) AS mes, SUM(valor) AS total
              FROM payments
             GROUP BY mes
             ORDER BY mes DESC
             LIMIT ?
            """,
            (months,),
        ).fetchall()

    dados = {r["mes"]: float(r["total"] or 0) for r in rows}

    today = date.today()
    year, month = today.year, today.month
    resultado: Dict[str, float] = {}
    for _ in range(months):
        key = f"{year:04d}-{month:02d}"
        resultado[key] = dados.get(key, 0.0)
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return dict(reversed(list(resultado.items())))


def plot(ax) -> None:
    data = fetch_data()
    meses = list(data.keys())
    valores = list(data.values())
    bars = ax.bar(meses, valores, color="#4C8BF5")
    annotate_bars(ax, bars, valores, fontsize=7, dy=3)
    ax.set_title("Gastos por mês (últimos 12 meses)")
    ax.set_ylabel("R$")
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")
