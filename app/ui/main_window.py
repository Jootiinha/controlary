"""Janela principal com sidebar de navegação."""
from __future__ import annotations

from collections.abc import Callable
from typing import Optional

from functools import partial

from PySide6.QtCore import QSettings, QSize, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QKeySequence,
    QPalette,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMenuBar,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.events import app_events
from app.ui.categories_view import CategoriesView
from app.ui.dashboard_view import DashboardView
from app.ui.income_sources_view import IncomeSourcesView
from app.ui.nav_icons import nav_icon
from app.ui.sections.analises_section import AnalisesSection
from app.ui.sections.cartoes_section import CartoesSection
from app.ui.sections.contas_section import ContasSection
from app.ui.sections.despesas_section import DespesasSection
from app.ui.sections.investimentos_section import InvestimentosSection
from app.ui.theme import THEME_DARK, THEME_LIGHT, apply_theme
from app.ui.ui_feedback import register_toast_handler
from app.ui.widgets.command_palette import CommandPaletteDialog
from app.ui.widgets.nova_despesa_wizard import open_nova_despesa_flow
from app.ui.widgets.toast import Toast


class MainWindow(QMainWindow):
    IDX_DASHBOARD = 0
    IDX_DESPESAS = 1
    IDX_RECEITAS = 2
    IDX_CARTOES = 3
    IDX_CONTAS = 4
    IDX_INVEST = 5
    IDX_ANALISES = 6
    IDX_CATEGORIES = 7

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Controle Financeiro")
        self.resize(1280, 860)
        self.setMinimumSize(960, 680)

        self.dashboard = DashboardView()
        self.section_despesas = DespesasSection()
        self.income_sources = IncomeSourcesView()
        self.section_cartoes = CartoesSection()
        self.section_contas = ContasSection()
        self.section_invest = InvestimentosSection()
        self.section_analises = AnalisesSection()
        self.categories = CategoriesView()

        self.stack = QStackedWidget()
        self.stack.setMinimumWidth(0)
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.section_despesas)
        self.stack.addWidget(self.income_sources)
        self.stack.addWidget(self.section_cartoes)
        self.stack.addWidget(self.section_contas)
        self.stack.addWidget(self.section_invest)
        self.stack.addWidget(self.section_analises)
        self.stack.addWidget(self.categories)

        self._nav_index_to_item: dict[int, QTreeWidgetItem] = {}
        self._sidebar_collapsed = False
        self.sidebar = self._build_sidebar()

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.addWidget(self.sidebar)
        self._splitter.addWidget(self.stack)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setOpaqueResize(False)
        self._splitter.splitterMoved.connect(self._splitter_moved_maybe_sync)
        self._splitter_first_layout = QTimer(self)
        self._splitter_first_layout.setSingleShot(True)
        self._splitter_first_layout.timeout.connect(self._apply_initial_splitter_sizes)
        self._splitter_initial_sizes_done = False

        central = QWidget()
        central_lay = QVBoxLayout(central)
        central_lay.setContentsMargins(0, 0, 0, 0)
        central_lay.setSpacing(0)
        self._toolbar = QToolBar()
        self._toolbar.setObjectName("MainToolBar")
        self._toolbar.setMovable(False)
        act_nova = self._toolbar.addAction("+ Nova despesa")
        act_nova.triggered.connect(self._nova_despesa)
        act_nova.setToolTip("Registrar despesa avulsa, parcelada, assinatura ou fixa (Ctrl+N)")
        central_lay.addWidget(self._toolbar)
        central_lay.addWidget(self._splitter, 1)
        self.setCentralWidget(central)

        self._connect_app_events()
        self._setup_menus()
        self._setup_shortcuts()
        register_toast_handler(self._toast_dispatch)

    def _toast_dispatch(
        self,
        message: str,
        action_label: str | None,
        on_action: Callable[[], None] | None,
    ) -> None:
        self.show_toast(message, action_label=action_label, on_action=on_action)

    def show_toast(
        self,
        message: str,
        *,
        action_label: str | None = None,
        on_action: Callable[[], None] | None = None,
    ) -> None:
        t = Toast(
            self.stack,
            message,
            action_label=action_label,
            on_action=on_action,
        )
        t.adjustSize()
        self._position_toast(t)
        t.show()
        t.raise_()

    def _position_toast(self, t: Toast) -> None:
        m = 16
        x = max(m, self.stack.width() - t.width() - m)
        y = max(m, self.stack.height() - t.height() - m)
        t.move(x, y)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._splitter_needs_sync():
            self._sync_splitter_to_available_width()
        for ch in self.stack.findChildren(Toast):
            self._position_toast(ch)

    def _nova_despesa(self) -> None:
        open_nova_despesa_flow(self, show_toast=lambda m: self.show_toast(m))

    def _command_palette(self) -> None:
        acts: list[tuple[str, str, Callable[[], None]]] = [
            ("dash", "Ir para Início", lambda: self._goto_page(self.IDX_DASHBOARD)),
            ("desp", "Ir para Despesas", lambda: self._goto_page(self.IDX_DESPESAS)),
            ("rec", "Ir para Receitas", lambda: self._goto_page(self.IDX_RECEITAS)),
            ("cart", "Ir para Cartões", lambda: self._goto_page(self.IDX_CARTOES)),
            ("cont", "Ir para Contas", lambda: self._goto_page(self.IDX_CONTAS)),
            ("inv", "Ir para Investimentos", lambda: self._goto_page(self.IDX_INVEST)),
            ("ana", "Ir para Análises", lambda: self._goto_page(self.IDX_ANALISES)),
            ("cat", "Abrir Categorias", self._open_categories_page),
            ("nova", "Nova despesa…", self._nova_despesa),
        ]
        CommandPaletteDialog(self, acts).exec()

    def _open_categories_page(self) -> None:
        self._goto_page(self.IDX_CATEGORIES)

    def _goto_page(self, idx: int) -> None:
        self.stack.setCurrentIndex(idx)
        w = self.stack.currentWidget()
        if hasattr(w, "reload"):
            w.reload()
        it = self._nav_index_to_item.get(idx)
        if it is not None and hasattr(self, "_nav_tree"):
            self._nav_tree.blockSignals(True)
            self._nav_tree.setCurrentItem(it)
            self._nav_tree.blockSignals(False)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence.StandardKey.New, self, self._nova_despesa)
        QShortcut(QKeySequence("Ctrl+K"), self, self._command_palette)
        for n in range(1, 8):
            QShortcut(
                QKeySequence(f"Ctrl+{n}"),
                self,
                partial(self._goto_page, n - 1),
            )

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

    def _nav_entries(
        self,
    ) -> list[tuple[str, list[tuple[str, int, str]]]]:
        return [
            (
                "Principal",
                [
                    ("Início", self.IDX_DASHBOARD, "dashboard"),
                    ("Despesas", self.IDX_DESPESAS, "payments"),
                    ("Receitas", self.IDX_RECEITAS, "income"),
                    ("Cartões", self.IDX_CARTOES, "card_invoices"),
                    ("Contas", self.IDX_CONTAS, "accounts"),
                    ("Investimentos", self.IDX_INVEST, "investments"),
                    ("Análises", self.IDX_ANALISES, "charts"),
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
                self._nav_index_to_item[stack_idx] = leaf

        tree.expandAll()
        first_leaf = tree.topLevelItem(0).child(0)
        tree.setCurrentItem(first_leaf)
        tree.currentItemChanged.connect(self._on_tree_nav_changed)
        tree.itemClicked.connect(self._on_tree_item_clicked)
        self._nav_tree = tree
        self._apply_sidebar_section_muted()

        self._icon_bar = QWidget()
        ib_lay = QVBoxLayout(self._icon_bar)
        ib_lay.setContentsMargins(4, 8, 4, 8)
        ib_lay.setSpacing(4)
        for _g, items in self._nav_entries():
            for label, stack_idx, icon_key in items:
                tb = QToolButton()
                tb.setIcon(nav_icon(icon_key, self.style()))
                tb.setToolTip(label)
                tb.setAutoRaise(True)
                tb.clicked.connect(
                    lambda checked=False, i=stack_idx: self._goto_page_from_icon(i)
                )
                ib_lay.addWidget(tb)
        ib_lay.addStretch()
        self._icon_bar.hide()

        self._btn_sidebar_toggle = QToolButton()
        self._btn_sidebar_toggle.setObjectName("SidebarToggle")
        self._btn_sidebar_toggle.setText("«")
        self._btn_sidebar_toggle.setToolTip("Recolher barra lateral")
        self._btn_sidebar_toggle.clicked.connect(self._toggle_sidebar_collapsed)

        top_row = QWidget()
        tr = QVBoxLayout(top_row)
        tr.setContentsMargins(0, 0, 0, 0)
        tr.setSpacing(0)
        h = QWidget()
        hl = QVBoxLayout(h)
        hl.setContentsMargins(12, 8, 12, 0)
        hl.addWidget(self._btn_sidebar_toggle, 0, Qt.AlignmentFlag.AlignRight)
        tr.addWidget(h)
        tr.addWidget(title)
        tr.addWidget(subtitle)
        tr.addWidget(tree, 1)
        tr.addWidget(self._icon_bar, 1)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(top_row)
        self._sidebar_title = title
        self._sidebar_subtitle = subtitle
        self._sidebar_tree_widget = tree
        return sidebar

    def _goto_page_from_icon(self, idx: int) -> None:
        self._goto_page(idx)

    def _toggle_sidebar_collapsed(self) -> None:
        self._sidebar_collapsed = not self._sidebar_collapsed
        if self._sidebar_collapsed:
            self._sidebar_tree_widget.hide()
            self._icon_bar.show()
            self._sidebar_title.hide()
            self._sidebar_subtitle.hide()
            self.sidebar.setMinimumWidth(72)
            self._btn_sidebar_toggle.setText("»")
            self._btn_sidebar_toggle.setToolTip("Expandir barra lateral")
        else:
            self._icon_bar.hide()
            self._sidebar_tree_widget.show()
            self._sidebar_title.show()
            self._sidebar_subtitle.show()
            content_px = self._sidebar_content_minimum_px()
            self.sidebar.setMinimumWidth(content_px)
            self._btn_sidebar_toggle.setText("«")
            self._btn_sidebar_toggle.setToolTip("Recolher barra lateral")
        self._sync_splitter_to_available_width()

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
            self.section_analises.reload()
            self.section_invest.reload()

        def refresh_lists() -> None:
            self.section_despesas.reload()
            self.income_sources.reload()
            self.section_cartoes.reload()
            self.section_contas.reload()
            self.categories.reload()

        def on_domain_change() -> None:
            refresh_all()
            refresh_lists()

        def on_accounts_change() -> None:
            refresh_all()
            refresh_lists()

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
        ev.investment_goals_changed.connect(refresh_all)

    def _setup_menus(self) -> None:
        bar = QMenuBar(self)
        self.setMenuBar(bar)
        view_menu = bar.addMenu("Exibir")
        self._act_theme_light = QAction("Tema claro", self)
        self._act_theme_light.setCheckable(True)
        self._act_theme_dark = QAction("Tema escuro", self)
        self._act_theme_dark.setCheckable(True)
        group = QActionGroup(self)
        group.setExclusive(True)
        group.addAction(self._act_theme_light)
        group.addAction(self._act_theme_dark)
        view_menu.addAction(self._act_theme_light)
        view_menu.addAction(self._act_theme_dark)
        group.triggered.connect(self._on_theme_menu)

        self._act_density_comfort = QAction("Densidade: confortável", self)
        self._act_density_comfort.setCheckable(True)
        self._act_density_compact = QAction("Densidade: compacta", self)
        self._act_density_compact.setCheckable(True)
        dg = QActionGroup(self)
        dg.setExclusive(True)
        dg.addAction(self._act_density_comfort)
        dg.addAction(self._act_density_compact)
        view_menu.addSeparator()
        view_menu.addAction(self._act_density_comfort)
        view_menu.addAction(self._act_density_compact)
        dg.triggered.connect(self._on_density_menu)

        self._act_font_normal = QAction("Tamanho da fonte: padrão", self)
        self._act_font_normal.setCheckable(True)
        self._act_font_large = QAction("Tamanho da fonte: maior", self)
        self._act_font_large.setCheckable(True)
        fg = QActionGroup(self)
        fg.setExclusive(True)
        fg.addAction(self._act_font_normal)
        fg.addAction(self._act_font_large)
        view_menu.addSeparator()
        view_menu.addAction(self._act_font_normal)
        view_menu.addAction(self._act_font_large)
        fg.triggered.connect(self._on_font_menu)

        cad = bar.addMenu("Cadastros")
        cad.addAction("Categorias…", self._open_categories_page)

        stored = QSettings().value("ui/theme", THEME_LIGHT)
        if stored == THEME_DARK:
            self._act_theme_dark.setChecked(True)
        else:
            self._act_theme_light.setChecked(True)

        dens = QSettings().value("ui/density", "comfortable")
        if dens == "compact":
            self._act_density_compact.setChecked(True)
        else:
            self._act_density_comfort.setChecked(True)

        fs = QSettings().value("ui/font_scale", "normal")
        if fs == "large":
            self._act_font_large.setChecked(True)
        else:
            self._act_font_normal.setChecked(True)

    def _on_density_menu(self, action: QAction) -> None:
        d = "compact" if action is self._act_density_compact else "comfortable"
        QSettings().setValue("ui/density", d)
        self._reapply_theme()

    def _on_font_menu(self, action: QAction) -> None:
        s = "large" if action is self._act_font_large else "normal"
        QSettings().setValue("ui/font_scale", s)
        self._reapply_theme()

    def _reapply_theme(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        theme = QSettings().value("ui/theme", THEME_LIGHT)
        if theme not in (THEME_LIGHT, THEME_DARK):
            theme = THEME_LIGHT
        apply_theme(app, theme)
        self._apply_sidebar_section_muted()

    def _on_theme_menu(self, action: QAction) -> None:
        app = QApplication.instance()
        if app is None:
            return
        theme = THEME_DARK if action is self._act_theme_dark else THEME_LIGHT
        apply_theme(app, theme)
        QSettings().setValue("ui/theme", theme)
        self._apply_sidebar_section_muted()
