"""Schemas for Payment endpoints."""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PaymentCreate(BaseModel):
    """Create payment request."""
    description: str = Field(..., min_length=1, max_length=500)
    amount: Decimal = Field(..., gt=0)
    account_id: Optional[str] = None
    card_id: Optional[str] = None
    category_id: Optional[str] = None
    data: datetime

    @validator('account_id', 'card_id', pre=True, always=True)
    def validate_destination(cls, v, values):
        """Validate that exactly one destination is provided."""
        account_id = values.get('account_id')
        card_id = values.get('card_id')
        has_account = account_id is not None
        has_card = card_id is not None

        if not (has_account ^ has_card):  # XOR: one but not both
            raise ValueError("Payment must have exactly one destination: account or card")
        return v


class PaymentUpdate(BaseModel):
    """Update payment request."""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    amount: Optional[Decimal] = Field(None, gt=0)
    category_id: Optional[str] = None
    is_paid: Optional[bool] = None


class PaymentResponse(BaseModel):
    """Payment response."""
    id: str
    description: str
    amount: Decimal
    account_id: Optional[str] = None
    card_id: Optional[str] = None
    category_id: Optional[str] = None
    is_paid: bool
    data: datetime

    class Config:
        from_attributes = True


class PaymentWithCategoryResponse(PaymentResponse):
    """Payment response with category name."""
    category_name: Optional[str] = None
