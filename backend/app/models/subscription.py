"""Subscription model."""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, Integer, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from app.database import Base


class SubscriptionStatus(PyEnum):
    """Subscription status enum."""
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class Subscription(Base):
    """Recurring subscription."""

    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("accounts.id"))
    card_id = Column(String(36), ForeignKey("cards.id"))
    category_id = Column(String(36), ForeignKey("categories.id"))
    name = Column(String(255), nullable=False)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    day_charge = Column(Integer, nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_subscription_user_deleted', 'user_id', 'is_deleted'),
    )

    # Relationships
    account = relationship("Account", back_populates="subscriptions")
    card = relationship("Card", back_populates="subscriptions")
    category = relationship("Category", back_populates="subscriptions")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "card_id": self.card_id,
            "category_id": self.category_id,
            "name": self.name,
            "amount": self.amount,
            "day_charge": self.day_charge,
            "status": self.status.value if self.status else None,
        }

    def __repr__(self):
        return f"<Subscription(id={self.id}, name={self.name})>"
