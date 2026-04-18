"""Fluxo de caixa acumulado: soma (renda fixa − gastos no mês)."""
from __future__ import annotations

from datetime import date

from matplotlib.ticker import FuncFormatter

from app.charts.renda_vs_despesa import fetch_data as fetch_renda_gastos


def plot(ax) -> None:
    labels, r_vals, g_vals = fetch_renda_gastos()
    acc = 0.0
    ys: list[float] = []
    for r, g in zip(r_vals, g_vals):
        acc += r - g
        ys.append(acc)
    x = range(len(labels))
    ax.plot(x, ys, marker="o", color="#6366F1", linewidth=1.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    ax.axhline(0, color="#9CA3AF", linewidth=0.8)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_title("Fluxo acumulado (renda ativa − gastos em pagamentos)")
    ax.grid(True, alpha=0.25)
