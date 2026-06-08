"""Accounts repository."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.account import Account, AccountTransaction
from app.repositories.base_repo import BaseRepository


class AccountsRepository(BaseRepository[Account]):
    """Repository for Account operations."""

    def __init__(self, db: Session):
        super().__init__(db, Account)

    def get_account_balance(self, user_id: str, account_id: str) -> float:
        """Calculate account balance: initial_balance + sum of transactions."""
        account = self.get_by_id(user_id, account_id)
        if not account:
            return 0.0

        total_transactions = self.db.query(
            func.sum(AccountTransaction.amount)
        ).filter(
            AccountTransaction.account_id == account_id
        ).scalar() or 0.0

        return account.initial_balance + total_transactions

    def get_account_with_balance(self, user_id: str, account_id: str) -> dict:
        """Get account with calculated balance."""
        account = self.get_by_id(user_id, account_id)
        if not account:
            return None

        account_dict = account.to_dict()
        account_dict["current_balance"] = self.get_account_balance(user_id, account_id)
        return account_dict

    def list_accounts_with_balances(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """List accounts with their balances."""
        accounts = self.list_by_user(user_id, skip, limit)
        return [
            {
                **account.to_dict(),
                "current_balance": self.get_account_balance(user_id, account.id),
            }
            for account in accounts
        ]

    def get_total_balance(self, user_id: str) -> float:
        """Calculate total balance across all accounts for a user."""
        accounts = self.db.query(Account).filter(Account.user_id == user_id).all()
        return sum(self.get_account_balance(user_id, account.id) for account in accounts)


class AccountTransactionsRepository(BaseRepository[AccountTransaction]):
    """Repository for AccountTransaction operations."""

    def __init__(self, db: Session):
        super().__init__(db, AccountTransaction)

    def create_transaction(
        self,
        user_id: str,
        account_id: str,
        amount: float,
        description: str,
        transaction_key: str,
    ) -> AccountTransaction:
        """Create a new transaction with idempotency key."""
        # Check if transaction already exists (idempotency)
        existing = self.db.query(AccountTransaction).filter(
            AccountTransaction.transaction_key == transaction_key
        ).first()

        if existing:
            return existing

        import uuid
        from datetime import datetime

        transaction = AccountTransaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            amount=amount,
            description=description,
            transaction_key=transaction_key,
            data=datetime.utcnow(),
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_account_transactions(
        self,
        account_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[AccountTransaction]:
        """Get transactions for an account."""
        return self.db.query(AccountTransaction).filter(
            AccountTransaction.account_id == account_id
        ).order_by(
            AccountTransaction.data.desc()
        ).offset(skip).limit(limit).all()

    def get_transaction_by_key(self, transaction_key: str) -> Optional[AccountTransaction]:
        """Get transaction by its idempotency key."""
        return self.db.query(AccountTransaction).filter(
            AccountTransaction.transaction_key == transaction_key
        ).first()
