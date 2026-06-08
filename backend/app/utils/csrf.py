"""
CSRF Protection Utilities

Implements CSRF token generation, validation, and middleware for protecting
against Cross-Site Request Forgery attacks.

Uses double-submit cookie pattern:
1. Server generates CSRF token and sends in secure HttpOnly cookie
2. Client reads token from cookie and includes in X-CSRF-Token header
3. Server validates header matches cookie value

This prevents CSRF because:
- SameSite cookie policy prevents automatic cookie inclusion on cross-site requests
- JavaScript can only read cookies if SameSite=None (not used here)
- Cross-site forms can't add custom headers (CORS same-origin policy)
"""

import secrets
import hmac
import hashlib
from typing import Optional
from datetime import datetime, timedelta


class CSRFTokenManager:
    """Manages CSRF token generation and validation."""

    def __init__(self, secret_key: str, token_lifetime_hours: int = 24):
        """
        Initialize CSRF token manager.

        Args:
            secret_key: Secret key for signing tokens
            token_lifetime_hours: Token validity duration in hours
        """
        self.secret_key = secret_key.encode()
        self.token_lifetime = timedelta(hours=token_lifetime_hours)

    def generate_token(self) -> str:
        """
        Generate a new CSRF token.

        Token format: timestamp|random|signature
        - timestamp: ISO format creation time
        - random: 32 bytes random data (base64)
        - signature: HMAC-SHA256 of timestamp+random

        Returns:
            CSRF token string
        """
        timestamp = datetime.utcnow().isoformat()
        random_bytes = secrets.token_urlsafe(32)

        # Create signature
        data = f"{timestamp}|{random_bytes}"
        signature = hmac.new(
            self.secret_key,
            data.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"{data}|{signature}"

    def validate_token(self, token: str) -> bool:
        """
        Validate CSRF token.

        Checks:
        1. Token has correct format (3 parts separated by |)
        2. Signature is valid
        3. Token hasn't expired

        Args:
            token: CSRF token to validate

        Returns:
            True if token is valid, False otherwise
        """
        try:
            parts = token.split("|")
            if len(parts) != 3:
                return False

            timestamp_str, random_bytes, signature = parts

            # Validate signature
            data = f"{timestamp_str}|{random_bytes}"
            expected_signature = hmac.new(
                self.secret_key,
                data.encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                return False

            # Validate expiration
            token_time = datetime.fromisoformat(timestamp_str)
            if datetime.utcnow() - token_time > self.token_lifetime:
                return False

            return True

        except (ValueError, IndexError):
            return False


class CSRFConfig:
    """CSRF protection configuration."""

    # HTTP methods that require CSRF token
    PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    # Header name for CSRF token
    TOKEN_HEADER = "X-CSRF-Token"

    # Cookie name for CSRF token
    TOKEN_COOKIE = "csrf_token"

    # Endpoints that skip CSRF protection (e.g., login, register, health checks)
    EXEMPT_PATHS = {
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/logout",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    # Same-site cookie policy
    SAMESITE = "Strict"  # Prevent cross-site cookie sending

    # Token lifetime in hours
    TOKEN_LIFETIME_HOURS = 24

    # Require secure (HTTPS) cookies in production
    SECURE = True  # Set to False only for local development
