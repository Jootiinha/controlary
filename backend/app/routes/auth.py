"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db, SessionLocal
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.utils.decorators import get_current_user
from app.utils.rate_limit import get_rate_limiter

router = APIRouter()


class RegisterRequest(BaseModel):
    """User registration request."""
    username: str
    email: EmailStr
    password: str
    full_name: str = None


class LoginRequest(BaseModel):
    """User login request."""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response model."""
    id: str
    username: str
    email: str
    full_name: str = None
    is_active: bool
    created_at: str = None
    last_login: str = None

    class Config:
        from_attributes = True

    @field_validator('created_at', 'last_login', mode='before')
    @classmethod
    def serialize_datetime(cls, v):
        """Convert datetime objects to ISO format strings."""
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str
    user: UserResponse


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user."""
    try:
        user = AuthService.register_user(
            db,
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return JWT token.

    Rate limited to 5 attempts per 10 minutes per IP address
    to prevent brute force attacks.
    """
    # Get client IP for rate limiting and audit logging
    client_ip = http_request.client.host if http_request.client else "unknown"
    user_agent = http_request.headers.get("user-agent", "unknown")

    # Check rate limit
    limiter = get_rate_limiter()
    if not limiter.is_allowed("login", client_ip):
        remaining_seconds = limiter.get_remaining_seconds("login", client_ip) or 0

        # Log rate limit violation
        AuditService.log_security_event(
            db,
            event_type="rate_limit",
            client_ip=client_ip,
            endpoint="POST /api/auth/login",
            details=f"Too many login attempts for user: {request.username}",
            user_agent=user_agent,
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please try again in {int(remaining_seconds) + 1} seconds.",
            headers={"Retry-After": str(int(remaining_seconds) + 1)},
        )

    try:
        user, token = AuthService.login(
            db,
            username=request.username,
            password=request.password,
        )

        # Log successful login
        AuditService.log_login_attempt(
            db,
            user_id=user.id,
            client_ip=client_ip,
            status="success",
            user_agent=user_agent,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user,
        }
    except ValueError as e:
        # Log failed login attempt
        AuditService.log_login_attempt(
            db,
            username=request.username,
            client_ip=client_ip,
            status="failure",
            error_message=str(e),
            user_agent=user_agent,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current authenticated user information."""
    try:
        user = AuthService.get_user_by_id(db, user_id)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/logout")
async def logout(user_id: str = Depends(get_current_user)):
    """Logout user (client-side token deletion)."""
    # JWT tokens are stateless, logout is handled by client deleting the token
    return {"message": "Logged out successfully"}


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change user password."""
    try:
        user = AuthService.change_password(
            db,
            user_id,
            old_password,
            new_password,
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
