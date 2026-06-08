"""Installments repository."""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.installment import Installment
from app.repositories.base_repo import BaseRepository


class InstallmentsRepository(BaseRepository[Installment]):
    """Repository for Installment operations."""

    def __init__(self, db: Session):
        super().__init__(db, Installment)

    def get_unpaid_installments(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Installment]:
        """Get unpaid installments for a user."""
        return self.list_by_user(user_id, skip, limit, is_paid=False)

    def get_paid_installments(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Installment]:
        """Get paid installments for a user."""
        return self.list_by_user(user_id, skip, limit, is_paid=True)

    def get_total_remaining_debt(self, user_id: str) -> float:
        """Calculate total remaining debt from unpaid installments."""
        total = self.db.query(
            func.sum(Installment.total_amount - Installment.paid_amount)
        ).filter(
            Installment.user_id == user_id,
            Installment.is_paid == False,
        ).scalar() or 0.0

        return max(0.0, total)  # Ensure non-negative

    def mark_as_paid(self, user_id: str, installment_id: str) -> Installment:
        """Mark installment as paid."""
        return self.update(user_id, installment_id, is_paid=True, paid_amount=self.db.query(Installment).filter(Installment.id == installment_id).first().total_amount)

    def update_payment(self, user_id: str, installment_id: str, paid_amount: float) -> Installment:
        """Update paid amount for an installment."""
        return self.update(user_id, installment_id, paid_amount=paid_amount)
