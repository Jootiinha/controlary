"""Income source model."""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, Integer, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from app.database import Base


class IncomeType(PyEnum):
    """Income type enum."""
    RECORRENTE = "recorrente"
    AVULSA = "avulsa"
    PARCELADA = "parcelada"


class IncomeSource(Base):
    """Income source."""

    __tablename__ = "income_sources"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("accounts.id"))
    card_id = Column(String(36), ForeignKey("cards.id"))
    category_id = Column(String(36), ForeignKey("categories.id"))
    name = Column(String(255), nullable=False)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    income_type = Column(SQLEnum(IncomeType), nullable=False)
    day_receipt = Column(Integer)
    num_parcels = Column(Integer)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_income_source_user_deleted', 'user_id', 'is_deleted'),
    )

    # Relationships
    account = relationship("Account", back_populates="income_sources")
    card = relationship("Card", back_populates="income_sources")
    category = relationship("Category", back_populates="income_sources")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "card_id": self.card_id,
            "category_id": self.category_id,
            "name": self.name,
            "amount": self.amount,
            "income_type": self.income_type.value if self.income_type else None,
            "day_receipt": self.day_receipt,
            "num_parcels": self.num_parcels,
        }

    def __repr__(self):
        return f"<IncomeSource(id={self.id}, name={self.name})>"
