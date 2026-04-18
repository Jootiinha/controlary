"""Barras: renda mensal (soma fontes ativas) vs gastos em pagamentos por mês."""
from __future__ import annotations

from datetime import date

import numpy as np
from matplotlib.ticker import FuncFormatter

from app.charts.plot_labels import annotate_bars
from app.database.connection import transaction
from app.services import income_sources_service


def _last_n_month_keys(n: int) -> list[str]:
    today = date.today()
    y, m = today.year, today.month
    out: list[str] = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(out))


def fetch_data(months: int = 12) -> tuple[list[str], list[float], list[float]]:
    keys = _last_n_month_keys(months)
    renda_fixa = income_sources_service.sum_active_monthly()
    with transaction() as conn:
        gastos: dict[str, float] = {}
        for r in conn.execute(
            """
            SELECT substr(data, 1, 7) AS mes, COALESCE(SUM(valor), 0) AS t
              FROM payments
             GROUP BY mes
            """
        ).fetchall():
            gastos[r["mes"]] = float(r["t"] or 0)
    r_vals = [renda_fixa for _ in keys]
    g_vals = [gastos.get(k, 0.0) for k in keys]
    labels = [k[5:7] + "/" + k[2:4] for k in keys]
    return labels, r_vals, g_vals


def plot(ax) -> None:
    labels, r_vals, g_vals = fetch_data()
    x = np.arange(len(labels))
    w = 0.35
    bars_r = ax.bar(
        x - w / 2, r_vals, width=w, label="Renda (ativas)", color="#22C55E"
    )
    bars_g = ax.bar(
        x + w / 2, g_vals, width=w, label="Gastos (pagamentos)", color="#EF4444"
    )
    annotate_bars(ax, bars_r, r_vals, fontsize=7, dy=3)
    annotate_bars(ax, bars_g, g_vals, fontsize=7, dy=3)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    ax.legend(fontsize=8)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_title("Renda mensal (fixa) vs gastos registrados por mês")
    ax.grid(True, axis="y", alpha=0.25)
