"""Tests for critical business logic validation."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, create_all_tables, Base, engine
from app.models.user import User
from app.models.account import Account, AccountTransaction
from app.models.payment import Payment
from app.models.card import Card
from app.models.subscription import Subscription
from app.models.category import Category
from app.utils.password import hash_password
from app.repositories.accounts_repo import AccountsRepository, AccountTransactionsRepository
from app.repositories.payments_repo import PaymentsRepository


@pytest.fixture
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpass123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_account(db_session: Session, test_user: User):
    """Create a test account."""
    account = Account(
        user_id=test_user.id,
        name="Test Account",
        description="Test account for validation",
        initial_balance=1000.00,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def test_card(db_session: Session, test_user: User):
    """Create a test credit card."""
    card = Card(
        user_id=test_user.id,
        name="Test Card",
        final_digits="1234",
        limit=5000.00,
        day_close=10,
        day_due=15,
    )
    db_session.add(card)
    db_session.commit()
    db_session.refresh(card)
    return card


@pytest.fixture
def test_category(db_session: Session, test_user: User):
    """Create a test category."""
    category = Category(
        user_id=test_user.id,
        name="Test Category",
        color="#3B82F6",
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


class TestLedgerIdempotence:
    """Test ledger idempotence via transaction_key."""

    def test_same_transaction_twice_creates_one_entry(
        self, db_session: Session, test_user: User, test_account: Account
    ):
        """Creating the same transaction twice should result in only one entry."""
        repo = AccountTransactionsRepository(db_session)

        # Create first transaction
        tx1 = repo.create_transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=100.00,
            description="Test transaction",
            transaction_key="unique-key-123",
            transaction_date=datetime.now(),
        )

        # Create same transaction again with same key
        tx2 = repo.create_transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=100.00,
            description="Test transaction",
            transaction_key="unique-key-123",
            transaction_date=datetime.now(),
        )

        # Both should return the same transaction
        assert tx1.id == tx2.id

        # Verify only one entry exists
        transactions = db_session.query(AccountTransaction).filter(
            AccountTransaction.user_id == test_user.id
        ).all()
        assert len(transactions) == 1
        assert transactions[0].transaction_key == "unique-key-123"

    def test_different_keys_create_separate_entries(
        self, db_session: Session, test_user: User, test_account: Account
    ):
        """Transactions with different keys should create separate entries."""
        repo = AccountTransactionsRepository(db_session)

        tx1 = repo.create_transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=100.00,
            description="Transaction 1",
            transaction_key="key-1",
            transaction_date=datetime.now(),
        )

        tx2 = repo.create_transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=100.00,
            description="Transaction 2",
            transaction_key="key-2",
            transaction_date=datetime.now(),
        )

        assert tx1.id != tx2.id

        transactions = db_session.query(AccountTransaction).filter(
            AccountTransaction.user_id == test_user.id
        ).all()
        assert len(transactions) == 2


class TestPaymentDestinationValidation:
    """Test payment destination validation (account XOR card)."""

    def test_payment_to_account_valid(
        self, db_session: Session, test_user: User, test_account: Account, test_category: Category
    ):
        """Payment to account without card should be valid."""
        payment = Payment(
            user_id=test_user.id,
            description="Payment to account",
            amount=-50.00,
            data=datetime.now(),
            account_id=test_account.id,
            card_id=None,
            category_id=test_category.id,
            is_paid=False,
        )
        db_session.add(payment)
        db_session.commit()

        assert payment.account_id == test_account.id
        assert payment.card_id is None

    def test_payment_to_card_valid(
        self, db_session: Session, test_user: User, test_card: Card, test_category: Category
    ):
        """Payment to card without account should be valid."""
        payment = Payment(
            user_id=test_user.id,
            description="Payment to card",
            amount=-50.00,
            data=datetime.now(),
            account_id=None,
            card_id=test_card.id,
            category_id=test_category.id,
            is_paid=False,
        )
        db_session.add(payment)
        db_session.commit()

        assert payment.account_id is None
        assert payment.card_id == test_card.id

    def test_payment_to_both_account_and_card_invalid(
        self, db_session: Session, test_user: User, test_account: Account, test_card: Card, test_category: Category
    ):
        """Payment to both account and card should violate XOR constraint."""
        payment = Payment(
            user_id=test_user.id,
            description="Invalid payment",
            amount=-50.00,
            data=datetime.now(),
            account_id=test_account.id,
            card_id=test_card.id,
            category_id=test_category.id,
            is_paid=False,
        )
        db_session.add(payment)

        # This should be caught at the API validation layer
        # The database constraint should prevent this
        with pytest.raises(Exception):  # Database constraint violation
            db_session.commit()

    def test_payment_to_neither_account_nor_card_invalid(
        self, db_session: Session, test_user: User, test_category: Category
    ):
        """Payment to neither account nor card should be invalid."""
        payment = Payment(
            user_id=test_user.id,
            description="Invalid payment",
            amount=-50.00,
            data=datetime.now(),
            account_id=None,
            card_id=None,
            category_id=test_category.id,
            is_paid=False,
        )
        db_session.add(payment)

        with pytest.raises(Exception):  # Database constraint violation
            db_session.commit()


class TestAccountBalanceCalculation:
    """Test account balance calculation logic."""

    def test_balance_equals_initial_plus_transactions(
        self, db_session: Session, test_user: User, test_account: Account
    ):
        """Account balance should equal initial_balance + sum(transactions)."""
        repo = AccountTransactionsRepository(db_session)
        accounts_repo = AccountsRepository(db_session)

        # Create some transactions
        repo.create_transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=100.00,
            description="Income",
            transaction_key="tx-1",
            transaction_date=datetime.now(),
        )

        repo.create_transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=-50.00,
            description="Expense",
            transaction_key="tx-2",
            transaction_date=datetime.now(),
        )

        # Get account balance
        balance = accounts_repo.get_account_balance(test_account.id, test_user.id)

        # Expected: 1000 (initial) + 100 - 50 = 1050
        expected_balance = test_account.initial_balance + 100.00 - 50.00
        assert balance == expected_balance

    def test_total_balance_sums_all_accounts(
        self, db_session: Session, test_user: User, test_account: Account
    ):
        """Total balance should be sum of all account balances."""
        # Create second account
        account2 = Account(
            user_id=test_user.id,
            name="Account 2",
            description="Second account",
            initial_balance=500.00,
        )
        db_session.add(account2)
        db_session.commit()

        accounts_repo = AccountsRepository(db_session)
        accounts = accounts_repo.list_by_user(test_user.id)

        total = sum(a.current_balance for a in accounts)
        expected = test_account.initial_balance + account2.initial_balance

        assert total == expected


class TestPaymentStatusLogic:
    """Test payment status and marking logic."""

    def test_mark_payment_as_paid(
        self, db_session: Session, test_user: User, test_account: Account, test_category: Category
    ):
        """Payment should be markable as paid."""
        payment = Payment(
            user_id=test_user.id,
            description="Payment to mark",
            amount=-50.00,
            data=datetime.now(),
            account_id=test_account.id,
            card_id=None,
            category_id=test_category.id,
            is_paid=False,
        )
        db_session.add(payment)
        db_session.commit()

        # Mark as paid
        payment.is_paid = True
        db_session.commit()

        db_session.refresh(payment)
        assert payment.is_paid is True

    def test_outstanding_balance_excludes_paid_payments(
        self, db_session: Session, test_user: User, test_account: Account, test_category: Category
    ):
        """Outstanding balance should only include unpaid payments."""
        # Create paid payment
        paid = Payment(
            user_id=test_user.id,
            description="Paid payment",
            amount=-100.00,
            data=datetime.now(),
            account_id=test_account.id,
            card_id=None,
            category_id=test_category.id,
            is_paid=True,
        )

        # Create unpaid payment
        unpaid = Payment(
            user_id=test_user.id,
            description="Unpaid payment",
            amount=-50.00,
            data=datetime.now(),
            account_id=test_account.id,
            card_id=None,
            category_id=test_category.id,
            is_paid=False,
        )

        db_session.add(paid)
        db_session.add(unpaid)
        db_session.commit()

        # Calculate outstanding
        outstanding = db_session.query(Payment).filter(
            Payment.user_id == test_user.id,
            Payment.is_paid == False,
            Payment.amount < 0,
        ).all()

        outstanding_total = sum(abs(p.amount) for p in outstanding)
        assert outstanding_total == 50.00


class TestSubscriptionStatusTransitions:
    """Test subscription status transitions."""

    def test_subscription_status_transitions(
        self, db_session: Session, test_user: User, test_account: Account, test_category: Category
    ):
        """Test valid subscription status transitions."""
        subscription = Subscription(
            user_id=test_user.id,
            name="Test Subscription",
            amount=99.99,
            account_id=test_account.id,
            category_id=test_category.id,
            start_date=datetime.now().date(),
            renewal_day=15,
            status="Ativa",
        )
        db_session.add(subscription)
        db_session.commit()

        # Active → Paused
        subscription.status = "Pausada"
        db_session.commit()
        db_session.refresh(subscription)
        assert subscription.status == "Pausada"

        # Paused → Active
        subscription.status = "Ativa"
        db_session.commit()
        db_session.refresh(subscription)
        assert subscription.status == "Ativa"

        # Active → Cancelled
        subscription.status = "Cancelada"
        db_session.commit()
        db_session.refresh(subscription)
        assert subscription.status == "Cancelada"

        # Cancelled cannot transition back
        # (business rule: cancelled subscriptions are final)
