"""Card routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.repositories.cards_repo import CardsRepository
from app.utils.decorators import get_current_user
from app.services.audit_service import AuditService

router = APIRouter()


class CardCreate(BaseModel):
    """Create card request."""
    name: str = Field(..., min_length=1, max_length=255)
    final_digits: Optional[str] = Field(None, max_length=4)
    limit: Optional[Decimal] = None
    day_close: Optional[int] = None
    day_due: Optional[int] = None


class CardUpdate(BaseModel):
    """Update card request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    limit: Optional[Decimal] = None
    day_close: Optional[int] = None
    day_due: Optional[int] = None
    is_active: Optional[bool] = None


class CardResponse(BaseModel):
    """Card response."""
    id: str
    name: str
    final_digits: Optional[str] = None
    limit: Optional[Decimal] = None
    day_close: Optional[int] = None
    day_due: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    request: CardCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new card."""
    try:
        repo = CardsRepository(db)
        card = repo.create(user_id, **request.dict())
        return card
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[CardResponse])
async def list_cards(
    user_id: str = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List all cards."""
    repo = CardsRepository(db)
    return repo.list_by_user(user_id, skip, limit)


@router.get("/active")
async def list_active_cards(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List active cards."""
    repo = CardsRepository(db)
    return repo.list_active_cards(user_id)


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get card details."""
    repo = CardsRepository(db)
    card = repo.get_by_id(user_id, card_id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card


@router.put("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: str,
    request: CardUpdate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update card."""
    try:
        repo = CardsRepository(db)
        card = repo.update(user_id, card_id, **request.dict(exclude_unset=True))
        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
        return card
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete card with audit logging."""
    repo = CardsRepository(db)

    # Get card details before deletion
    card = repo.get_by_id(user_id, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )

    try:
        repo.delete(user_id, card_id)

        # Log deletion
        client_ip = request.client.host if request.client else "unknown"
        AuditService.log_data_operation(
            db,
            user_id=user_id,
            operation="delete",
            resource_type="card",
            resource_id=card_id,
            client_ip=client_ip,
            endpoint=request.url.path,
            status="success",
            status_code=204,
            changes={"deleted": True, "name": card.name}
        )
    except Exception as e:
        client_ip = request.client.host if request.client else "unknown"
        AuditService.log_data_operation(
            db,
            user_id=user_id,
            operation="delete",
            resource_type="card",
            resource_id=card_id,
            client_ip=client_ip,
            endpoint=request.url.path,
            status="failure",
            status_code=500,
            error_message=str(e)
        )
        raise


@router.get("/{card_id}/balance")
async def get_card_balance(
    card_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get card current balance and available limit."""
    repo = CardsRepository(db)
    card = repo.get_by_id(user_id, card_id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return {
        "card_id": card_id,
        "current_balance": repo.get_card_current_balance(user_id, card_id),
        "available_limit": repo.get_available_limit(user_id, card_id),
    }
