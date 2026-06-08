"""Income sources repository."""

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.income_source import IncomeSource, IncomeType
from app.repositories.base_repo import BaseRepository


class IncomeSourcesRepository(BaseRepository[IncomeSource]):
    """Repository for IncomeSource operations."""

    def __init__(self, db: Session):
        super().__init__(db, IncomeSource)

    def list_recurring_income(self, user_id: str, skip: int = 0, limit: int = 50):
        """List recurring income sources."""
        return self.list_by_user(
            user_id, skip, limit, income_type=IncomeType.RECORRENTE
        )

    def list_occasional_income(self, user_id: str, skip: int = 0, limit: int = 50):
        """List occasional (avulsa) income sources."""
        return self.list_by_user(
            user_id, skip, limit, income_type=IncomeType.AVULSA
        )

    def list_installment_income(self, user_id: str, skip: int = 0, limit: int = 50):
        """List installment (parcelada) income sources."""
        return self.list_by_user(
            user_id, skip, limit, income_type=IncomeType.PARCELADA
        )

    def get_total_monthly_recurring(self, user_id: str) -> float:
        """Calculate total monthly recurring income."""
        total = self.db.query(
            func.sum(IncomeSource.amount)
        ).filter(
            IncomeSource.user_id == user_id,
            IncomeSource.income_type == IncomeType.RECORRENTE,
        ).scalar() or 0.0

        return total

    def get_total_by_type(self, user_id: str, income_type: IncomeType) -> float:
        """Get total income by type."""
        total = self.db.query(
            func.sum(IncomeSource.amount)
        ).filter(
            IncomeSource.user_id == user_id,
            IncomeSource.income_type == income_type,
        ).scalar() or 0.0

        return total
