"""Investments repository."""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.models.investment import Investment, InvestmentSnapshot
from app.repositories.base_repo import BaseRepository


class InvestmentsRepository(BaseRepository[Investment]):
    """Repository for Investment operations."""

    def __init__(self, db: Session):
        super().__init__(db, Investment)

    def add_snapshot(
        self,
        investment_id: str,
        value: float,
    ) -> InvestmentSnapshot:
        """Add a new snapshot to an investment."""
        import uuid

        snapshot = InvestmentSnapshot(
            id=str(uuid.uuid4()),
            investment_id=investment_id,
            value=value,
            snapshot_date=datetime.utcnow(),
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def get_investment_snapshots(
        self,
        investment_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[InvestmentSnapshot]:
        """Get snapshots for an investment."""
        return self.db.query(InvestmentSnapshot).filter(
            InvestmentSnapshot.investment_id == investment_id
        ).order_by(
            InvestmentSnapshot.snapshot_date.desc()
        ).offset(skip).limit(limit).all()

    def get_investment_total_value(self, user_id: str) -> float:
        """Calculate total investment portfolio value."""
        total = self.db.query(
            func.sum(Investment.current_value)
        ).filter(
            Investment.user_id == user_id
        ).scalar() or 0.0

        return total

    def get_investment_gains(self, user_id: str, investment_id: str) -> float:
        """Calculate gains/losses for an investment."""
        investment = self.get_by_id(user_id, investment_id)
        if not investment:
            return 0.0

        return investment.current_value - investment.initial_amount

    def get_investment_roi(self, user_id: str, investment_id: str) -> float:
        """Calculate ROI percentage for an investment."""
        investment = self.get_by_id(user_id, investment_id)
        if not investment or investment.initial_amount == 0:
            return 0.0

        gains = self.get_investment_gains(user_id, investment_id)
        return (gains / investment.initial_amount) * 100
