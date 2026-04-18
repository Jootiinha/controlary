"""Card de KPI usado no dashboard."""
from __future__ import annotations

from typing import Literal

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


# Dimensões dos KPI compactos no dashboard. A altura é fixa (uniformidade visual),
# mas a largura cresce para ocupar toda a faixa disponível — com um mínimo razoável.
_KPI_COMPACT_MIN_W = 168
_KPI_COMPACT_H = 112
_KPI_SUBTITLE_MAX_LINES = 2


class _ElidedLabel(QLabel):
    """Label com word-wrap até N linhas e elide com '…' na última."""

    def __init__(self, text: str = "", max_lines: int = 2) -> None:
        super().__init__(text)
        self._full_text = text
        self._max_lines = max_lines
        self.setWordWrap(True)

    def setText(self, text: str) -> None:  # noqa: D401 - override
        self._full_text = text or ""
        super().setText(self._full_text)
        self._apply_elide()

    def resizeEvent(self, event) -> None:  # noqa: D401 - override
        super().resizeEvent(event)
        self._apply_elide()

    def _apply_elide(self) -> None:
        if not self._full_text:
            return
        fm = QFontMetrics(self.font())
        width = max(1, self.width())
        # Quebra greedy por palavras; corta ao atingir max_lines e elide na última.
        words = self._full_text.split()
        lines: list[str] = []
        current = ""
        for w in words:
            candidate = f"{current} {w}".strip()
            if fm.horizontalAdvance(candidate) <= width:
                current = candidate
                continue
            if current:
                lines.append(current)
            if len(lines) == self._max_lines:
                break
            current = w
        if current and len(lines) < self._max_lines:
            lines.append(current)
        if len(lines) == self._max_lines:
            remaining = self._full_text
            consumed = " ".join(lines[:-1])
            if consumed:
                remaining = self._full_text[len(consumed):].lstrip()
            last = fm.elidedText(remaining, Qt.TextElideMode.ElideRight, width)
            lines[-1] = last
        super().setText("\n".join(lines) if lines else self._full_text)


class KpiCard(QFrame):
    def __init__(
        self,
        title: str,
        value: str = "-",
        subtitle: str = "",
        *,
        compact: bool = False,
        compact_style: Literal["default", "tall_narrow"] = "default",
    ) -> None:
        super().__init__()
        self.setObjectName("KpiCardCompact" if compact else "KpiCard")
        self.setFrameShape(QFrame.StyledPanel)

        self._title = QLabel(title)
        self._title.setObjectName("KpiTitle")
        self._title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._title.setWordWrap(True)

        self._value = QLabel(value)
        self._value.setObjectName("KpiValue")
        self._value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._value.setWordWrap(False)

        if compact:
            self._subtitle: QLabel = _ElidedLabel(subtitle, max_lines=_KPI_SUBTITLE_MAX_LINES)
        else:
            self._subtitle = QLabel(subtitle)
            self._subtitle.setWordWrap(True)
        self._subtitle.setObjectName("KpiSubtitle")
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2 if compact else 8)
        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addWidget(self._subtitle)

        if compact and compact_style == "tall_narrow":
            self.setFixedHeight(128)
            self.setMinimumWidth(112)
            self.setSizePolicy(
                QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
            )
            self._title.setMinimumHeight(44)
            self._title.setMaximumHeight(56)
            self._title.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
            )
            self._value.setFixedHeight(26)
            if not (subtitle or "").strip():
                self._subtitle.hide()
                self._subtitle.setMaximumHeight(0)
            else:
                self._subtitle.setFixedHeight(28)
            layout.setSpacing(5)
            layout.setStretch(0, 0)
            layout.setStretch(1, 0)
            layout.setStretch(2, 0)
        elif compact:
            self.setFixedHeight(_KPI_COMPACT_H)
            self.setMinimumWidth(_KPI_COMPACT_MIN_W)
            self.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            self._title.setFixedHeight(16)
            self._value.setFixedHeight(24)
            self._subtitle.setFixedHeight(32)
            layout.setStretch(0, 0)
            layout.setStretch(1, 0)
            layout.setStretch(2, 1)
        else:
            self._value.setMinimumHeight(36)
            self.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred,
            )
            layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self._value.setText(value)

    def set_subtitle(self, subtitle: str) -> None:
        self._subtitle.setText(subtitle)
