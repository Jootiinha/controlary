"""Janela principal com sidebar de navegação."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QStyle,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.accounts_cards_view import AccountsCardsView
from app.ui.calendar_view import CalendarView
from app.ui.card_invoices_view import CardInvoicesView
from app.ui.categories_view import CategoriesView
from app.ui.charts_view import ChartsView
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
        self.charts_view = ChartsView()
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
        self.stack.addWidget(self.charts_view)
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

    def _nav_entries(
        self,
    ) -> list[tuple[str, list[tuple[str, int, QStyle.StandardPixmap]]]]:
        """Grupos e itens (rótulo, índice no QStackedWidget, ícone padrão Qt)."""
        return [
            (
                "Visão geral",
                [
                    (
                        "Dashboard",
                        0,
                        QStyle.StandardPixmap.SP_FileDialogDetailedView,
                    ),
                    (
                        "Calendário",
                        9,
                        QStyle.StandardPixmap.SP_FileDialogInfoView,
                    ),
                ],
            ),
            (
                "Movimento",
                [
                    (
                        "Lançamentos",
                        4,
                        QStyle.StandardPixmap.SP_DialogApplyButton,
                    ),
                    (
                        "Parcelamentos",
                        5,
                        QStyle.StandardPixmap.SP_FileDialogListView,
                    ),
                    (
                        "Assinaturas",
                        6,
                        QStyle.StandardPixmap.SP_BrowserReload,
                    ),
                    (
                        "Gastos fixos",
                        7,
                        QStyle.StandardPixmap.SP_DialogSaveButton,
                    ),
                    (
                        "Faturas de cartão",
                        8,
                        QStyle.StandardPixmap.SP_FileIcon,
                    ),
                ],
            ),
            (
                "Análise",
                [
                    (
                        "Histórico",
                        10,
                        QStyle.StandardPixmap.SP_FileDialogContentsView,
                    ),
                    (
                        "Gráficos e análises",
                        11,
                        QStyle.StandardPixmap.SP_FileDialogDetailedView,
                    ),
                    (
                        "Investimentos",
                        12,
                        QStyle.StandardPixmap.SP_ArrowUp,
                    ),
                ],
            ),
            (
                "Cadastros",
                [
                    (
                        "Contas e cartões",
                        2,
                        QStyle.StandardPixmap.SP_DriveHDIcon,
                    ),
                    (
                        "Categorias",
                        3,
                        QStyle.StandardPixmap.SP_DirIcon,
                    ),
                    (
                        "Renda",
                        1,
                        QStyle.StandardPixmap.SP_DialogYesButton,
                    ),
                ],
            ),
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

        tree = QTreeWidget()
        tree.setObjectName("SidebarTree")
        tree.setHeaderHidden(True)
        tree.setIndentation(16)
        tree.setRootIsDecorated(False)
        tree.setExpandsOnDoubleClick(False)
        tree.setAnimated(True)
        tree.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        header_font = QFont()
        header_font.setPointSize(10)
        header_font.setWeight(QFont.Weight.DemiBold)

        for group_name, items in self._nav_entries():
            hdr = QTreeWidgetItem([group_name.upper()])
            hdr.setFlags(Qt.ItemFlag.ItemIsEnabled)
            hdr.setExpanded(True)
            hdr.setFirstColumnSpanned(True)
            hdr.setFont(0, header_font)
            hdr.setForeground(0, QBrush(QColor("#9CA3AF")))
            hdr.setData(0, Qt.ItemDataRole.UserRole, None)
            hdr.setSizeHint(0, QSize(0, 36))
            tree.addTopLevelItem(hdr)

            for label, stack_idx, spix in items:
                leaf = QTreeWidgetItem(hdr, [label])
                leaf.setIcon(0, self.style().standardIcon(spix))
                leaf.setData(0, Qt.ItemDataRole.UserRole, stack_idx)
                leaf.setFlags(
                    Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
                )

        tree.expandAll()
        first_leaf = tree.topLevelItem(0).child(0)
        tree.setCurrentItem(first_leaf)
        tree.currentItemChanged.connect(self._on_tree_nav_changed)
        tree.itemClicked.connect(self._on_tree_item_clicked)
        self._nav_tree = tree

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(tree, 1)
        return sidebar

    def _on_tree_item_clicked(
        self, item: QTreeWidgetItem, column: int
    ) -> None:
        if item.childCount() > 0:
            item.setExpanded(not item.isExpanded())

    def _on_tree_nav_changed(
        self,
        current: Optional[QTreeWidgetItem],
        previous: Optional[QTreeWidgetItem],
    ) -> None:
        if current is None:
            return
        idx = current.data(0, Qt.ItemDataRole.UserRole)
        if idx is None:
            self._nav_tree.blockSignals(True)
            if previous is not None:
                self._nav_tree.setCurrentItem(previous)
            else:
                for i in range(self._nav_tree.topLevelItemCount()):
                    sec = self._nav_tree.topLevelItem(i)
                    if sec.childCount() > 0:
                        self._nav_tree.setCurrentItem(sec.child(0))
                        break
            self._nav_tree.blockSignals(False)
            return
        self.stack.setCurrentIndex(int(idx))
        widget = self.stack.currentWidget()
        if hasattr(widget, "reload"):
            widget.reload()

    def _connect_data_changes(self) -> None:
        def refresh_all():
            self.dashboard.reload()
            self.history.reload()
            self.charts_view.reload()
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
