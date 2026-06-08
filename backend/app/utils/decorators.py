"""Decorators for routes."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.utils.jwt import get_user_id_from_token

security = HTTPBearer()


async def get_current_user(credentials = Depends(security)) -> str:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    user_id = get_user_id_from_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return user_id
