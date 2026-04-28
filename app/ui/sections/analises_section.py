from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from app.ui.calendar_view import CalendarView
from app.ui.charts_view import ChartsView
from app.ui.history_view import HistoryView


class AnalisesSection(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("SectionTabs")
        self._cal = CalendarView()
        self._hist = HistoryView()
        self._charts = ChartsView()
        tabs = QTabWidget()
        tabs.addTab(self._cal, "Calendário")
        tabs.addTab(self._hist, "Histórico")
        tabs.addTab(self._charts, "Gráficos e análises")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(tabs)

    def reload(self) -> None:
        self._cal.reload()
        self._hist.reload()
        self._charts.reload()
