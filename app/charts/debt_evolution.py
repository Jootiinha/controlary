"""Gráfico de evolução do saldo devedor (passado linear + futuro com parcelas pagas)."""
from __future__ import annotations

from datetime import date

from matplotlib.ticker import FuncFormatter

from app.charts.cards_window import cards_window, diff_months
from app.charts.plot_labels import annotate_line_points
from app.models.installment import Installment
from app.services import installments_service
from app.utils.formatting import format_currency_short


def _saldo_em_mes(m: str, current_ym: str, ativos: list[Installment]) -> float:
    """Passado: aproximação linear; futuro e mês atual: usa ``parcelas_pagas``."""
    total = 0.0
    for inst in ativos:
        if m < inst.mes_referencia:
            continue
        if m < current_ym:
            decorridos = diff_months(inst.mes_referencia, m) + 1
            decorridos = min(decorridos, inst.total_parcelas)
            restantes = max(0, inst.total_parcelas - decorridos)
        else:
            i = diff_months(current_ym, m)
            restantes = max(inst.total_parcelas - inst.parcelas_pagas - i, 0)
        total += float(inst.valor_parcela) * restantes
    return round(total, 2)


def fetch_data(current_ym: str | None = None) -> list[tuple[str, float]]:
    """Uma entrada por mês na janela comum (6 passados + atual + 12 futuros)."""
    if current_ym is None:
        today = date.today()
        current_ym = f"{today.year:04d}-{today.month:02d}"

    ativos = [i for i in installments_service.list_all() if i.status == "ativo"]
    if not ativos:
        return []

    meses = cards_window(current_ym)
    return [(m, _saldo_em_mes(m, current_ym, ativos)) for m in meses]


def plot(ax) -> None:
    today = date.today()
    current_ym = f"{today.year:04d}-{today.month:02d}"

    data = fetch_data(current_ym)
    if not data:
        ax.text(0.5, 0.5, "Sem parcelamentos ativos", ha="center", va="center")
        ax.set_axis_off()
        return
    meses = [d[0] for d in data]
    valores = [d[1] for d in data]
    ax.plot(meses, valores, marker="s", color="#DC2626", linewidth=2)
    ax.fill_between(meses, valores, alpha=0.15, color="#DC2626")
    annotate_line_points(ax, meses, valores, fontsize=7, dy=7)

    if current_ym in meses:
        ax.axvline(current_ym, color="#9CA3AF", linewidth=0.9, linestyle=":")

    ax.set_title(
        "Saldo devedor (6 passados · 12 futuros)",
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
