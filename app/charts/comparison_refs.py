"""Referências de comparativo (mês anterior e média dos últimos 6 meses) para gráficos de linha."""
from __future__ import annotations

from datetime import date

from matplotlib.axes import Axes

from app.database.connection import transaction
from app.utils.formatting import format_currency


def _month_keys_back_from_today(n: int, ref: date | None = None) -> list[str]:
    """Retorna [M-1, M-2, ..., M-n] como ``YYYY-MM`` (meses calendário anteriores ao mês de ``ref``)."""
    ref = ref or date.today()
    y, m = ref.year, ref.month
    out: list[str] = []
    for _ in range(n):
        m -= 1
        if m == 0:
            m = 12
            y -= 1
        out.append(f"{y:04d}-{m:02d}")
    return out


def payments_prev_month_and_avg6(ref: date | None = None) -> tuple[float, float]:
    """Totais de pagamentos: mês calendário anterior e média dos 6 meses anteriores ao atual."""
    keys = _month_keys_back_from_today(6, ref)
    with transaction() as conn:
        vals = []
        for ym in keys:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(valor), 0) AS t
                  FROM payments
                 WHERE substr(data, 1, 7) = ?
                """,
                (ym,),
            ).fetchone()
            vals.append(float(row["t"]))
    prev_m = vals[0]
    avg6 = sum(vals) / 6.0
    return prev_m, avg6


def installments_prev_month_and_avg6(ref: date | None = None) -> tuple[float, float]:
    """Soma de parcelas por ``mes_referencia``: mês anterior e média dos 6 meses anteriores."""
    keys = _month_keys_back_from_today(6, ref)
    with transaction() as conn:
        vals = []
        for ym in keys:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(valor_parcela), 0) AS t
                  FROM installments
                 WHERE mes_referencia = ?
                """,
                (ym,),
            ).fetchone()
            vals.append(float(row["t"]))
    prev_m = vals[0]
    avg6 = sum(vals) / 6.0
    return prev_m, avg6


def add_prev_and_avg6_lines(ax: Axes, prev_val: float, avg_val: float) -> None:
    """Desenha duas retas horizontais tracejadas e legenda."""
    ax.axhline(
        prev_val,
        color="#64748B",
        linestyle=(0, (4, 4)),
        linewidth=1.3,
        label=f"Mês anterior · {format_currency(prev_val)}",
        zorder=2,
    )
    ax.axhline(
        avg_val,
        color="#059669",
        linestyle=(0, (2, 3)),
        linewidth=1.3,
        label=f"Média 6 meses · {format_currency(avg_val)}",
        zorder=2,
    )
    leg = ax.legend(loc="best", fontsize=8, framealpha=0.95, edgecolor="#E5E7EB")
    if leg is not None:
        leg.get_frame().set_linewidth(0.8)
