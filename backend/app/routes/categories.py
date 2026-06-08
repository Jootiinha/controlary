"""Category routes."""

import re
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, validator
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.categories_repo import CategoriesRepository
from app.utils.decorators import get_current_user
from app.services.audit_service import AuditService

router = APIRouter()

# Valid icon names (emoji list)
VALID_ICONS = {
    "shopping", "food", "transportation", "entertainment", "health",
    "utilities", "rent", "salary", "investment", "savings", "gift",
    "other", "💰", "🍔", "🚗", "🎬", "🏥", "💡", "🏠", "💼", "📈", "🎁"
}


class CategoryCreate(BaseModel):
    """Create category request."""
    name: str = Field(..., min_length=1, max_length=255)
    color: Optional[str] = Field(default="#000000", max_length=7)
    icon: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)

    @validator('color')
    def validate_color(cls, v):
        """Validate hex color format."""
        if v is None:
            return v
        if not re.match(r'^#[0-9a-fA-F]{6}$', v):
            raise ValueError("Color must be a valid hex color code (e.g., #FF5733)")
        return v

    @validator('icon')
    def validate_icon(cls, v):
        """Validate icon is from allowed set."""
        if v is None:
            return v
        if v not in VALID_ICONS:
            raise ValueError(f"Icon must be one of: {', '.join(sorted(VALID_ICONS))}")
        return v


class CategoryUpdate(BaseModel):
    """Update category request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)

    @validator('color')
    def validate_color(cls, v):
        """Validate hex color format."""
        if v is None:
            return v
        if not re.match(r'^#[0-9a-fA-F]{6}$', v):
            raise ValueError("Color must be a valid hex color code (e.g., #FF5733)")
        return v

    @validator('icon')
    def validate_icon(cls, v):
        """Validate icon is from allowed set."""
        if v is None:
            return v
        if v not in VALID_ICONS:
            raise ValueError(f"Icon must be one of: {', '.join(sorted(VALID_ICONS))}")
        return v


class CategoryResponse(BaseModel):
    """Category response."""
    id: str
    name: str
    color: str
    icon: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    request: CategoryCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new category."""
    try:
        repo = CategoriesRepository(db)
        category = repo.create(user_id, **request.dict())
        return category
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[CategoryResponse])
async def list_categories(
    user_id: str = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List all categories."""
    repo = CategoriesRepository(db)
    return repo.list_by_user(user_id, skip, limit)


@router.get("/all")
async def list_all_categories(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all categories (no pagination)."""
    repo = CategoriesRepository(db)
    return repo.list_all_categories(user_id)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get category details."""
    repo = CategoriesRepository(db)
    category = repo.get_by_id(user_id, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    request: CategoryUpdate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update category."""
    try:
        repo = CategoriesRepository(db)
        category = repo.update(user_id, category_id, **request.dict(exclude_unset=True))
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        return category
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete category with audit logging."""
    repo = CategoriesRepository(db)

    # Get category details before deletion
    category = repo.get_by_id(user_id, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    try:
        repo.delete(user_id, category_id)

        # Log deletion
        client_ip = request.client.host if request.client else "unknown"
        AuditService.log_data_operation(
            db,
            user_id=user_id,
            operation="delete",
            resource_type="category",
            resource_id=category_id,
            client_ip=client_ip,
            endpoint=request.url.path,
            status="success",
            status_code=204,
            changes={"deleted": True, "name": category.name}
        )
    except Exception as e:
        client_ip = request.client.host if request.client else "unknown"
        AuditService.log_data_operation(
            db,
            user_id=user_id,
            operation="delete",
            resource_type="category",
            resource_id=category_id,
            client_ip=client_ip,
            endpoint=request.url.path,
            status="failure",
            status_code=500,
            error_message=str(e)
        )
        raise
