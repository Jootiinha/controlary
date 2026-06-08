"""Category model."""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Category(Base):
    """Expense/income category."""

    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    color = Column(String(7), default="#000000")
    icon = Column(String(50))
    description = Column(String(500))
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_category_user_deleted', 'user_id', 'is_deleted'),
    )

    # Relationships
    user = relationship("User", back_populates="categories")
    payments = relationship("Payment", back_populates="category")
    subscriptions = relationship("Subscription", back_populates="category")
    fixed_expenses = relationship("FixedExpense", back_populates="category")
    income_sources = relationship("IncomeSource", back_populates="category")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "color": self.color,
            "icon": self.icon,
            "description": self.description,
        }

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"
