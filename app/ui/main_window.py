"""Janela principal com sidebar de navegação."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.accounts_cards_view import AccountsCardsView
from app.ui.calendar_view import CalendarView
from app.ui.dashboard_view import DashboardView
from app.ui.fixed_expenses_view import FixedExpensesView
from app.ui.history_view import HistoryView
from app.ui.income_sources_view import IncomeSourcesView
from app.ui.installments_view import InstallmentsView
from app.ui.payments_view import PaymentsView
from app.ui.subscriptions_view import SubscriptionsView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Controle Financeiro")
        self.resize(1280, 860)
        self.setMinimumSize(960, 680)

        self.dashboard = DashboardView()
        self.income_sources = IncomeSourcesView()
        self.accounts_cards = AccountsCardsView()
        self.payments = PaymentsView()
        self.installments = InstallmentsView()
        self.subscriptions = SubscriptionsView()
        self.fixed_expenses = FixedExpensesView()
        self.calendar_page = CalendarView()
        self.history = HistoryView()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.income_sources)
        self.stack.addWidget(self.accounts_cards)
        self.stack.addWidget(self.payments)
        self.stack.addWidget(self.installments)
        self.stack.addWidget(self.subscriptions)
        self.stack.addWidget(self.fixed_expenses)
        self.stack.addWidget(self.calendar_page)
        self.stack.addWidget(self.history)

        self.sidebar = self._build_sidebar()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 980])
        self._splitter = splitter

        self.setCentralWidget(splitter)

        self._connect_data_changes()

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setMinimumWidth(168)
        sidebar.setMaximumWidth(400)

        title = QLabel("Controle\nFinanceiro")
        title.setObjectName("SidebarTitle")
        subtitle = QLabel("Gestão pessoal · SQLite local")
        subtitle.setObjectName("SidebarSubtitle")

        menu = QListWidget()
        menu.setObjectName("SidebarList")
        for label in (
            "Dashboard",
            "Renda",
            "Contas e cartões",
            "Pagamentos",
            "Parcelamentos",
            "Assinaturas",
            "Gastos fixos",
            "Calendário",
            "Histórico",
        ):
            QListWidgetItem(label, menu)
        menu.setCurrentRow(0)
        menu.currentRowChanged.connect(self._on_nav_change)
        self._menu = menu

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(menu, 1)
        return sidebar

    def _on_nav_change(self, row: int) -> None:
        self.stack.setCurrentIndex(row)
        widget = self.stack.currentWidget()
        if hasattr(widget, "reload"):
            widget.reload()

    def _connect_data_changes(self) -> None:
        """Recarrega dashboard/histórico e listas quando dados mudam."""

        def refresh_all():
            self.dashboard.reload()
            self.history.reload()
            self.calendar_page.reload()

        def refresh_lists():
            self.payments.reload()
            self.installments.reload()
            self.subscriptions.reload()
            self.fixed_expenses.reload()

        for view in (
            self.income_sources,
            self.payments,
            self.installments,
            self.subscriptions,
            self.fixed_expenses,
        ):
            if hasattr(view, "data_changed"):
                view.data_changed.connect(refresh_all)
                view.data_changed.connect(refresh_lists)

        self.accounts_cards.data_changed.connect(refresh_all)
        self.accounts_cards.data_changed.connect(refresh_lists)
        self.accounts_cards.data_changed.connect(self.accounts_cards.reload)
