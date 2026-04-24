"""Janela principal com sidebar de navegação."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSettings, QSize, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QPalette,
)
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMenuBar,
    QSplitter,
    QStackedWidget,
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
from app.ui.nav_icons import nav_icon
from app.ui.payments_view import PaymentsView
from app.ui.subscriptions_view import SubscriptionsView
from app.events import app_events
from app.ui.theme import THEME_DARK, THEME_LIGHT, apply_theme


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
        self.stack.setMinimumWidth(0)
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
        self._splitter = splitter
        splitter.setOpaqueResize(False)
        splitter.splitterMoved.connect(self._splitter_moved_maybe_sync)
        self._splitter_first_layout = QTimer(self)
        self._splitter_first_layout.setSingleShot(True)
        self._splitter_first_layout.timeout.connect(self._apply_initial_splitter_sizes)
        self._splitter_initial_sizes_done = False

        self.setCentralWidget(splitter)

        self._connect_app_events()
        self._setup_theme_menu()

    def _splitter_needs_sync(self) -> bool:
        splitter = self._splitter
        aw = splitter.width()
        if aw <= 1:
            return False
        s0, s1 = splitter.sizes()
        w0 = splitter.widget(0)
        w1 = splitter.widget(1)
        if abs(s0 + s1 - aw) > 1:
            return True
        if w0.geometry().x() < -1 or w1.geometry().x() < -1:
            return True
        return False

    def _sync_splitter_to_available_width(self) -> None:
        splitter = self._splitter
        aw = splitter.width()
        if aw <= 1:
            return
        w0 = splitter.widget(0)
        w1 = splitter.widget(1)
        min0 = max(1, w0.minimumWidth())
        min1 = max(0, w1.minimumWidth())
        if min0 + min1 > aw:
            return
        s0, s1 = splitter.sizes()
        geo0 = w0.geometry()
        if s0 + s1 == aw and geo0.x() >= 0 and w1.geometry().x() >= 0:
            return
        total = s0 + s1
        if total <= 0:
            target = getattr(self, "_sidebar_open_width", min0 + 40)
            left = max(min0, min(target, aw - min1))
        else:
            left = int(round(aw * (s0 / total)))
        left = max(min0, min(left, aw - min1))
        right = aw - left
        splitter.blockSignals(True)
        splitter.setSizes([left, right])
        splitter.blockSignals(False)

    def _splitter_moved_maybe_sync(self, _pos: int, _index: int) -> None:
        if self._splitter_needs_sync():
            self._sync_splitter_to_available_width()

    def _apply_initial_splitter_sizes(self) -> None:
        splitter = self._splitter
        aw = splitter.width()
        if aw <= 1:
            return
        left = max(
            self.sidebar.minimumWidth(),
            min(self._sidebar_open_width, aw - 320),
        )
        splitter.setSizes([left, aw - left])
        if self._splitter_needs_sync():
            self._sync_splitter_to_available_width()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._splitter_initial_sizes_done:
            self._splitter_initial_sizes_done = True
            self._splitter_first_layout.start(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._splitter_needs_sync():
            self._sync_splitter_to_available_width()

    def _nav_entries(
        self,
    ) -> list[tuple[str, list[tuple[str, int, str]]]]:
        """Grupos e itens (rótulo, índice no QStackedWidget, chave do ícone em nav_icons)."""
        return [
            (
                "Visão geral",
                [
                    ("Dashboard", 0, "dashboard"),
                    ("Calendário", 9, "calendar"),
                ],
            ),
            (
                "Movimento",
                [
                    ("Lançamentos", 4, "payments"),
                    ("Parcelamentos", 5, "installments"),
                    ("Assinaturas", 6, "subscriptions"),
                    ("Gastos fixos", 7, "fixed_expenses"),
                    ("Faturas de cartão", 8, "card_invoices"),
                ],
            ),
            (
                "Análise",
                [
                    ("Histórico", 10, "history"),
                    ("Gráficos e análises", 11, "charts"),
                    ("Investimentos", 12, "investments"),
                ],
            ),
            (
                "Cadastros",
                [
                    ("Contas e cartões", 2, "accounts"),
                    ("Categorias", 3, "categories"),
                    ("Renda", 1, "income"),
                ],
            ),
        ]

    def _sidebar_content_minimum_px(self) -> int:
        leaf_font = QFont(self.font())
        sec_font = QFont(leaf_font)
        sec_font.setPointSize(10)
        sec_font.setWeight(QFont.Weight.DemiBold)
        title_font = QFont(leaf_font)
        title_font.setPointSize(18)
        title_font.setWeight(QFont.Weight.DemiBold)
        sub_font = QFont(leaf_font)
        sub_font.setPointSize(11)
        mw = 0
        for group_name, items in self._nav_entries():
            mw = max(mw, QFontMetrics(sec_font).horizontalAdvance(group_name.upper()))
            for label, _, _ in items:
                mw = max(mw, QFontMetrics(leaf_font).horizontalAdvance(label))
        for line in ("Controle", "Financeiro"):
            mw = max(mw, QFontMetrics(title_font).horizontalAdvance(line))
        mw = max(
            mw,
            QFontMetrics(sub_font).horizontalAdvance(
                "Gestão pessoal · SQLite local"
            ),
        )
        tree_slack = 88
        return max(268, mw + tree_slack)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        content_px = self._sidebar_content_minimum_px()
        sidebar.setMinimumWidth(content_px)
        self._sidebar_open_width = content_px + 20

        title = QLabel("Controle\nFinanceiro")
        title.setObjectName("SidebarTitle")
        subtitle = QLabel("Gestão pessoal · SQLite local")
        subtitle.setObjectName("SidebarSubtitle")

        tree = QTreeWidget()
        tree.setObjectName("SidebarTree")
        tree.setHeaderHidden(True)
        tree.setIndentation(20)
        tree.setIconSize(QSize(20, 20))
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
            hdr.setData(0, Qt.ItemDataRole.UserRole, None)
            hdr.setSizeHint(0, QSize(0, 32))
            tree.addTopLevelItem(hdr)

            for label, stack_idx, icon_key in items:
                leaf = QTreeWidgetItem(hdr, [label])
                leaf.setIcon(0, nav_icon(icon_key, self.style()))
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
        self._apply_sidebar_section_muted()

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(tree, 1)
        return sidebar

    def _sidebar_section_muted_color(self) -> QColor:
        app = QApplication.instance()
        if app is None:
            return QColor("#9CA3AF")
        return app.palette().color(QPalette.ColorRole.PlaceholderText)

    def _apply_sidebar_section_muted(self) -> None:
        brush = QBrush(self._sidebar_section_muted_color())
        for i in range(self._nav_tree.topLevelItemCount()):
            sec = self._nav_tree.topLevelItem(i)
            if sec.data(0, Qt.ItemDataRole.UserRole) is None:
                sec.setForeground(0, brush)

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

    def _connect_app_events(self) -> None:
        ev = app_events()

        def refresh_all() -> None:
            self.dashboard.reload()
            self.history.reload()
            self.charts_view.reload()
            self.calendar_page.reload()
            self.investments.reload()

        def refresh_lists() -> None:
            self.payments.reload()
            self.installments.reload()
            self.subscriptions.reload()
            self.fixed_expenses.reload()
            self.card_invoices.reload()
            self.income_sources.reload()

        def on_domain_change() -> None:
            refresh_all()
            refresh_lists()

        def on_accounts_change() -> None:
            refresh_all()
            refresh_lists()
            self.accounts_cards.reload()

        for sig in (
            ev.payments_changed,
            ev.income_changed,
            ev.installments_changed,
            ev.subscriptions_changed,
            ev.fixed_changed,
            ev.categories_changed,
            ev.card_invoices_changed,
        ):
            sig.connect(on_domain_change)

        ev.accounts_changed.connect(on_accounts_change)
        ev.investments_changed.connect(refresh_all)

    def _setup_theme_menu(self) -> None:
        bar = QMenuBar(self)
        self.setMenuBar(bar)
        menu = bar.addMenu("Exibir")

        self._act_theme_light = QAction("Tema claro", self)
        self._act_theme_light.setCheckable(True)
        self._act_theme_dark = QAction("Tema escuro", self)
        self._act_theme_dark.setCheckable(True)
        group = QActionGroup(self)
        group.setExclusive(True)
        group.addAction(self._act_theme_light)
        group.addAction(self._act_theme_dark)
        menu.addAction(self._act_theme_light)
        menu.addAction(self._act_theme_dark)
        group.triggered.connect(self._on_theme_menu)

        stored = QSettings().value("ui/theme", THEME_LIGHT)
        if stored == THEME_DARK:
            self._act_theme_dark.setChecked(True)
        else:
            self._act_theme_light.setChecked(True)

    def _on_theme_menu(self, action: QAction) -> None:
        app = QApplication.instance()
        if app is None:
            return
        theme = THEME_DARK if action is self._act_theme_dark else THEME_LIGHT
        apply_theme(app, theme)
        QSettings().setValue("ui/theme", theme)
        self._apply_sidebar_section_muted()
