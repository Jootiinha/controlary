"""Categories repository."""

from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.base_repo import BaseRepository


class CategoriesRepository(BaseRepository[Category]):
    """Repository for Category operations."""

    def __init__(self, db: Session):
        super().__init__(db, Category)

    def get_by_name(self, user_id: str, name: str) -> Category:
        """Get category by name for a user."""
        return self.db.query(Category).filter(
            Category.user_id == user_id,
            Category.name == name,
        ).first()

    def list_all_categories(self, user_id: str):
        """List all categories for a user (no pagination)."""
        return self.db.query(Category).filter(
            Category.user_id == user_id
        ).order_by(Category.name).all()
