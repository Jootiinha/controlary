"""Fluxo de caixa acumulado: soma (renda do mês − despesas do mês), com projeção."""
from __future__ import annotations

from statistics import mean

from matplotlib.ticker import FuncFormatter

from app.charts.plot_labels import annotate_line_points
from app.charts.renda_vs_despesa import fetch_data as fetch_renda_gastos
from app.charts.renda_vs_despesa import next_n_month_keys
from app.utils.formatting import format_currency_short


def plot(ax) -> None:
    labels_hist, r_vals, g_vals = fetch_renda_gastos()
    acc = 0.0
    ys_hist: list[float] = []
    for r, g in zip(r_vals, g_vals):
        acc += r - g
        ys_hist.append(acc)
    n_hist = len(labels_hist)
    x_hist = list(range(n_hist))

    deltas = [r - g for r, g in zip(r_vals, g_vals)]
    d_bar = mean(deltas) if deltas else 0.0
    last_acc = ys_hist[-1] if ys_hist else 0.0
    ys_proj = [last_acc + k * d_bar for k in range(1, 7)]
    keys_fut = next_n_month_keys(6)
    labels_fut = [k[5:7] + "/" + k[2:4] for k in keys_fut]
    x_proj = list(range(n_hist, n_hist + len(ys_proj)))

    ax.plot(
        x_hist,
        ys_hist,
        marker="o",
        color="#6366F1",
        linewidth=1.8,
        label="Realizado",
        zorder=3,
    )
    annotate_line_points(ax, x_hist, ys_hist, fontsize=7, dy=7, clip_on=True)
    ax.plot(
        x_proj,
        ys_proj,
        linestyle=(0, (6, 4)),
        marker="o",
        markersize=5,
        color="#A5B4FC",
        linewidth=1.6,
        label="Projeção (média do saldo mensal)",
        zorder=2,
    )

    all_x = x_hist + x_proj
    all_labels = labels_hist + labels_fut
    ax.set_xticks(all_x)
    ax.set_xticklabels(all_labels, rotation=35, ha="right", fontsize=8)
    if n_hist > 0:
        ax.axvline(n_hist - 0.5, color="#9CA3AF", linewidth=0.9, linestyle=":")
    ax.axhline(0, color="#9CA3AF", linewidth=0.8)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda v, _: format_currency_short(v))
    )
    ax.set_title(
        "Fluxo acumulado (renda − despesas)\n"
        "Projeção: último acumulado + k × média(renda − despesa) dos 6 meses"
    )
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=7, loc="best")
