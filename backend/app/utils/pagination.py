"""Pagination utilities for API responses."""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters from query string."""
    skip: int = 0
    limit: int = 50

    class Config:
        """Pydantic config."""
        min_items = 0
        max_items = 100

    @property
    def offset(self) -> int:
        """Get offset (alias for skip)."""
        return self.skip

    def validate(self) -> None:
        """Validate pagination params."""
        if self.skip < 0:
            raise ValueError("skip must be >= 0")
        if self.limit < 1:
            raise ValueError("limit must be >= 1")
        if self.limit > 100:
            raise ValueError("limit must be <= 100")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response."""
    items: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True

    @classmethod
    def create(cls, items: List[T], total: int, skip: int, limit: int) -> 'PaginatedResponse[T]':
        """Create paginated response."""
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )


def paginate(query, skip: int = 0, limit: int = 50):
    """Apply pagination to SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        skip: Number of items to skip
        limit: Number of items to return (max 100)

    Returns:
        Tuple of (paginated_query, total_count)
    """
    if skip < 0:
        skip = 0
    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100

    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return items, total
