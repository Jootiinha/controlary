"""Rótulos de valor (R$) em elementos de gráfico matplotlib."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any, Sequence

from matplotlib.axes import Axes

from app.utils.formatting import format_currency


def annotate_bars(
    ax: Axes,
    bars,
    values: Sequence[float],
    *,
    fontsize: float = 8,
    dy: float = 2,
    skip_zero: bool = False,
    format_value: Callable[[float], str] | None = None,
) -> None:
    """Coloca o rótulo acima de cada barra (R$ por padrão)."""
    fmt = format_value or format_currency
    for bar, val in zip(bars, values):
        if skip_zero and val == 0:
            continue
        h = bar.get_height()
        ax.annotate(
            fmt(val),
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, dy),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=fontsize,
            clip_on=True,
        )


def annotate_line_points(
    ax: Axes,
    x: Sequence[Any],
    y: Sequence[float],
    *,
    fontsize: float = 7,
    dy: float = 8,
    skip_zero: bool = False,
    clip_on: bool = False,
) -> None:
    """Anota cada ponto (x, y) com o valor em R$."""
    for xi, yi in zip(x, y):
        if skip_zero and yi == 0:
            continue
        ax.annotate(
            format_currency(yi),
            xy=(xi, yi),
            xytext=(0, dy),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=fontsize,
            clip_on=clip_on,
        )
