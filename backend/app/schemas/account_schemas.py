"""Schemas for Account endpoints."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class AccountCreate(BaseModel):
    """Create account request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    initial_balance: Decimal = Field(default=Decimal("0.00"))


class AccountUpdate(BaseModel):
    """Update account request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    initial_balance: Optional[Decimal] = None
    is_active: Optional[bool] = None


class AccountResponse(BaseModel):
    """Account response."""
    id: str
    name: str
    description: Optional[str] = None
    initial_balance: Decimal
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AccountWithBalanceResponse(AccountResponse):
    """Account response with balance."""
    current_balance: Decimal


class AccountTransactionResponse(BaseModel):
    """Account transaction response."""
    id: str
    account_id: str
    amount: Decimal
    description: Optional[str] = None
    transaction_key: str
    data: datetime

    class Config:
        from_attributes = True
