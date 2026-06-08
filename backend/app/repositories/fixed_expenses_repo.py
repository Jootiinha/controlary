"""Fixed expenses repository."""

from sqlalchemy.orm import Session

from app.models.fixed_expense import FixedExpense
from app.repositories.base_repo import BaseRepository


class FixedExpensesRepository(BaseRepository[FixedExpense]):
    """Repository for FixedExpense operations."""

    def __init__(self, db: Session):
        super().__init__(db, FixedExpense)

    def list_active_expenses(self, user_id: str, skip: int = 0, limit: int = 50):
        """List active fixed expenses for a user."""
        return self.list_by_user(user_id, skip, limit, is_active=True)

    def deactivate_expense(self, user_id: str, expense_id: str) -> FixedExpense:
        """Deactivate a fixed expense."""
        return self.update(user_id, expense_id, is_active=False)

    def activate_expense(self, user_id: str, expense_id: str) -> FixedExpense:
        """Activate a fixed expense."""
        return self.update(user_id, expense_id, is_active=True)

    def get_expenses_by_day(self, user_id: str, day: int):
        """Get all fixed expenses that occur on a specific day of the month."""
        return self.db.query(FixedExpense).filter(
            FixedExpense.user_id == user_id,
            FixedExpense.day == day,
            FixedExpense.is_active == True,
        ).all()
