"""Evolução das despesas (pagamentos registrados) mês a mês no ano civil."""
from __future__ import annotations

from datetime import date

from app.charts.comparison_refs import add_prev_and_avg6_lines, payments_prev_month_and_avg6
from app.charts.plot_labels import annotate_line_points
from app.database.connection import transaction

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


def fetch_calendar_year(year: int | None = None) -> tuple[int, list[str], list[float]]:
    if year is None:
        year = date.today().year
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT substr(data, 1, 7) AS mes, SUM(valor) AS total
              FROM payments
             WHERE data >= ? AND data < ?
             GROUP BY mes
             ORDER BY mes
            """,
            (f"{year}-01-01", f"{year + 1}-01-01"),
        ).fetchall()
    dados = {r["mes"]: float(r["total"] or 0) for r in rows}
    meses_keys = [f"{year:04d}-{m:02d}" for m in range(1, 13)]
    valores = [dados.get(k, 0.0) for k in meses_keys]
    labels = list(_MONTH_ABBR)
    return year, labels, valores


def plot(ax) -> None:
    year, labels, valores = fetch_calendar_year()
    x = list(range(12))
    ax.plot(x, valores, marker="o", color="#4C8BF5", linewidth=2, zorder=3)
    ax.fill_between(x, valores, alpha=0.12, color="#4C8BF5", zorder=1)
    y_prev, y_avg = payments_prev_month_and_avg6()
    add_prev_and_avg6_lines(ax, y_prev, y_avg)
    annotate_line_points(ax, x, valores, fontsize=6, dy=4, skip_zero=False, clip_on=False)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title(f"Despesas no ano {year} (por mês)")
    ax.set_ylabel("R$")
    ax.set_xlim(-0.35, 11.35)

    y_all = [float(v) for v in valores] + [float(y_prev), float(y_avg)]
    top = max(y_all) if y_all else 0.0
    bottom = min(0.0, min(y_all) if y_all else 0.0)
    span = top - bottom
    if span <= 0:
        span = 1.0
    # Espaço extra no topo para rótulos em pt e para a legenda
    ax.set_ylim(bottom, bottom + span * 1.2)
