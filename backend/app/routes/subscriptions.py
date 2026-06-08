"""Subscription routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, Field, validator
from typing import Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.repositories.subscriptions_repo import SubscriptionsRepository
from app.models.subscription import SubscriptionStatus
from app.utils.decorators import get_current_user
from app.services.audit_service import AuditService

router = APIRouter()


class SubscriptionCreate(BaseModel):
    """Create subscription request."""
    name: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0)
    day_charge: int = Field(..., ge=1, le=31)
    start_date: Optional[str] = None
    account_id: Optional[str] = None
    card_id: Optional[str] = None
    category_id: Optional[str] = None

    @validator('account_id', 'card_id', pre=True, always=True)
    def validate_destination(cls, v, values):
        """Ensure exactly one destination (account or card) is provided."""
        account_id = values.get('account_id')
        card_id = values.get('card_id')

        has_account = account_id is not None
        has_card = card_id is not None

        if not (has_account ^ has_card):
            raise ValueError("Subscription must have exactly one destination: either account_id or card_id, not both or neither")

        return v


class SubscriptionUpdate(BaseModel):
    """Update subscription request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[Decimal] = Field(None, gt=0)
    day_charge: Optional[int] = Field(None, ge=1, le=31)
    category_id: Optional[str] = None


class SubscriptionResponse(BaseModel):
    """Subscription response."""
    id: str
    name: str
    amount: Decimal
    day_charge: int
    account_id: Optional[str] = None
    card_id: Optional[str] = None
    category_id: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: SubscriptionCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new subscription."""
    try:
        repo = SubscriptionsRepository(db)
        subscription = repo.create(user_id, **request.dict())
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    user_id: str = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List subscriptions."""
    repo = SubscriptionsRepository(db)
    filters = {}
    if status:
        try:
            filters["status"] = SubscriptionStatus[status.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}. Valid statuses are: {', '.join([s.name for s in SubscriptionStatus])}"
            )
    return repo.list_by_user(user_id, skip, limit, **filters)


@router.get("/active")
async def list_active_subscriptions(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List active subscriptions."""
    repo = SubscriptionsRepository(db)
    return repo.list_active_subscriptions(user_id)


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get subscription details."""
    repo = SubscriptionsRepository(db)
    subscription = repo.get_by_id(user_id, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    return subscription


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: str,
    request: SubscriptionUpdate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update subscription."""
    try:
        repo = SubscriptionsRepository(db)
        subscription = repo.update(user_id, subscription_id, **request.dict(exclude_unset=True))
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete subscription with audit logging."""
    repo = SubscriptionsRepository(db)

    # Get subscription details before deletion
    subscription = repo.get_by_id(user_id, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    try:
        repo.delete(user_id, subscription_id)

        # Log deletion
        client_ip = request.client.host if request.client else "unknown"
        AuditService.log_data_operation(
            db,
            user_id=user_id,
            operation="delete",
            resource_type="subscription",
            resource_id=subscription_id,
            client_ip=client_ip,
            endpoint=request.url.path,
            status="success",
            status_code=204,
            changes={"deleted": True, "name": subscription.name}
        )
    except Exception as e:
        client_ip = request.client.host if request.client else "unknown"
        AuditService.log_data_operation(
            db,
            user_id=user_id,
            operation="delete",
            resource_type="subscription",
            resource_id=subscription_id,
            client_ip=client_ip,
            endpoint=request.url.path,
            status="failure",
            status_code=500,
            error_message=str(e)
        )
        raise


@router.patch("/{subscription_id}/pause", response_model=SubscriptionResponse)
async def pause_subscription(
    subscription_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pause a subscription."""
    repo = SubscriptionsRepository(db)
    subscription = repo.mark_as_paused(user_id, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    return subscription


@router.patch("/{subscription_id}/activate", response_model=SubscriptionResponse)
async def activate_subscription(
    subscription_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Activate a subscription."""
    repo = SubscriptionsRepository(db)
    subscription = repo.mark_as_active(user_id, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    return subscription


@router.patch("/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a subscription."""
    repo = SubscriptionsRepository(db)
    subscription = repo.cancel_subscription(user_id, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    return subscription
