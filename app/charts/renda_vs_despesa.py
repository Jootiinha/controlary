"""Barras: renda mensal (recorrente + avulsa + parcelas do mês) vs gastos por mês."""
from __future__ import annotations

from datetime import date

import numpy as np
from matplotlib.ticker import FuncFormatter

from app.charts.plot_labels import annotate_bars
from app.services import expense_totals_service, income_sources_service
from app.utils.formatting import format_currency_short


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


def next_n_month_keys(n: int) -> list[str]:
    """Os ``n`` meses civis seguintes ao mês atual (primeiro = próximo mês)."""
    today = date.today()
    y, m = today.year, today.month
    m += 1
    if m > 12:
        m = 1
        y += 1
    out: list[str] = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def fetch_data(months: int = 6) -> tuple[list[str], list[float], list[float]]:
    keys = _last_n_month_keys(months)
    r_vals = [income_sources_service.sum_for_month(k) for k in keys]
    g_vals = [expense_totals_service.total_despesa_mes(k) for k in keys]
    labels = [k[5:7] + "/" + k[2:4] for k in keys]
    return labels, r_vals, g_vals


def plot(ax) -> None:
    labels, r_vals, g_vals = fetch_data()
    x = np.arange(len(labels))
    w = 0.35
    bars_r = ax.bar(
        x - w / 2, r_vals, width=w, label="Renda (mês)", color="#22C55E"
    )
    bars_g = ax.bar(
        x + w / 2,
        g_vals,
        width=w,
        label="Despesas (caixa + cartão)",
        color="#EF4444",
    )
    annotate_bars(ax, bars_r, r_vals, fontsize=7, dy=3)
    annotate_bars(ax, bars_g, g_vals, fontsize=7, dy=3)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    ax.legend(fontsize=8)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda v, _: format_currency_short(v))
    )
    ax.set_title(
        "Renda esperada (por mês) vs despesas\n(caixa no mês + compras no cartão)"
    )
    ax.grid(True, axis="y", alpha=0.25)
