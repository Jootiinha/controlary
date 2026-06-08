"""Payment routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.payments_repo import PaymentsRepository
from app.schemas.payment_schemas import (
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
)
from app.utils.decorators import get_current_user
from app.services.audit_service import AuditService

router = APIRouter()


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: PaymentCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new payment."""
    try:
        repo = PaymentsRepository(db)

        # Validate payment destination
        if not repo.validate_payment_destination(request.account_id, request.card_id):
            raise ValueError("Payment must have exactly one destination: account or card")

        payment = repo.create(user_id, **request.dict())
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=list[PaymentResponse])
async def list_payments(
    user_id: str = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
    is_paid: bool = Query(None),
    db: Session = Depends(get_db),
):
    """List payments."""
    repo = PaymentsRepository(db)
    filters = {}
    if is_paid is not None:
        filters["is_paid"] = is_paid
    return repo.list_by_user(user_id, skip, limit, **filters)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get payment details."""
    repo = PaymentsRepository(db)
    payment = repo.get_by_id(user_id, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return payment


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: str,
    request: PaymentUpdate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update payment."""
    try:
        repo = PaymentsRepository(db)
        payment = repo.update(user_id, payment_id, **request.dict(exclude_unset=True))
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete payment with audit logging."""
    repo = PaymentsRepository(db)

    # Get payment details before deletion for audit log
    payment = repo.get_by_id(user_id, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    # Delete payment
    try:
        repo.delete(user_id, payment_id)

        # Log deletion
        client_ip = request.client.host if request.client else "unknown"
        AuditService.log_data_operation(
            db,
            user_id=user_id,
            operation="delete",
            resource_type="payment",
            resource_id=payment_id,
            client_ip=client_ip,
            endpoint=request.url.path,
            status="success",
            status_code=204,
            changes={"deleted": True, "description": payment.description}
        )
    except Exception as e:
        # Log failure
        client_ip = request.client.host if request.client else "unknown"
        AuditService.log_data_operation(
            db,
            user_id=user_id,
            operation="delete",
            resource_type="payment",
            resource_id=payment_id,
            client_ip=client_ip,
            endpoint=request.url.path,
            status="failure",
            status_code=500,
            error_message=str(e)
        )
        raise


@router.patch("/{payment_id}/mark-paid", response_model=PaymentResponse)
async def mark_payment_paid(
    payment_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark payment as paid."""
    repo = PaymentsRepository(db)
    payment = repo.mark_as_paid(user_id, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return payment


@router.patch("/{payment_id}/mark-unpaid", response_model=PaymentResponse)
async def mark_payment_unpaid(
    payment_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark payment as unpaid."""
    repo = PaymentsRepository(db)
    payment = repo.mark_as_unpaid(user_id, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return payment


@router.get("/month/{year}/{month}")
async def get_month_payments(
    year: int,
    month: int,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get payments for a specific month."""
    repo = PaymentsRepository(db)
    payments = repo.get_month_payments(user_id, year, month)
    total = repo.get_month_expenses_total(user_id, year, month)
    return {
        "year": year,
        "month": month,
        "payments": [payment.to_dict() for payment in payments],
        "total": total,
    }
