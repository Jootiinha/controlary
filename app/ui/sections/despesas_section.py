from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from app.ui.fixed_expenses_view import FixedExpensesView
from app.ui.installments_view import InstallmentsView
from app.ui.payments_view import PaymentsView
from app.ui.subscriptions_view import SubscriptionsView


class DespesasSection(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("SectionTabs")
        self._payments = PaymentsView()
        self._installments = InstallmentsView()
        self._subscriptions = SubscriptionsView()
        self._fixed = FixedExpensesView()
        tabs = QTabWidget()
        tabs.addTab(self._payments, "Despesas avulsas")
        tabs.addTab(self._installments, "Despesas parceladas")
        tabs.addTab(self._subscriptions, "Assinaturas")
        tabs.addTab(self._fixed, "Despesas fixas")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(tabs)

    def reload(self) -> None:
        self._payments.reload()
        self._installments.reload()
        self._subscriptions.reload()
        self._fixed.reload()
