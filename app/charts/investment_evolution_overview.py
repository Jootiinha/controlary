"""Visões agregadas: patrimônio total e linhas por investimento."""
from __future__ import annotations

from datetime import datetime

import matplotlib.dates as mdates
from matplotlib import pyplot as plt

from app.charts.plot_labels import annotate_line_points
from app.services import investments_service


def plot_patrimonio_total():
    def _plot(ax) -> None:
        series = investments_service.portfolio_patrimonio_series()
        if not series:
            ax.text(0.5, 0.5, "Sem dados de evolução", ha="center", va="center")
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
        ax.set_title("Patrimônio total")
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


def plot_todos_investimentos():
    def _plot(ax) -> None:
        invs = investments_service.list_all()
        cmap = plt.get_cmap("tab10")
        lines = 0
        for i, inv in enumerate(invs):
            if inv.id is None:
                continue
            series = investments_service.evolution_series(inv.id)
            if not series:
                continue
            dates = [datetime.strptime(d, "%Y-%m-%d") for d, _ in series]
            xs = mdates.date2num(dates)
            ys = [v for _, v in series]
            color = cmap(i % 10)
            label = inv.nome if len(inv.nome) <= 28 else inv.nome[:25] + "…"
            ax.plot(
                xs,
                ys,
                marker="o",
                linewidth=1.2,
                markersize=4,
                color=color,
                label=label,
            )
            lines += 1
        if lines == 0:
            ax.text(0.5, 0.5, "Sem dados de evolução", ha="center", va="center")
            ax.set_axis_off()
            return
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
        ax.set_ylabel("Valor (R$)")
        ax.set_title("Por investimento")
        ax.grid(True, alpha=0.25)
        leg = ax.legend(loc="best", fontsize=7, framealpha=0.95, ncol=1)
        if leg is not None:
            leg.get_frame().set_linewidth(0.8)
        fig = ax.get_figure()
        if fig is not None:
            fig.autofmt_xdate(rotation=35, ha="right")

    return _plot
