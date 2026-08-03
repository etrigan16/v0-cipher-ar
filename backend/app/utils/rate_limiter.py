"""In-memory rate limiter: dict[str, list[float]].

Max 5 attempts per 60-second window per key (IP address or partial token).
Trivially replaceable with Redis later.
"""

import time

from fastapi import HTTPException, status


class InMemoryRateLimiter:
    """Sliding-window rate limiter backed by an in-memory dict."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 60) -> None:
        self._store: dict[str, list[float]] = {}
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds

    def _prune(self, key: str, now: float) -> None:
        timestamps = self._store.get(key)
        if timestamps is None:
            return
        cutoff = now - self._window_seconds
        self._store[key] = [t for t in timestamps if t > cutoff]
        if not self._store[key]:
            del self._store[key]

    def check(self, key: str) -> bool:
        """Return True if the request is allowed, False if rate-limited."""
        now = time.time()
        self._prune(key, now)
        timestamps = self._store.get(key)
        if timestamps is None:
            return True
        return len(timestamps) < self._max_attempts

    def record(self, key: str) -> None:
        """Record an attempt for the given key."""
        now = time.time()
        self._store.setdefault(key, []).append(now)

    def raise_if_limited(self, key: str) -> None:
        """Raise 429 if the key is rate-limited."""
        if not self.check(key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos. Intente de nuevo en 60 segundos.",
            )


# Singleton instance scoped to the challenge endpoint.
challenge_limiter = InMemoryRateLimiter()
