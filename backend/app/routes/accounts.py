"""Account routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.accounts_repo import AccountsRepository
from app.schemas.account_schemas import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountWithBalanceResponse,
)
from app.utils.decorators import get_current_user
from app.services.audit_service import AuditService

router = APIRouter()

# Constants for pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: AccountCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new account."""
    try:
        repo = AccountsRepository(db)
        account = repo.create(user_id, **request.dict())
        return account
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=list[AccountWithBalanceResponse])
async def list_accounts(
    user_id: str = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
):
    """List all accounts with balances."""
    repo = AccountsRepository(db)
    return repo.list_accounts_with_balances(user_id, skip, limit)


@router.get("/{account_id}", response_model=AccountWithBalanceResponse)
async def get_account(
    account_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get account details with balance."""
    repo = AccountsRepository(db)
    account = repo.get_account_with_balance(user_id, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    request: AccountUpdate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update account."""
    try:
        repo = AccountsRepository(db)
        account = repo.update(user_id, account_id, **request.dict(exclude_unset=True))
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found",
            )
        return account
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete account with audit logging."""
    repo = AccountsRepository(db)

    # Get account details before deletion
    account = repo.get_by_id(user_id, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    try:
        repo.delete(user_id, account_id)

        # Log deletion
        client_ip = request.client.host if request.client else "unknown"
        AuditService.log_data_operation(
            db,
            user_id=user_id,
            operation="delete",
            resource_type="account",
            resource_id=account_id,
            client_ip=client_ip,
            endpoint=request.url.path,
            status="success",
            status_code=204,
            changes={"deleted": True, "name": account.name}
        )
    except Exception as e:
        client_ip = request.client.host if request.client else "unknown"
        AuditService.log_data_operation(
            db,
            user_id=user_id,
            operation="delete",
            resource_type="account",
            resource_id=account_id,
            client_ip=client_ip,
            endpoint=request.url.path,
            status="failure",
            status_code=500,
            error_message=str(e)
        )
        raise


@router.get("/{account_id}/balance")
async def get_account_balance(
    account_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get account balance."""
    repo = AccountsRepository(db)
    account = repo.get_by_id(user_id, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return {
        "account_id": account_id,
        "balance": repo.get_account_balance(user_id, account_id),
    }


@router.get("/accounts/total-balance")
async def get_total_balance(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get total balance across all accounts."""
    repo = AccountsRepository(db)
    return {
        "total_balance": repo.get_total_balance(user_id),
    }
