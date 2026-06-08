"""Authentication service."""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import exc

from app.models.user import User
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_access_token


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def register_user(
        db: Session,
        username: str,
        email: str,
        password: str,
        full_name: str = None,
    ) -> User:
        """Register a new user."""
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            raise ValueError(
                f"User with username '{username}' or email '{email}' already exists"
            )

        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
        )

        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except exc.IntegrityError:
            db.rollback()
            raise ValueError("Failed to create user")

    @staticmethod
    def login(db: Session, username: str, password: str) -> tuple[User, str]:
        """Authenticate user and return token."""
        user = db.query(User).filter(User.username == username).first()

        if not user:
            raise ValueError(f"User '{username}' not found")

        if not user.is_active:
            raise ValueError("User account is inactive")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid password")

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        # Create access token
        token = create_access_token(user.id)

        return user, token

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User:
        """Get user by ID."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID '{user_id}' not found")
        return user

    @staticmethod
    def update_user(
        db: Session,
        user_id: str,
        **kwargs,
    ) -> User:
        """Update user information."""
        user = AuthService.get_user_by_id(db, user_id)

        # Only allow specific fields to be updated
        allowed_fields = {"full_name", "email"}
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(user, key, value)

        try:
            db.commit()
            db.refresh(user)
            return user
        except exc.IntegrityError:
            db.rollback()
            raise ValueError("Failed to update user")

    @staticmethod
    def change_password(db: Session, user_id: str, old_password: str, new_password: str) -> User:
        """Change user password."""
        user = AuthService.get_user_by_id(db, user_id)

        if not verify_password(old_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        user.password_hash = hash_password(new_password)

        try:
            db.commit()
            db.refresh(user)
            return user
        except exc.IntegrityError:
            db.rollback()
            raise ValueError("Failed to change password")
