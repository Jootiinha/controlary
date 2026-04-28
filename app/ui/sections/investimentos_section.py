from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from app.ui.investment_goals_view import InvestmentGoalsView
from app.ui.investments_view import InvestmentsView


class InvestimentosSection(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("SectionTabs")
        self._inv = InvestmentsView()
        self._goals = InvestmentGoalsView()
        tabs = QTabWidget()
        tabs.addTab(self._inv, "Posições")
        tabs.addTab(self._goals, "Metas")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(tabs)

    def reload(self) -> None:
        self._inv.reload()
        self._goals.reload()
