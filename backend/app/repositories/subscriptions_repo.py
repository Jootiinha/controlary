"""Subscriptions repository."""

from sqlalchemy.orm import Session

from app.models.subscription import Subscription, SubscriptionStatus
from app.repositories.base_repo import BaseRepository


class SubscriptionsRepository(BaseRepository[Subscription]):
    """Repository for Subscription operations."""

    def __init__(self, db: Session):
        super().__init__(db, Subscription)

    def list_active_subscriptions(self, user_id: str, skip: int = 0, limit: int = 50):
        """List active subscriptions for a user."""
        return self.list_by_user(
            user_id, skip, limit, status=SubscriptionStatus.ACTIVE
        )

    def list_paused_subscriptions(self, user_id: str, skip: int = 0, limit: int = 50):
        """List paused subscriptions for a user."""
        return self.list_by_user(
            user_id, skip, limit, status=SubscriptionStatus.PAUSED
        )

    def mark_as_paused(self, user_id: str, subscription_id: str) -> Subscription:
        """Pause a subscription."""
        return self.update(user_id, subscription_id, status=SubscriptionStatus.PAUSED)

    def mark_as_active(self, user_id: str, subscription_id: str) -> Subscription:
        """Activate a subscription."""
        return self.update(user_id, subscription_id, status=SubscriptionStatus.ACTIVE)

    def cancel_subscription(self, user_id: str, subscription_id: str) -> Subscription:
        """Cancel a subscription."""
        return self.update(user_id, subscription_id, status=SubscriptionStatus.CANCELLED)
