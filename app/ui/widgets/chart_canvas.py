"""Canvas matplotlib integrado ao Qt."""
from __future__ import annotations

from typing import Callable

import matplotlib
matplotlib.use("QtAgg")  # garante backend Qt

from PySide6.QtWidgets import QSizePolicy

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402


class ChartCanvas(FigureCanvasQTAgg):
    def __init__(self, renderer: Callable | None = None, width: float = 6.0,
                 height: float = 3.5, dpi: int = 100) -> None:
        self._figure = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self._figure.patch.set_facecolor("#FFFFFF")
        super().__init__(self._figure)
        self.setMinimumSize(200, 160)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._renderer = renderer
        if renderer is not None:
            self.refresh()

    def set_renderer(self, renderer: Callable) -> None:
        self._renderer = renderer

    def refresh(self) -> None:
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor("#FFFFFF")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        if self._renderer is not None:
            self._renderer(ax)
        self._figure.tight_layout(pad=1.15, h_pad=0.9, w_pad=0.8)
        self.draw_idle()
