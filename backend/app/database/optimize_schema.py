"""Database schema optimization with indexes."""

from sqlalchemy import Index, event, text
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
import logging

logger = logging.getLogger(__name__)


def _execute_index(conn, sql: str, index_name: str):
    """Execute index creation with error handling."""
    try:
        conn.execute(text(sql))
    except Exception as e:
        logger.warning(f"Could not create index {index_name}: {e}")


def create_performance_indexes(engine: Engine):
    """Create indexes for performance optimization.

    Indexes are created on frequently queried columns:
    - user_id: Filter by user (multi-tenancy)
    - data/date columns: Range queries by date
    - status columns: Filter by status
    - foreign keys: Join optimization
    """

    # Get connection and create indexes
    with engine.begin() as conn:
        # Account Transactions indexes
        # Most queries filter by account_id, often with date range
        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_account_transactions_account_id
            ON account_transactions(account_id)
        """, "idx_account_transactions_account_id")

        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_account_transactions_data
            ON account_transactions(data)
        """, "idx_account_transactions_data")

        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_account_transactions_transaction_key
            ON account_transactions(transaction_key)
        """, "idx_account_transactions_transaction_key")

        # Payments indexes
        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_payments_user_id
            ON payments(user_id)
        """, "idx_payments_user_id")

        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_payments_account_id
            ON payments(account_id)
        """, "idx_payments_account_id")

        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_payments_card_id
            ON payments(card_id)
        """, "idx_payments_card_id")

        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_payments_user_date
            ON payments(user_id, data)
        """, "idx_payments_user_date")

        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_payments_user_is_paid
            ON payments(user_id, is_paid)
        """, "idx_payments_user_is_paid")

        # Subscriptions indexes
        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id
            ON subscriptions(user_id)
        """, "idx_subscriptions_user_id")

        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status
            ON subscriptions(user_id, status)
        """, "idx_subscriptions_user_status")

        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_subscriptions_account_id
            ON subscriptions(account_id)
        """, "idx_subscriptions_account_id")

        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_subscriptions_card_id
            ON subscriptions(card_id)
        """, "idx_subscriptions_card_id")

        # Cards indexes
        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_cards_user_id
            ON cards(user_id)
        """, "idx_cards_user_id")

        # Accounts indexes
        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_accounts_user_id
            ON accounts(user_id)
        """, "idx_accounts_user_id")

        # Categories indexes
        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_categories_user_id
            ON categories(user_id)
        """, "idx_categories_user_id")

        # Fixed Expenses indexes
        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_fixed_expenses_user_id
            ON fixed_expenses(user_id)
        """, "idx_fixed_expenses_user_id")

        # Income Sources indexes
        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_income_sources_user_id
            ON income_sources(user_id)
        """, "idx_income_sources_user_id")

        # Installments indexes
        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_installments_user_id
            ON installments(user_id)
        """, "idx_installments_user_id")

        # Card Invoices indexes
        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_card_invoices_card_id
            ON card_invoices(card_id)
        """, "idx_card_invoices_card_id")

        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_card_invoices_status
            ON card_invoices(status)
        """, "idx_card_invoices_status")

        # Investments indexes
        _execute_index(conn, """
            CREATE INDEX IF NOT EXISTS idx_investments_user_id
            ON investments(user_id)
        """, "idx_investments_user_id")


# Index definitions for future Alembic migrations
INDEXES_TO_CREATE = [
    # Account Transactions
    Index('idx_account_transactions_user_id', 'account_transactions.user_id'),
    Index('idx_account_transactions_account_id', 'account_transactions.account_id'),
    Index('idx_account_transactions_user_date', 'account_transactions.user_id', 'account_transactions.data'),
    Index('idx_account_transactions_transaction_key', 'account_transactions.transaction_key'),

    # Payments
    Index('idx_payments_user_id', 'payments.user_id'),
    Index('idx_payments_account_id', 'payments.account_id'),
    Index('idx_payments_card_id', 'payments.card_id'),
    Index('idx_payments_user_date', 'payments.user_id', 'payments.data'),
    Index('idx_payments_user_is_paid', 'payments.user_id', 'payments.is_paid'),

    # Subscriptions
    Index('idx_subscriptions_user_id', 'subscriptions.user_id'),
    Index('idx_subscriptions_user_status', 'subscriptions.user_id', 'subscriptions.status'),
    Index('idx_subscriptions_account_id', 'subscriptions.account_id'),
    Index('idx_subscriptions_card_id', 'subscriptions.card_id'),

    # Cards
    Index('idx_cards_user_id', 'cards.user_id'),

    # Accounts
    Index('idx_accounts_user_id', 'accounts.user_id'),

    # Categories
    Index('idx_categories_user_id', 'categories.user_id'),

    # Fixed Expenses
    Index('idx_fixed_expenses_user_id', 'fixed_expenses.user_id'),

    # Income Sources
    Index('idx_income_sources_user_id', 'income_sources.user_id'),

    # Installments
    Index('idx_installments_user_id', 'installments.user_id'),

    # Card Invoices
    Index('idx_card_invoices_user_id', 'card_invoices.user_id'),
    Index('idx_card_invoices_card_id', 'card_invoices.card_id'),

    # Investments
    Index('idx_investments_user_id', 'investments.user_id'),
]
