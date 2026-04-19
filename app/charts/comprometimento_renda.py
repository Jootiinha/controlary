"""Percentual: despesas (caixa + cartão) / renda esperada do mês."""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

from app.charts.plot_labels import annotate_bars
from app.charts.renda_vs_despesa import build_series


def plot(ax) -> None:
    labels, r_vals, g_vals, keys_past, keys_fut = build_series()
    pct: list[float] = []
    for r, g in zip(r_vals, g_vals):
        if r > 0:
            pct.append(100.0 * g / r)
        else:
            pct.append(0.0)
    x = np.arange(len(labels))
    bars = ax.bar(x, pct, color="#F59E0B")
    annotate_bars(
        ax,
        bars,
        pct,
        fontsize=7,
        dy=3,
        format_value=lambda v: f"{v:.0f}%",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    if keys_past and keys_fut:
        ax.axvline(len(keys_past) - 0.5, color="#9CA3AF", linewidth=0.9, linestyle=":")
    ax.set_ylabel("% da renda")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_title(
        "Comprometimento: despesas / renda\n"
        "(passado: realizado · futuro: previsto do mês)"
    )
    ax.set_ylim(0, max(pct + [5]) * 1.1)
    ax.grid(True, axis="y", alpha=0.25)

    def _hover_format(artist, target, index):
        if isinstance(artist, Rectangle):
            return f"{artist.get_height():.1f}%"
        return ""

    ax._hover_format = _hover_format
