"""Linha do tempo do valor de um investimento (eixo X = calendário desde a data de aplicação)."""
from __future__ import annotations

from datetime import datetime

import matplotlib.dates as mdates

from app.charts.plot_labels import annotate_line_points
from app.services import investments_service


def plot_for_investment(investment_id: int):
    def _plot(ax) -> None:
        inv = investments_service.get(investment_id)
        series = investments_service.evolution_series(investment_id)
        if not series or inv is None:
            ax.text(0.5, 0.5, "Sem dados", ha="center", va="center")
            ax.set_axis_off()
            return
        dates = [datetime.strptime(d, "%Y-%m-%d") for d, _ in series]
        xs = mdates.date2num(dates)
        ys = [v for _, v in series]
        ax.plot(xs, ys, marker="o", color="#2563EB", linewidth=1.5)
        annotate_line_points(ax, xs, ys, fontsize=7, dy=8, clip_on=False)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
        ax.set_ylabel("Valor (R$)")
        ax.set_title(inv.nome)
        ax.grid(True, alpha=0.25)
        ylo, yhi = min(ys), max(ys)
        if ylo == yhi:
            span = abs(yhi) if yhi else 1.0
            ax.set_ylim(ylo - span * 0.15, yhi + span * 0.35)
        else:
            pad = (yhi - ylo) * 0.14
            ax.set_ylim(ylo - pad * 0.35, yhi + pad)
        if len(xs) == 1:
            ax.set_xlim(xs[0] - 2.0, xs[0] + 2.0)
        fig = ax.get_figure()
        if fig is not None:
            fig.autofmt_xdate(rotation=35, ha="right")

    return _plot
