"""Percentual: gastos em pagamentos / renda mensal (ativas) por mês."""
from __future__ import annotations

import numpy as np
from matplotlib.ticker import FuncFormatter

from app.charts.renda_vs_despesa import fetch_data as fetch_renda_gastos


def plot(ax) -> None:
    labels, r_vals, g_vals = fetch_renda_gastos()
    pct: list[float] = []
    for r, g in zip(r_vals, g_vals):
        if r > 0:
            pct.append(100.0 * g / r)
        else:
            pct.append(0.0)
    x = np.arange(len(labels))
    ax.bar(x, pct, color="#F59E0B")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("% da renda")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_title("Comprometimento: gastos / renda mensal")
    ax.set_ylim(0, max(pct + [5]) * 1.1)
    ax.grid(True, axis="y", alpha=0.25)
