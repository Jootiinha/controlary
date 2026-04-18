"""Linha do tempo do valor de um investimento (snapshots)."""
from __future__ import annotations

from app.services import investments_service
from app.utils.formatting import format_date_br


def plot_for_investment(investment_id: int):
    def _plot(ax) -> None:
        snaps = investments_service.list_snapshots(investment_id)
        if not snaps:
            ax.text(0.5, 0.5, "Sem pontos de valor", ha="center", va="center")
            ax.set_axis_off()
            return
        ys = [s.valor_atual for s in snaps]
        labels = [format_date_br(s.data) for s in snaps]
        xs = list(range(len(ys)))
        ax.plot(xs, ys, marker="o", color="#2563EB", linewidth=1.5)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
        ax.set_ylabel("Valor (R$)")
        ax.grid(True, alpha=0.25)

    return _plot
