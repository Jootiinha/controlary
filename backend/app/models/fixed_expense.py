"""Fixed expense model."""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, Integer, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from app.database import Base


class FixedExpense(Base):
    """Fixed monthly expense."""

    __tablename__ = "fixed_expenses"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("accounts.id"))
    card_id = Column(String(36), ForeignKey("cards.id"))
    category_id = Column(String(36), ForeignKey("categories.id"))
    name = Column(String(255), nullable=False)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    day = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_fixed_expense_user_deleted', 'user_id', 'is_deleted'),
    )

    # Relationships
    account = relationship("Account", back_populates="fixed_expenses")
    card = relationship("Card", back_populates="fixed_expenses")
    category = relationship("Category", back_populates="fixed_expenses")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "card_id": self.card_id,
            "category_id": self.category_id,
            "name": self.name,
            "amount": self.amount,
            "day": self.day,
            "is_active": self.is_active,
        }

    def __repr__(self):
        return f"<FixedExpense(id={self.id}, name={self.name})>"
