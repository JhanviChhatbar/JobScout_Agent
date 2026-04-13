from __future__ import annotations

import hashlib
import logging
import os
from typing import Optional

import redis


logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def _key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _get_client() -> Optional[redis.Redis]:
    try:
        client = redis.from_url(REDIS_URL)
        # quick health check
        client.ping()
        return client
    except Exception as exc:
        logger.warning("Redis unavailable at %s: %s", REDIS_URL, exc)
        return None


def get_cached(url: str) -> Optional[str]:
    """Return cached content for URL or None if not cached/available."""
    client = _get_client()
    if client is None:
        return None

    try:
        val = client.get(_key(url))
        if val is None:
            return None
        if isinstance(val, bytes):
            return val.decode("utf-8")
        return str(val)
    except Exception as exc:
        logger.warning("Error reading cache for %s: %s", url, exc)
        return None


def set_cache(url: str, content: str, ttl_hours: int = 24) -> None:
    """Store content for URL with TTL (hours)."""
    client = _get_client()
    if client is None:
        return

    try:
        ttl_seconds = int(ttl_hours * 3600)
        client.setex(_key(url), ttl_seconds, content)
    except Exception as exc:
        logger.warning("Error setting cache for %s: %s", url, exc)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_url = "https://example.com/"
    print("Setting cache for", test_url)
    set_cache(test_url, "<html><body>Example</body></html>")
    print("Got:", get_cached(test_url))
