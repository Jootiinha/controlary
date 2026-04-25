"""Comparativo de custo de vida: mês atual vs mês anterior."""
from __future__ import annotations

from app.services.dashboard_service import cost_of_living
from app.utils.formatting import current_month, format_currency, format_month_br


def _shift_month(ym: str, delta: int) -> str:
    y, m = map(int, ym.split("-"))
    m += delta
    while m > 12:
        m -= 12
        y += 1
    while m < 1:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}"


def plot(ax, ref: str | None = None) -> None:
    ref = ref or current_month()
    prev = _shift_month(ref, -1)
    v_cur = cost_of_living(ref)
    v_prev = cost_of_living(prev)

    labels = [
        f"Anterior · {format_month_br(prev)}",
        f"Referência · {format_month_br(ref)}",
    ]
    values = [v_prev, v_cur]
    y_pos = [0.0, 1.0]
    colors = ["#94A3B8", "#4C8BF5"]
    bars = ax.barh(y_pos, values, height=0.55, color=colors, zorder=3)

    xmax = max(values + [1.0])
    ax.set_xlim(0, xmax * 1.32)
    ax.set_ylim(-0.6, 1.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.tick_params(axis="y", length=0)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    for bar, val in zip(bars, values):
        w = bar.get_width()
        ax.annotate(
            format_currency(val),
            xy=(w, bar.get_y() + bar.get_height() / 2),
            xytext=(6, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=9,
            clip_on=True,
        )

    delta = v_cur - v_prev
    if v_prev > 0:
        pct = (delta / v_prev) * 100.0
        pct_s = f"{pct:+.1f}%"
    else:
        pct_s = "—"
    sign = "+" if delta > 0 else ""
    delta_line = f"{sign}{format_currency(delta)} ({pct_s}) vs {format_month_br(prev)}"
    color = "#059669" if delta <= 0 else "#DC2626"

    title_main = f"Custo do mês — {format_month_br(ref)} vs {format_month_br(prev)}"
    ax.set_title(title_main, fontsize=10, pad=8, color="#111827")
    ax.set_xlabel(delta_line, fontsize=9, color=color, labelpad=4)

    ax.margins(x=0.02)
