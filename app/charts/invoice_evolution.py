"""Gráfico de evolução da fatura (total de parcelas por mês de referência)."""
from __future__ import annotations

from app.charts.comparison_refs import add_prev_and_avg6_lines, installments_prev_month_and_avg6
from app.charts.plot_labels import annotate_line_points
from app.database.connection import transaction


def fetch_data():
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT mes_referencia AS mes, SUM(valor_parcela) AS total
              FROM installments
             GROUP BY mes_referencia
             ORDER BY mes_referencia ASC
            """
        ).fetchall()
    return [(r["mes"], float(r["total"] or 0)) for r in rows]


def plot(ax) -> None:
    data = fetch_data()
    if not data:
        ax.text(0.5, 0.5, "Sem dados de parcelamentos", ha="center", va="center")
        ax.set_axis_off()
        return
    meses = [d[0] for d in data]
    valores = [d[1] for d in data]
    ax.plot(meses, valores, marker="o", color="#F59E0B", linewidth=2, zorder=3)
    ax.fill_between(meses, valores, alpha=0.15, color="#F59E0B", zorder=1)
    annotate_line_points(ax, meses, valores, fontsize=7, dy=7)
    y_prev, y_avg = installments_prev_month_and_avg6()
    add_prev_and_avg6_lines(ax, y_prev, y_avg)
    ax.set_title("Evolução da fatura por mês de referência")
    ax.set_ylabel("R$")
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")
