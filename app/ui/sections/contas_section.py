from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from app.ui.accounts_cards_view import AccountsCrudView
from app.ui.ledger_view import LedgerView


class ContasSection(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("SectionTabs")
        self._accounts = AccountsCrudView()
        self._ledger = LedgerView()
        tabs = QTabWidget()
        tabs.addTab(self._accounts, "Contas")
        tabs.addTab(self._ledger, "Livro-caixa")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(tabs)

    def reload(self) -> None:
        self._accounts.reload()
        self._ledger.reload()
