"""Custo de vida: total agregado por mês (últimos 6 meses)."""
from __future__ import annotations

from datetime import date
from typing import Dict

from matplotlib.ticker import FuncFormatter

from app.charts.plot_labels import annotate_bars
from app.services import dashboard_service, expense_totals_service
from app.utils.formatting import current_month, format_currency, format_currency_short

_MONTH_ABBR = (
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
)


def _rolling_month_keys(months: int) -> tuple[list[str], str, str]:
    today = date.today()
    y, m = today.year, today.month
    return _rolling_month_keys_from(y, m, months)


def _rolling_month_keys_from(year: int, month: int, months: int) -> tuple[list[str], str, str]:
    y, m = year, month
    newest_first: list[str] = []
    for _ in range(months):
        newest_first.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    chronological = list(reversed(newest_first))
    return chronological, chronological[0], chronological[-1]


def _keys_ending_at_ym(end_ym: str, months: int) -> list[str]:
    y, m = map(int, end_ym.split("-"))
    chrono, _, _ = _rolling_month_keys_from(y, m, months)
    return chrono


def _label_ym(ym: str) -> str:
    y, mo = map(int, ym.split("-"))
    return f"{_MONTH_ABBR[mo - 1]}/{y % 100:02d}"


def fetch_data(months: int = 6, end_ym: str | None = None) -> Dict[str, float]:
    if end_ym is None:
        keys, _, _ = _rolling_month_keys(months)
    else:
        keys = _keys_ending_at_ym(end_ym, months)
    ref = current_month()
    out: Dict[str, float] = {}
    for k in keys:
        if k < ref:
            out[k] = expense_totals_service.total_despesa_mes(k)
        else:
            out[k] = dashboard_service.previsto_mes_for(k)
    return out


def plot(ax, end_ym: str | None = None) -> None:
    data = fetch_data(6, end_ym=end_ym)
    meses_keys = list(data.keys())
    valores = list(data.values())
    labels = [_label_ym(k) for k in meses_keys]
    x = list(range(len(valores)))
    bars = ax.bar(x, valores, color="#4C8BF5", zorder=3)
    annotate_bars(
        ax,
        bars,
        valores,
        fontsize=8,
        dy=3,
        format_value=format_currency_short,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, rotation=0, ha="center")
    ax.tick_params(axis="x", pad=2)

    avg_window = sum(valores) / len(valores) if valores else 0.0
    ax.axhline(
        avg_window,
        color="#059669",
        linestyle=(0, (4, 4)),
        linewidth=1.2,
        label=f"Média período · {format_currency(avg_window)}",
        zorder=2,
    )
    leg = ax.legend(loc="upper left", fontsize=8, framealpha=0.95, edgecolor="#E5E7EB")
    if leg is not None:
        leg.get_frame().set_linewidth(0.8)

    end_key = end_ym or current_month()
    ax.set_title(
        f"Custo de vida — 6 meses até {_label_ym(end_key)} (realizado / previsto)",
        fontsize=9,
        pad=6,
    )
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda v, _: format_currency_short(v))
    )
    y_all = list(valores) + [avg_window]
    top = max(y_all) if y_all else 0.0
    bottom = min(0.0, min(y_all) if y_all else 0.0)
    span = top - bottom
    if span <= 0:
        span = 1.0
    ax.set_ylim(bottom, bottom + span * 1.28)
    ax.margins(x=0.02)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
