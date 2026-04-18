"""Distribuição do valor aplicado por tipo de investimento."""
from __future__ import annotations

from typing import Any

from matplotlib.patches import Wedge

from app.services import investments_service
from app.utils.formatting import format_currency


def fetch_data() -> list[tuple[str, float]]:
    out: dict[str, float] = {}
    for inv in investments_service.list_all():
        t = inv.tipo or "Outros"
        out[t] = out.get(t, 0.0) + float(inv.valor_aplicado)
    items = [(k, v) for k, v in out.items() if v > 0]
    items.sort(key=lambda x: x[1], reverse=True)
    return items


def plot(ax) -> None:
    data = fetch_data()
    if not data:
        ax.text(0.5, 0.5, "Sem investimentos ativos", ha="center", va="center")
        ax.set_axis_off()
        return
    labels = [d[0] for d in data]
    values = [d[1] for d in data]
    total = sum(values)

    def autopct_fmt(pct: float) -> str:
        val = pct * total / 100.0
        return f"{pct:.1f}%\n{format_currency(val)}"

    ax.pie(
        values,
        autopct=autopct_fmt,
        startangle=90,
        textprops={"fontsize": 8},
    )
    ax.legend(
        labels,
        title="Tipo",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=8,
    )
    ax.set_title("Investimentos ativos por tipo (valor aplicado)")

    def _hover_format(artist: Any, target: Any, index: int | None) -> str:
        if not isinstance(artist, Wedge):
            return ""
        idx = int(index) if index is not None else None
        if idx is None:
            wedges = [p for p in ax.patches if isinstance(p, Wedge)]
            try:
                idx = wedges.index(artist)
            except ValueError:
                return ""
        if not (0 <= idx < len(labels)):
            return ""
        val = values[idx]
        lbl = labels[idx]
        pct = 100.0 * val / total if total else 0.0
        return f"{lbl}\n{format_currency(val)}\n({pct:.1f}% do total)"

    ax._hover_format = _hover_format
