"""Investment model."""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from app.database import Base


class Investment(Base):
    """Investment/portfolio item."""

    __tablename__ = "investments"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    initial_amount = Column(Numeric(precision=15, scale=2), nullable=False)
    current_value = Column(Numeric(precision=15, scale=2), nullable=False)
    start_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_investment_user_deleted', 'user_id', 'is_deleted'),
    )

    # Relationships
    snapshots = relationship("InvestmentSnapshot", back_populates="investment", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "initial_amount": self.initial_amount,
            "current_value": self.current_value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
        }

    def __repr__(self):
        return f"<Investment(id={self.id}, name={self.name})>"


class InvestmentSnapshot(Base):
    """Historical snapshot of investment value."""

    __tablename__ = "investment_snapshots"

    id = Column(String(36), primary_key=True, index=True)
    investment_id = Column(String(36), ForeignKey("investments.id"), nullable=False, index=True)
    value = Column(Numeric(precision=15, scale=2), nullable=False)
    snapshot_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    investment = relationship("Investment", back_populates="snapshots")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "investment_id": self.investment_id,
            "value": self.value,
            "snapshot_date": self.snapshot_date.isoformat() if self.snapshot_date else None,
        }

    def __repr__(self):
        return f"<InvestmentSnapshot(id={self.id}, value={self.value})>"
