"""Caching utilities for performance optimization."""

import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple


class TTLCache:
    """Simple Time-To-Live cache for frequently accessed data."""

    def __init__(self, ttl_seconds: int = 300):
        """Initialize cache.

        Args:
            ttl_seconds: Time to live for cached items in seconds
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/not found
        """
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        """Set cache value.

        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = (value, time.time())

    def delete(self, key: str) -> None:
        """Delete cache entry.

        Args:
            key: Cache key
        """
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear all cache."""
        self.cache.clear()

    def cleanup_expired(self) -> None:
        """Remove all expired entries."""
        now = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp > self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]


# Global caches for different data types
dashboard_cache = TTLCache(ttl_seconds=60)  # 1 minute for dashboard KPIs
analytics_cache = TTLCache(ttl_seconds=300)  # 5 minutes for analytics data
user_cache = TTLCache(ttl_seconds=600)  # 10 minutes for user data


def cached(cache: TTLCache, key_prefix: str = ""):
    """Decorator for caching function results.

    Args:
        cache: TTLCache instance to use
        key_prefix: Prefix for cache keys

    Example:
        @cached(dashboard_cache, "kpis")
        def get_dashboard_kpis(user_id: int):
            return {...}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Build cache key from function name, prefix, and args
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.append(str(args))
            if kwargs:
                key_parts.append(str(kwargs))

            cache_key = ":".join(filter(None, key_parts))

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)

            return result

        return wrapper

    return decorator


def cache_key_for_user(prefix: str, user_id: int) -> str:
    """Generate cache key for user-specific data.

    Args:
        prefix: Cache key prefix
        user_id: User ID

    Returns:
        Cache key
    """
    return f"{prefix}:user:{user_id}"


def invalidate_user_cache(user_id: int, prefix: str = "") -> None:
    """Invalidate cache for specific user.

    Args:
        user_id: User ID
        prefix: Cache key prefix (optional, invalidates all if not specified)
    """
    cache_key = cache_key_for_user(prefix, user_id)
    dashboard_cache.delete(cache_key)
    analytics_cache.delete(cache_key)
    user_cache.delete(cache_key)


def invalidate_all_caches() -> None:
    """Invalidate all caches."""
    dashboard_cache.clear()
    analytics_cache.clear()
    user_cache.clear()
