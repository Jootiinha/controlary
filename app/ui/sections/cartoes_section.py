from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from app.ui.accounts_cards_view import CardsCrudView
from app.ui.card_invoices_view import CardInvoicesView


class CartoesSection(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("SectionTabs")
        self._invoices = CardInvoicesView()
        self._cards = CardsCrudView()
        tabs = QTabWidget()
        tabs.addTab(self._invoices, "Faturas")
        tabs.addTab(self._cards, "Cadastro de cartões")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(tabs)

    def reload(self) -> None:
        self._invoices.reload()
        self._cards.reload()
