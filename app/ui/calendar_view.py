"""Calendário de pagamentos e compromissos do mês."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, QLocale, Qt
from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.services import calendar_service
from app.services.calendar_service import CalendarEvent
from app.utils.formatting import format_currency, format_date_br


_TIPO_LABEL = {
    "pagamento": "Pagamento",
    "renda": "Renda",
    "assinatura": "Assinatura",
    "fixo": "Gasto fixo",
    "parcela": "Parcelamento",
}


class CalendarView(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.lbl_title = QLabel("Calendário")
        self.lbl_title.setObjectName("PageTitle")
        self.lbl_subtitle = QLabel(
            "Pagamentos lançados, rendas, assinaturas, gastos fixos e parcelas. "
            "Parcelamentos usam o dia de pagamento da fatura definido no cartão."
        )
        self.lbl_subtitle.setObjectName("PageSubtitle")
        self.lbl_subtitle.setWordWrap(True)

        self.calendar = QCalendarWidget()
        self.calendar.setLocale(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))
        self.calendar.setGridVisible(True)
        self.calendar.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.lbl_day = QLabel("Selecione uma data")
        self.lbl_day.setObjectName("PageSubtitle")

        self.list_day = QListWidget()
        self.list_day.setMinimumHeight(160)
        self.list_day.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        detail = QWidget()
        detail_lay = QVBoxLayout(detail)
        detail_lay.setContentsMargins(0, 0, 0, 0)
        detail_lay.setSpacing(8)
        detail_lay.addWidget(self.lbl_day)
        detail_lay.addWidget(self.list_day, 1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.calendar)
        splitter.addWidget(detail)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        inner = QVBoxLayout(self)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(12)
        inner.addWidget(self.lbl_title)
        inner.addWidget(self.lbl_subtitle)
        inner.addWidget(splitter, 1)

        self._by_date: dict[date, list[CalendarEvent]] = {}
        self._fmt_highlight = QTextCharFormat()
        self._fmt_highlight.setBackground(QColor(200, 230, 255))
        self._fmt_normal = QTextCharFormat()

        self.calendar.currentPageChanged.connect(self._on_page_changed)
        self.calendar.selectionChanged.connect(self._on_selection_changed)

        self.reload()

    def _year_month(self) -> tuple[int, int]:
        return self.calendar.yearShown(), self.calendar.monthShown()

    def reload(self) -> None:
        y, m = self._year_month()
        self._by_date = calendar_service.events_by_date(y, m)
        self._apply_highlights(y, m)
        self._on_selection_changed()

    def _apply_highlights(self, ano: int, mes: int) -> None:
        from calendar import monthrange

        last = monthrange(ano, mes)[1]
        for d in range(1, last + 1):
            qd = QDate(ano, mes, d)
            self.calendar.setDateTextFormat(qd, self._fmt_normal)

        for ev_date in self._by_date:
            if ev_date.year != ano or ev_date.month != mes:
                continue
            qd = QDate(ev_date.year, ev_date.month, ev_date.day)
            self.calendar.setDateTextFormat(qd, self._fmt_highlight)

    def _on_page_changed(self, year: int, month: int) -> None:
        self._by_date = calendar_service.events_by_date(year, month)
        self._apply_highlights(year, month)
        self._on_selection_changed()

    def _py_date_selected(self) -> date:
        qd = self.calendar.selectedDate()
        return date(qd.year(), qd.month(), qd.day())

    def _on_selection_changed(self) -> None:
        d = self._py_date_selected()
        self.lbl_day.setText(format_date_br(d))
        self.list_day.clear()
        events = self._by_date.get(d, [])
        if not events:
            QListWidgetItem("Nada neste dia", self.list_day)
            return
        for ev in events:
            tipo = _TIPO_LABEL.get(ev.tipo, ev.tipo)
            line = f"{tipo} · {ev.titulo} — {format_currency(ev.valor)}"
            QListWidgetItem(line, self.list_day)
