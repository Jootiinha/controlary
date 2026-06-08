"""
Rate Limiting Utilities

Implements token bucket rate limiting for protecting endpoints against brute force
and DoS attacks.

Token Bucket Algorithm:
- Each client (by IP or user_id) has a bucket with fixed capacity (max_tokens)
- Bucket refills at constant rate (tokens_per_window)
- Each request consumes 1 token
- When bucket empty, request is rejected with 429 Too Many Requests
- Simple but effective for per-endpoint limits

Example:
    Login endpoint: 5 attempts per 10 minutes (1 token per 2 minutes)
    API endpoint: 100 requests per minute
"""

import logging
import time
from typing import Dict, Tuple, Optional
from threading import Lock
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration for an endpoint."""

    # Requests allowed per time window
    max_requests: int

    # Time window in seconds
    window_seconds: int

    # Custom error message
    error_message: str = "Rate limit exceeded"

    @property
    def tokens_per_second(self) -> float:
        """Calculate token generation rate per second."""
        return self.max_requests / self.window_seconds


class TokenBucket:
    """Token bucket for rate limiting a single client/endpoint."""

    def __init__(self, max_tokens: float, tokens_per_second: float):
        """
        Initialize token bucket.

        Args:
            max_tokens: Maximum tokens in bucket (burst capacity)
            tokens_per_second: Token generation rate per second
        """
        self.max_tokens = max_tokens
        self.tokens_per_second = tokens_per_second
        self.tokens = max_tokens
        self.last_refill = time.time()
        self.lock = Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Updates bucket tokens based on elapsed time and checks if enough
        tokens available. Thread-safe.

        Args:
            tokens: Number of tokens to consume (default 1)

        Returns:
            True if tokens available and consumed, False otherwise
        """
        with self.lock:
            # Refill bucket based on elapsed time
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(
                self.max_tokens,
                self.tokens + elapsed * self.tokens_per_second
            )
            self.last_refill = now

            # Try to consume
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def get_remaining_seconds(self) -> float:
        """
        Get seconds until next token available (if bucket empty).

        Returns:
            Seconds to wait, or 0 if tokens available
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            tokens = min(
                self.max_tokens,
                self.tokens + elapsed * self.tokens_per_second
            )

            if tokens >= 1:
                return 0

            # Time until 1 token generated
            tokens_needed = 1 - tokens
            return tokens_needed / self.tokens_per_second


class RateLimiter:
    """
    Rate limiter tracking multiple clients and endpoints.

    Thread-safe implementation using token buckets.

    Usage:
        limiter = RateLimiter()
        limiter.add_rule("login", max_requests=5, window_seconds=600)
        limiter.add_rule("api", max_requests=100, window_seconds=60)

        # In endpoint
        if not limiter.is_allowed("login", client_ip):
            return HTTPException(429)
    """

    def __init__(self):
        """Initialize rate limiter."""
        self.rules: Dict[str, RateLimitConfig] = {}
        self.buckets: Dict[Tuple[str, str], TokenBucket] = {}
        self.lock = Lock()

    def add_rule(
        self,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
        error_message: str = None
    ) -> None:
        """
        Add rate limit rule for endpoint.

        Args:
            endpoint: Endpoint identifier (e.g., "login", "api_general")
            max_requests: Requests allowed per time window
            window_seconds: Time window in seconds
            error_message: Custom error message
        """
        self.rules[endpoint] = RateLimitConfig(
            max_requests=max_requests,
            window_seconds=window_seconds,
            error_message=error_message or "Rate limit exceeded"
        )

    def is_allowed(self, endpoint: str, client_id: str) -> bool:
        """
        Check if client can make request to endpoint.

        Returns 429 Too Many Requests error if rate limited.
        Creates new bucket automatically for unknown client.

        Args:
            endpoint: Endpoint identifier
            client_id: Client identifier (IP, user_id, etc)

        Returns:
            True if request allowed, False if rate limited
        """
        if endpoint not in self.rules:
            logger.warning(f"No rate limit rule for endpoint: {endpoint}")
            return True

        config = self.rules[endpoint]
        bucket_key = (endpoint, client_id)

        with self.lock:
            # Create bucket if needed
            if bucket_key not in self.buckets:
                self.buckets[bucket_key] = TokenBucket(
                    max_tokens=config.max_requests,
                    tokens_per_second=config.tokens_per_second
                )

            bucket = self.buckets[bucket_key]

        # Try to consume token
        allowed = bucket.consume()

        if not allowed:
            logger.warning(
                f"Rate limit exceeded: endpoint={endpoint}, client={client_id}"
            )

        return allowed

    def get_remaining_seconds(self, endpoint: str, client_id: str) -> Optional[float]:
        """
        Get seconds until client can retry (if rate limited).

        Args:
            endpoint: Endpoint identifier
            client_id: Client identifier

        Returns:
            Seconds to wait if rate limited, None if allowed
        """
        bucket_key = (endpoint, client_id)

        if bucket_key not in self.buckets:
            return None

        return self.buckets[bucket_key].get_remaining_seconds()

    def cleanup_old_buckets(self, max_age_seconds: int = 3600) -> None:
        """
        Remove old buckets (not accessed in max_age_seconds).

        Prevents memory leak from unlimited client_ids.
        Should be called periodically (e.g., every 10 minutes).

        Args:
            max_age_seconds: Bucket age threshold for removal (default 1 hour)
        """
        now = time.time()
        with self.lock:
            to_remove = []
            for key, bucket in self.buckets.items():
                age = now - bucket.last_refill
                if age > max_age_seconds:
                    to_remove.append(key)

            for key in to_remove:
                del self.buckets[key]

            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} rate limit buckets")


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get or create global rate limiter instance.

    Returns:
        Global RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def configure_rate_limits() -> RateLimiter:
    """
    Configure default rate limits for common endpoints.

    Returns:
        Configured RateLimiter instance

    Configured limits:
        - login: 5 requests per 10 minutes (anti brute force)
        - register: 3 requests per hour (anti spam)
        - api_general: 100 requests per minute (anti DoS)
        - api_strict: 10 requests per minute (sensitive operations)
    """
    limiter = get_rate_limiter()

    # Login: 5 attempts per 10 minutes (1 per 2 minutes)
    limiter.add_rule(
        "login",
        max_requests=5,
        window_seconds=600,
        error_message="Too many login attempts. Try again in 10 minutes."
    )

    # Registration: 3 attempts per hour (anti spam)
    limiter.add_rule(
        "register",
        max_requests=3,
        window_seconds=3600,
        error_message="Too many registration attempts. Try again later."
    )

    # General API: 100 per minute per IP
    limiter.add_rule(
        "api_general",
        max_requests=100,
        window_seconds=60,
        error_message="API rate limit exceeded"
    )

    # Strict: 10 per minute (sensitive operations)
    limiter.add_rule(
        "api_strict",
        max_requests=10,
        window_seconds=60,
        error_message="Rate limit exceeded for this operation"
    )

    return limiter
