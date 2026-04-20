"""Canvas matplotlib integrado ao Qt."""
from __future__ import annotations

from typing import Any, Callable

import matplotlib

matplotlib.use("QtAgg")  # garante backend Qt

import mplcursors
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Wedge
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from PySide6.QtWidgets import QSizePolicy

from app.utils.formatting import format_currency

_MIN_TITLE_PAD_PT = 18.0

HoverFormatFn = Callable[[Any, Any, int | None], str]


def _as_float(x: Any) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _style_hover_annotation(sel: mplcursors.Selection) -> None:
    ann = sel.annotation
    ann.set_fontsize(9)
    bbox = ann.get_bbox_patch()
    if bbox is not None:
        bbox.set(facecolor="white", alpha=0.95, edgecolor="#E5E7EB", linewidth=0.8)


def _default_hover_text(ax, sel: mplcursors.Selection) -> str:
    artist = sel.artist
    custom: HoverFormatFn | None = getattr(ax, "_hover_format", None)
    if callable(custom):
        out = custom(artist, sel.target, sel.index)
        if out:
            return out

    if isinstance(artist, Rectangle):
        return format_currency(_as_float(artist.get_height()))

    if isinstance(artist, Line2D):
        targ = sel.target
        if hasattr(targ, "__len__") and len(targ) >= 2:
            _, y = targ[0], targ[1]
        else:
            y = targ
        yf = _as_float(y)
        lab = artist.get_label()
        if lab and not lab.startswith("_"):
            return f"{lab}\n{format_currency(yf)}"
        idx = sel.index
        xlabels = [t.get_text() for t in ax.get_xticklabels()]
        if idx is not None and 0 <= int(idx) < len(xlabels) and xlabels[int(idx)]:
            return f"{xlabels[int(idx)]}\n{format_currency(yf)}"
        return format_currency(yf)

    if isinstance(artist, Wedge):
        wedges = [p for p in ax.patches if isinstance(p, Wedge)]
        if artist in wedges:
            total = sum(w.theta2 - w.theta1 for w in wedges) or 1.0
            frac = (artist.theta2 - artist.theta1) / total
            return f"{frac * 100:.1f}%"
        return ""

    return ""


def _collect_hover_artists(ax) -> list[Any]:
    out: list[Any] = []
    out.extend(ax.containers)
    out.extend(ax.lines)
    for p in ax.patches:
        if isinstance(p, Wedge):
            out.append(p)
    return out


def _ensure_title_spacing(ax: Axes, *, min_pad_pt: float = _MIN_TITLE_PAD_PT) -> None:
    title_text = ax.get_title()
    if not title_text:
        return
    ttl = ax.title
    ax.set_title(
        title_text,
        fontsize=ttl.get_fontsize(),
        fontweight=ttl.get_fontweight(),
        color=ttl.get_color(),
        pad=min_pad_pt,
    )


class ChartCanvas(FigureCanvasQTAgg):
    def __init__(
        self,
        renderer: Callable[..., Any] | None = None,
        width: float = 6.0,
        height: float = 3.5,
        dpi: int = 100,
    ) -> None:
        # "constrained" evita cortar título/legendas como o tight_layout(rect=...) costumava fazer
        self._figure = Figure(figsize=(width, height), dpi=dpi, layout="constrained")
        self._figure.patch.set_facecolor("#FFFFFF")
        self._figure.get_layout_engine().set(h_pad=0.1, w_pad=0.055)
        super().__init__(self._figure)
        self.setMinimumSize(200, 160)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._renderer = renderer
        self._hover_cursor: mplcursors.Cursor | None = None
        if renderer is not None:
            self.refresh()

    def set_renderer(self, renderer: Callable[..., Any]) -> None:
        self._renderer = renderer

    def _remove_hover_cursor(self) -> None:
        if self._hover_cursor is not None:
            self._hover_cursor.remove()
            self._hover_cursor = None

    def _attach_hover_cursor(self, ax) -> None:
        self._remove_hover_cursor()
        artists = _collect_hover_artists(ax)
        if not artists:
            return

        cursor = mplcursors.cursor(
            artists,
            hover=mplcursors.HoverMode.Transient,
        )

        @cursor.connect("add")
        def on_add(sel: mplcursors.Selection) -> None:
            text = _default_hover_text(ax, sel)
            if text:
                sel.annotation.set(text=text)
            _style_hover_annotation(sel)

        self._hover_cursor = cursor

    def refresh(self) -> None:
        self._remove_hover_cursor()
        self._figure.clear()
        self._figure.get_layout_engine().set(h_pad=0.1, w_pad=0.055)
        ax = self._figure.add_subplot(111)
        ax.set_facecolor("#FFFFFF")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        if self._renderer is not None:
            self._renderer(ax)
            _ensure_title_spacing(ax)
        self._attach_hover_cursor(ax)
        self.draw_idle()
