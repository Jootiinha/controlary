"""Card de KPI usado no dashboard."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class KpiCard(QFrame):
    def __init__(
        self,
        title: str,
        value: str = "-",
        subtitle: str = "",
        *,
        compact: bool = False,
    ) -> None:
        super().__init__()
        self.setObjectName("KpiCardCompact" if compact else "KpiCard")
        self.setFrameShape(QFrame.StyledPanel)

        self._title = QLabel(title)
        self._title.setObjectName("KpiTitle")

        self._value = QLabel(value)
        self._value.setObjectName("KpiValue")
        self._value.setWordWrap(True)

        self._subtitle = QLabel(subtitle)
        self._subtitle.setObjectName("KpiSubtitle")
        self._subtitle.setWordWrap(True)

        layout = QVBoxLayout(self)
        m = 10 if compact else 16
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(2)
        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addWidget(self._subtitle)
        layout.addStretch()

    def set_value(self, value: str) -> None:
        self._value.setText(value)

    def set_subtitle(self, subtitle: str) -> None:
        self._subtitle.setText(subtitle)
