"""Eventos de domínio para sincronizar UI sem acoplamento direto entre views."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class AppEvents(QObject):
    payments_changed = Signal()
    income_changed = Signal()
    installments_changed = Signal()
    subscriptions_changed = Signal()
    fixed_changed = Signal()
    card_invoices_changed = Signal()
    accounts_changed = Signal()
    categories_changed = Signal()
    investments_changed = Signal()
    investment_goals_changed = Signal()

    _instance: AppEvents | None = None

    @classmethod
    def instance(cls) -> AppEvents:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def app_events() -> AppEvents:
    return AppEvents.instance()
