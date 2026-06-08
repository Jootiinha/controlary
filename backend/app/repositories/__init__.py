"""Repositories package for data access."""

from app.repositories.accounts_repo import AccountsRepository
from app.repositories.cards_repo import CardsRepository
from app.repositories.payments_repo import PaymentsRepository
from app.repositories.subscriptions_repo import SubscriptionsRepository
from app.repositories.categories_repo import CategoriesRepository
from app.repositories.fixed_expenses_repo import FixedExpensesRepository
from app.repositories.installments_repo import InstallmentsRepository
from app.repositories.income_sources_repo import IncomeSourcesRepository
from app.repositories.card_invoices_repo import CardInvoicesRepository
from app.repositories.investments_repo import InvestmentsRepository

__all__ = [
    "AccountsRepository",
    "CardsRepository",
    "PaymentsRepository",
    "SubscriptionsRepository",
    "CategoriesRepository",
    "FixedExpensesRepository",
    "InstallmentsRepository",
    "IncomeSourcesRepository",
    "CardInvoicesRepository",
    "InvestmentsRepository",
]
