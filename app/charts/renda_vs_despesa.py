"""Barras: renda mensal (recorrente + avulsa + parcelas do mês) vs gastos por mês."""
from __future__ import annotations

from datetime import date

import numpy as np
from matplotlib.ticker import FuncFormatter

from app.charts.plot_labels import annotate_bars
from app.services import dashboard_service, expense_totals_service, income_sources_service
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


def build_series(
    months_past: int = 3, months_future: int = 9
) -> tuple[list[str], list[float], list[float], list[str], list[str]]:
    keys_past = _last_n_month_keys(months_past)
    keys_fut = next_n_month_keys(months_future)
    keys = keys_past + keys_fut
    labels = [k[5:7] + "/" + k[2:4] for k in keys]
    r_vals = [income_sources_service.sum_for_month(k) for k in keys]
    g_vals: list[float] = [
        expense_totals_service.total_despesa_mes(k) for k in keys_past
    ]
    g_vals += [dashboard_service.previsto_mes_for(k) for k in keys_fut]
    return labels, r_vals, g_vals, keys_past, keys_fut


def plot(ax, months_past: int = 3, months_future: int = 9) -> None:
    labels, r_vals, g_vals, keys_past, keys_fut = build_series(
        months_past, months_future
    )

    x = np.arange(len(labels))
    w = 0.35
    bars_r = ax.bar(
        x - w / 2, r_vals, width=w, label="Renda (mês)", color="#22C55E"
    )
    bars_g = ax.bar(
        x + w / 2,
        g_vals,
        width=w,
        label="Despesas (realizado / previsto mês)",
        color="#EF4444",
    )
    annotate_bars(ax, bars_r, r_vals, fontsize=7, dy=3)
    annotate_bars(ax, bars_g, g_vals, fontsize=7, dy=3)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    if keys_past and keys_fut:
        ax.axvline(len(keys_past) - 0.5, color="#9CA3AF", linewidth=0.9, linestyle=":")
    ax.legend(fontsize=8)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda v, _: format_currency_short(v))
    )
    ax.set_title(
        "Renda esperada (recorrente + avulsa) vs despesas\n"
        f"Passado: renda e despesas realizadas · Futuro: renda esperada e despesas previstas "
        f"(card «Gasto previsto no mês»)"
    )
    ax.grid(True, axis="y", alpha=0.25)
