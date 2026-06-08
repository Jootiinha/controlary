"""Payment model."""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from app.database import Base


class Payment(Base):
    """One-time payment/transaction."""

    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("accounts.id"))
    card_id = Column(String(36), ForeignKey("cards.id"))
    category_id = Column(String(36), ForeignKey("categories.id"))
    description = Column(String(500), nullable=False)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    data = Column(DateTime, nullable=False, index=True)
    is_paid = Column(Boolean, default=False, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_payment_user_deleted', 'user_id', 'is_deleted'),
    )

    # Relationships
    account = relationship("Account", back_populates="payments")
    card = relationship("Card", back_populates="payments")
    category = relationship("Category", back_populates="payments")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "card_id": self.card_id,
            "category_id": self.category_id,
            "description": self.description,
            "amount": self.amount,
            "data": self.data.isoformat() if self.data else None,
            "is_paid": self.is_paid,
        }

    def __repr__(self):
        return f"<Payment(id={self.id}, description={self.description}, amount={self.amount})>"
