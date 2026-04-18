"""Janela principal com sidebar de navegação."""
from __future__ import annotations

from typing import Optional

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
from app.ui.card_invoices_view import CardInvoicesView
from app.ui.categories_view import CategoriesView
from app.ui.dashboard_view import DashboardView
from app.ui.fixed_expenses_view import FixedExpensesView
from app.ui.history_view import HistoryView
from app.ui.income_sources_view import IncomeSourcesView
from app.ui.installments_view import InstallmentsView
from app.ui.investments_view import InvestmentsView
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
        self.categories = CategoriesView()
        self.payments = PaymentsView()
        self.installments = InstallmentsView()
        self.subscriptions = SubscriptionsView()
        self.fixed_expenses = FixedExpensesView()
        self.card_invoices = CardInvoicesView()
        self.calendar_page = CalendarView()
        self.history = HistoryView()
        self.investments = InvestmentsView()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.income_sources)
        self.stack.addWidget(self.accounts_cards)
        self.stack.addWidget(self.categories)
        self.stack.addWidget(self.payments)
        self.stack.addWidget(self.installments)
        self.stack.addWidget(self.subscriptions)
        self.stack.addWidget(self.fixed_expenses)
        self.stack.addWidget(self.card_invoices)
        self.stack.addWidget(self.calendar_page)
        self.stack.addWidget(self.history)
        self.stack.addWidget(self.investments)

        self.sidebar = self._build_sidebar()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 980])
        self._splitter = splitter

        self.setCentralWidget(splitter)

        self._connect_data_changes()

    def _nav_entries(self) -> list[tuple[str, Optional[int]]]:
        return [
            ("— Cadastros —", None),
            ("Contas e cartões", 2),
            ("Categorias", 3),
            ("Renda", 1),
            ("— Movimento —", None),
            ("Pagamentos", 4),
            ("Parcelamentos", 5),
            ("Assinaturas", 6),
            ("Gastos fixos", 7),
            ("Faturas de cartão", 8),
            ("— Análise —", None),
            ("Dashboard", 0),
            ("Calendário", 9),
            ("Histórico e análises", 10),
            ("Investimentos", 11),
        ]

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
        for label, stack_idx in self._nav_entries():
            it = QListWidgetItem(label)
            if stack_idx is None:
                it.setFlags(Qt.ItemFlag.ItemIsEnabled)
                it.setData(Qt.ItemDataRole.UserRole, None)
            else:
                it.setData(Qt.ItemDataRole.UserRole, stack_idx)
            menu.addItem(it)

        first_real = next(
            i for i in range(menu.count())
            if menu.item(i).data(Qt.ItemDataRole.UserRole) is not None
        )
        menu.setCurrentRow(first_real)
        menu.currentItemChanged.connect(self._on_nav_item_changed)
        self._menu = menu

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(menu, 1)
        return sidebar

    def _on_nav_item_changed(
        self,
        current: Optional[QListWidgetItem],
        previous: Optional[QListWidgetItem],
    ) -> None:
        if current is None:
            return
        idx = current.data(Qt.ItemDataRole.UserRole)
        if idx is None:
            self._menu.blockSignals(True)
            if previous is not None:
                self._menu.setCurrentItem(previous)
            else:
                for i in range(self._menu.count()):
                    it = self._menu.item(i)
                    if it.data(Qt.ItemDataRole.UserRole) is not None:
                        self._menu.setCurrentRow(i)
                        break
            self._menu.blockSignals(False)
            return
        self.stack.setCurrentIndex(int(idx))
        widget = self.stack.currentWidget()
        if hasattr(widget, "reload"):
            widget.reload()

    def _connect_data_changes(self) -> None:
        def refresh_all():
            self.dashboard.reload()
            self.history.reload()
            self.calendar_page.reload()
            self.investments.reload()

        def refresh_lists():
            self.payments.reload()
            self.installments.reload()
            self.subscriptions.reload()
            self.fixed_expenses.reload()
            self.card_invoices.reload()
            self.income_sources.reload()

        for view in (
            self.income_sources,
            self.payments,
            self.installments,
            self.subscriptions,
            self.fixed_expenses,
            self.categories,
        ):
            if hasattr(view, "data_changed"):
                view.data_changed.connect(refresh_all)
                view.data_changed.connect(refresh_lists)

        self.accounts_cards.data_changed.connect(refresh_all)
        self.accounts_cards.data_changed.connect(refresh_lists)
        self.accounts_cards.data_changed.connect(self.accounts_cards.reload)

        self.card_invoices.data_changed.connect(refresh_all)
        self.card_invoices.data_changed.connect(refresh_lists)

        self.investments.data_changed.connect(refresh_all)
