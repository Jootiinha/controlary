"""Gráfico de evolução do saldo devedor ao longo dos próximos meses."""
from __future__ import annotations

from datetime import date

from matplotlib.ticker import FuncFormatter

from app.charts.plot_labels import annotate_line_points
from app.services import installments_service
from app.utils.formatting import format_currency_short


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    total = year * 12 + (month - 1) + delta
    return total // 12, (total % 12) + 1


def fetch_data(horizonte: int = 12):
    """Projeta saldo devedor assumindo 1 parcela paga/mês em cada parcelamento ativo."""
    ativos = [i for i in installments_service.list_all() if i.status == "ativo"]
    today = date.today()
    year, month = today.year, today.month
    projecao: list[tuple[str, float]] = []
    for i in range(horizonte):
        y, m = _shift_month(year, month, i)
        key = f"{y:04d}-{m:02d}"
        total = 0.0
        for inst in ativos:
            restantes = max(inst.total_parcelas - inst.parcelas_pagas - i, 0)
            total += inst.valor_parcela * restantes
        projecao.append((key, round(total, 2)))
    return projecao


def plot(ax) -> None:
    data = fetch_data()
    if not data:
        ax.text(0.5, 0.5, "Sem parcelamentos ativos", ha="center", va="center")
        ax.set_axis_off()
        return
    meses = [d[0] for d in data]
    valores = [d[1] for d in data]
    ax.plot(meses, valores, marker="s", color="#DC2626", linewidth=2)
    ax.fill_between(meses, valores, alpha=0.15, color="#DC2626")
    annotate_line_points(ax, meses, valores, fontsize=7, dy=7)
    ax.set_title("Projeção do saldo devedor (próximos 12 meses)")
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda v, _: format_currency_short(v))
    )
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")
