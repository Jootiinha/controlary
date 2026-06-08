"""Cards repository."""

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.card import Card
from app.models.payment import Payment
from app.repositories.base_repo import BaseRepository


class CardsRepository(BaseRepository[Card]):
    """Repository for Card operations."""

    def __init__(self, db: Session):
        super().__init__(db, Card)

    def get_card_current_balance(self, user_id: str, card_id: str) -> float:
        """Calculate card balance (sum of unpaid payments)."""
        card = self.get_by_id(user_id, card_id)
        if not card:
            return 0.0

        unpaid_sum = self.db.query(
            func.sum(Payment.amount)
        ).filter(
            Payment.card_id == card_id,
            Payment.is_paid == False,
        ).scalar() or 0.0

        return unpaid_sum

    def get_available_limit(self, user_id: str, card_id: str) -> float:
        """Calculate available limit."""
        card = self.get_by_id(user_id, card_id)
        if not card or not card.limit:
            return 0.0

        used = self.get_card_current_balance(user_id, card_id)
        return card.limit - used

    def list_active_cards(self, user_id: str, skip: int = 0, limit: int = 50):
        """List active cards for a user."""
        return self.list_by_user(user_id, skip, limit, is_active=True)
