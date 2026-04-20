"""Histórico do valor registrado na fatura (fechada/paga) por cartão."""
from __future__ import annotations

from datetime import date

from matplotlib.ticker import FuncFormatter

from app.charts.cards_window import cards_window
from app.charts.invoice_evolution import CARD_LINE_COLORS, _card_name_map
from app.services import card_invoices_service
from app.utils.formatting import format_currency_short


def plot(ax) -> None:
    today = date.today()
    current_ym = f"{today.year:04d}-{today.month:02d}"

    wm = cards_window(current_ym)
    try:
        idx = wm.index(current_ym)
    except ValueError:
        idx = len(wm) - 1

    meses_axis = wm[: idx + 1]
    if not meses_axis:
        ax.text(
            0.5,
            0.5,
            "Sem faturas registradas no período",
            ha="center",
            va="center",
        )
        ax.set_axis_off()
        return

    start_ym = meses_axis[0]
    end_ym = meses_axis[-1]

    by_card = card_invoices_service.history_by_card(start_ym, end_ym)
    names = _card_name_map()

    if not by_card:
        ax.text(
            0.5,
            0.5,
            "Sem faturas registradas no período",
            ha="center",
            va="center",
        )
        ax.set_axis_off()
        return

    n_colors = len(CARD_LINE_COLORS)

    for i, cid in enumerate(sorted(by_card.keys())):
        ym_to_v = dict(by_card[cid])
        ys = [float(ym_to_v[m]) if m in ym_to_v else float("nan") for m in meses_axis]
        label = names.get(cid, f"Cartão #{cid}")
        ax.plot(
            meses_axis,
            ys,
            marker="o",
            color=CARD_LINE_COLORS[i % n_colors],
            linewidth=2,
            label=label,
            zorder=3,
        )

    if current_ym in meses_axis:
        ax.axvline(current_ym, color="#9CA3AF", linewidth=0.9, linestyle=":")

    leg = ax.legend(
        loc="best", fontsize=7, framealpha=0.95, edgecolor="#E5E7EB", ncol=2
    )
    if leg is not None:
        leg.get_frame().set_linewidth(0.8)

    ax.set_title(
        "Faturas registradas por cartão (fechadas/pagas)",
        fontsize=9,
        pad=8,
    )
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda v, _: format_currency_short(v))
    )
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    ax.grid(True, axis="y", alpha=0.22)
