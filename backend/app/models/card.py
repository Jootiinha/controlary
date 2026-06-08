"""Card model."""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, Integer, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from app.database import Base


class Card(Base):
    """Credit or debit card."""

    __tablename__ = "cards"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    final_digits = Column(String(4))
    limit = Column(Numeric(precision=15, scale=2))
    day_close = Column(Integer)
    day_due = Column(Integer)
    is_active = Column(Boolean, default=True, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_card_user_deleted', 'user_id', 'is_deleted'),
    )

    # Relationships
    user = relationship("User", back_populates="cards")
    payments = relationship("Payment", back_populates="card")
    invoices = relationship("CardInvoice", back_populates="card")
    subscriptions = relationship("Subscription", back_populates="card")
    fixed_expenses = relationship("FixedExpense", back_populates="card")
    income_sources = relationship("IncomeSource", back_populates="card")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "final_digits": self.final_digits,
            "limit": self.limit,
            "day_close": self.day_close,
            "day_due": self.day_due,
            "is_active": self.is_active,
        }

    def __repr__(self):
        return f"<Card(id={self.id}, name={self.name})>"
