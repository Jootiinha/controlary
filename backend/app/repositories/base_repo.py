"""Base repository with common CRUD operations."""

from typing import TypeVar, Generic, List, Optional, Type, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, exc
from contextlib import contextmanager
from datetime import datetime
import uuid

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic base repository for common CRUD operations."""

    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def _apply_soft_delete_filter(self, query):
        """Apply soft delete filter if model supports it."""
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        return query

    @contextmanager
    def _transaction(self):
        """Context manager for atomic transactions."""
        try:
            yield
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

    def create(self, user_id: str, **kwargs) -> T:
        """Create a new entity with atomic transaction."""
        entity = self.model(
            id=str(uuid.uuid4()),
            user_id=user_id,
            **kwargs,
        )
        try:
            with self._transaction():
                self.db.add(entity)
                self.db.refresh(entity)
            return entity
        except exc.IntegrityError:
            raise ValueError(f"Failed to create {self.model.__name__}")

    def get_by_id(self, user_id: str, entity_id: str, include_deleted: bool = False) -> Optional[T]:
        """Get entity by ID for a specific user, excluding soft-deleted by default."""
        query = self.db.query(self.model).filter(
            self.model.id == entity_id,
            self.model.user_id == user_id,
        )
        if not include_deleted:
            query = self._apply_soft_delete_filter(query)
        return query.first()

    def list_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        order_by: Optional[str] = None,
        include_deleted: bool = False,
        **filters,
    ) -> List[T]:
        """List entities for a user with optional filtering and pagination."""
        query = self.db.query(self.model).filter(self.model.user_id == user_id)

        # Apply soft delete filter
        if not include_deleted:
            query = self._apply_soft_delete_filter(query)

        # Apply filters
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(desc(getattr(self.model, order_by)))
        else:
            # Default ordering by created_at descending
            if hasattr(self.model, "created_at"):
                query = query.order_by(desc(self.model.created_at))

        return query.offset(skip).limit(limit).all()

    def update(self, user_id: str, entity_id: str, **kwargs) -> Optional[T]:
        """Update an entity with atomic transaction."""
        entity = self.get_by_id(user_id, entity_id)
        if not entity:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(entity, key):
                setattr(entity, key, value)

        try:
            with self._transaction():
                self.db.refresh(entity)
            return entity
        except exc.IntegrityError:
            raise ValueError(f"Failed to update {self.model.__name__}")

    def soft_delete(self, user_id: str, entity_id: str) -> bool:
        """Soft delete an entity (mark as deleted)."""
        entity = self.get_by_id(user_id, entity_id, include_deleted=False)
        if not entity:
            return False

        try:
            entity.is_deleted = True
            entity.deleted_at = datetime.utcnow()
            with self._transaction():
                self.db.refresh(entity)
            return True
        except (exc.IntegrityError, AttributeError):
            raise ValueError(f"Failed to soft delete {self.model.__name__}")

    def hard_delete(self, user_id: str, entity_id: str) -> bool:
        """Permanently delete an entity from database."""
        entity = self.get_by_id(user_id, entity_id, include_deleted=True)
        if not entity:
            return False

        try:
            with self._transaction():
                self.db.delete(entity)
            return True
        except exc.IntegrityError:
            raise ValueError(f"Failed to hard delete {self.model.__name__}")

    def delete(self, user_id: str, entity_id: str) -> bool:
        """Delete an entity (soft delete by default for soft-delete enabled models)."""
        # Use soft delete if model supports it, otherwise hard delete
        if hasattr(self.model, 'is_deleted'):
            return self.soft_delete(user_id, entity_id)
        else:
            return self.hard_delete(user_id, entity_id)

    def count_by_user(self, user_id: str, include_deleted: bool = False) -> int:
        """Count entities for a user."""
        query = self.db.query(self.model).filter(
            self.model.user_id == user_id
        )
        if not include_deleted:
            query = self._apply_soft_delete_filter(query)
        return query.count()
