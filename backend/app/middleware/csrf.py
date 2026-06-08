"""
CSRF Protection Middleware

Middleware that:
1. Generates and sets CSRF tokens for authenticated users
2. Validates CSRF tokens for protected HTTP methods
3. Returns 403 Forbidden for invalid/missing tokens on protected requests
"""

import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.csrf import CSRFTokenManager, CSRFConfig

logger = logging.getLogger(__name__)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware for FastAPI.

    Flow:
    1. For GET requests: Generate token, set secure HttpOnly cookie, continue
    2. For POST/PUT/PATCH/DELETE: Validate token from header matches cookie
    3. For exempt paths: Skip all validation
    """

    def __init__(self, app, secret_key: str, csrf_config: CSRFConfig = None):
        """
        Initialize CSRF middleware.

        Args:
            app: FastAPI app instance
            secret_key: Secret key for token signing
            csrf_config: CSRF configuration (uses defaults if None)
        """
        super().__init__(app)
        self.token_manager = CSRFTokenManager(
            secret_key,
            token_lifetime_hours=csrf_config.TOKEN_LIFETIME_HOURS if csrf_config else 24
        )
        self.config = csrf_config or CSRFConfig()

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and apply CSRF protection.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response (possibly with CSRF token set in cookie)
        """
        path = request.url.path

        # Skip CSRF protection for exempt paths
        if path in self.config.EXEMPT_PATHS or path.startswith("/api/auth"):
            if request.method == "GET":
                # Still set token for future protected requests
                response = await call_next(request)
                token = self.token_manager.generate_token()
                self._set_csrf_cookie(response, token)
                return response
            return await call_next(request)

        # Check if request needs CSRF validation
        if request.method in self.config.PROTECTED_METHODS:
            # Validate CSRF token
            is_valid = await self._validate_csrf_token(request)
            if not is_valid:
                logger.warning(
                    f"CSRF validation failed for {request.method} {path} "
                    f"from {request.client.host if request.client else 'unknown'}"
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "CSRF token validation failed",
                        "error_code": "CSRF_VALIDATION_ERROR"
                    }
                )

        # Process request
        response = await call_next(request)

        # For successful GET requests, set fresh CSRF token
        if request.method == "GET" and response.status_code < 400:
            token = self.token_manager.generate_token()
            self._set_csrf_cookie(response, token)

        return response

    async def _validate_csrf_token(self, request: Request) -> bool:
        """
        Validate CSRF token from request.

        Checks:
        1. Token present in X-CSRF-Token header
        2. Token present in csrf_token cookie
        3. Header token matches and is valid

        Args:
            request: Request to validate

        Returns:
            True if token is valid, False otherwise
        """
        # Get token from header
        header_token = request.headers.get(self.config.TOKEN_HEADER)
        if not header_token:
            logger.debug(f"No CSRF token in header {self.config.TOKEN_HEADER}")
            return False

        # Get token from cookie
        cookie_token = request.cookies.get(self.config.TOKEN_COOKIE)
        if not cookie_token:
            logger.debug(f"No CSRF token in cookie {self.config.TOKEN_COOKIE}")
            return False

        # Tokens must match exactly
        if header_token != cookie_token:
            logger.debug("CSRF token header/cookie mismatch")
            return False

        # Validate token signature and expiration
        if not self.token_manager.validate_token(header_token):
            logger.debug("CSRF token signature or expiration invalid")
            return False

        return True

    def _set_csrf_cookie(self, response: Response, token: str) -> None:
        """
        Set CSRF token in secure HttpOnly cookie.

        Args:
            response: Response to modify
            token: CSRF token to set
        """
        response.set_cookie(
            key=self.config.TOKEN_COOKIE,
            value=token,
            httponly=True,  # Prevent JavaScript access (XSS protection)
            secure=self.config.SECURE,  # HTTPS only in production
            samesite=self.config.SAMESITE,  # Prevent cross-site cookie send
            max_age=self.config.TOKEN_LIFETIME_HOURS * 3600,
            path="/",
        )


def setup_csrf_protection(app, secret_key: str, csrf_config: CSRFConfig = None):
    """
    Setup CSRF protection middleware on FastAPI app.

    Usage:
        from app.middleware.csrf import setup_csrf_protection
        setup_csrf_protection(app, settings.SECRET_KEY)

    Args:
        app: FastAPI application
        secret_key: Secret key for token signing
        csrf_config: Optional CSRF configuration override
    """
    app.add_middleware(CSRFProtectionMiddleware, secret_key=secret_key, csrf_config=csrf_config)
