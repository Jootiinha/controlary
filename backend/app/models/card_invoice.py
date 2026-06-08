"""Card invoice model."""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from app.database import Base


class InvoiceStatus(PyEnum):
    """Invoice status enum."""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class CardInvoice(Base):
    """Credit card invoice/statement."""

    __tablename__ = "card_invoices"

    id = Column(String(36), primary_key=True, index=True)
    card_id = Column(String(36), ForeignKey("cards.id"), nullable=False, index=True)
    reference_month = Column(String(7), nullable=False, index=True)
    total_amount = Column(Numeric(precision=15, scale=2), default=Decimal("0.00"))
    paid_amount = Column(Numeric(precision=15, scale=2), default=Decimal("0.00"))
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.PENDING)
    due_date = Column(DateTime)
    paid_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    card = relationship("Card", back_populates="invoices")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "card_id": self.card_id,
            "reference_month": self.reference_month,
            "total_amount": self.total_amount,
            "paid_amount": self.paid_amount,
            "status": self.status.value if self.status else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "paid_date": self.paid_date.isoformat() if self.paid_date else None,
        }

    def __repr__(self):
        return f"<CardInvoice(id={self.id}, card_id={self.card_id}, month={self.reference_month})>"
