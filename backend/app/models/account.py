"""Account model."""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from app.database import Base


class Account(Base):
    """Bank or savings account."""

    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    initial_balance = Column(Numeric(precision=15, scale=2), default=Decimal("0.00"))
    is_active = Column(Boolean, default=True, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_account_user_deleted', 'user_id', 'is_deleted'),
    )

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("AccountTransaction", back_populates="account", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="account")
    subscriptions = relationship("Subscription", back_populates="account")
    fixed_expenses = relationship("FixedExpense", back_populates="account")
    income_sources = relationship("IncomeSource", back_populates="account")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "initial_balance": self.initial_balance,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Account(id={self.id}, name={self.name}, user_id={self.user_id})>"


class AccountTransaction(Base):
    """Transaction in an account's ledger."""

    __tablename__ = "account_transactions"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    description = Column(String(500))
    transaction_key = Column(String(255), unique=True, nullable=False, index=True)
    data = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="transactions")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "amount": self.amount,
            "description": self.description,
            "transaction_key": self.transaction_key,
            "data": self.data.isoformat() if self.data else None,
        }

    def __repr__(self):
        return f"<AccountTransaction(id={self.id}, account_id={self.account_id}, amount={self.amount})>"
