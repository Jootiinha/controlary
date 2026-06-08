"""Payments repository."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date

from app.models.payment import Payment
from app.repositories.base_repo import BaseRepository


class PaymentsRepository(BaseRepository[Payment]):
    """Repository for Payment operations."""

    def __init__(self, db: Session):
        super().__init__(db, Payment)

    def validate_payment_destination(
        self,
        account_id: Optional[str],
        card_id: Optional[str],
    ) -> bool:
        """Validate that payment has exactly one destination (account XOR card)."""
        has_account = account_id is not None
        has_card = card_id is not None
        return (has_account and not has_card) or (has_card and not has_account)

    def get_unpaid_payments(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Payment]:
        """Get unpaid payments for a user."""
        return self.list_by_user(user_id, skip, limit, is_paid=False)

    def get_paid_payments(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Payment]:
        """Get paid payments for a user."""
        return self.list_by_user(user_id, skip, limit, is_paid=True)

    def get_month_payments(
        self,
        user_id: str,
        year: int,
        month: int,
    ) -> List[Payment]:
        """Get payments for a specific month."""
        query = self.db.query(Payment).filter(
            Payment.user_id == user_id,
        )

        # Filter by year and month
        query = query.filter(
            func.strftime("%Y", Payment.data) == str(year),
            func.strftime("%m", Payment.data) == str(month).zfill(2),
        )

        return query.order_by(Payment.data.desc()).all()

    def get_month_expenses_total(
        self,
        user_id: str,
        year: int,
        month: int,
    ) -> float:
        """Get total expenses for a month."""
        total = self.db.query(
            func.sum(Payment.amount)
        ).filter(
            Payment.user_id == user_id,
            func.strftime("%Y", Payment.data) == str(year),
            func.strftime("%m", Payment.data) == str(month).zfill(2),
        ).scalar() or 0.0

        return total

    def mark_as_paid(self, user_id: str, payment_id: str) -> Optional[Payment]:
        """Mark a payment as paid."""
        return self.update(user_id, payment_id, is_paid=True)

    def mark_as_unpaid(self, user_id: str, payment_id: str) -> Optional[Payment]:
        """Mark a payment as unpaid."""
        return self.update(user_id, payment_id, is_paid=False)
