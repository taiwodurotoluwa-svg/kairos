from __future__ import annotations

from collections import defaultdict
import math
import time

from app.config import get_settings
from app.errors import KairosError
from app.schemas import ErrorCode


class RateLimiter:
    """In-memory sliding-window rate limiter per client IP."""

    def __init__(self, limit_per_minute: int | None = None) -> None:
        if limit_per_minute is None:
            limit_per_minute = get_settings().analyze_rate_limit_per_minute
        self.limit = limit_per_minute
        self.window_seconds = 60.0
        self._history: dict[str, list[float]] = defaultdict(list)

    def check_rate_limit(self, client_ip: str) -> None:
        """Verify client IP has not exceeded rate limit. Raises KairosError(429) if exceeded."""
        now = time.monotonic()
        cutoff = now - self.window_seconds

        # Clean history
        records = [t for t in self._history[client_ip] if t > cutoff]
        self._history[client_ip] = records

        if len(records) >= self.limit:
            oldest = records[0]
            retry_after = max(1, math.ceil(self.window_seconds - (now - oldest)))
            raise KairosError(
                ErrorCode.RATE_LIMITED,
                f"Rate limit exceeded: maximum {self.limit} requests per minute.",
                status_code=429,
                details={"retry_after": retry_after},
            )

        self._history[client_ip].append(now)

    def reset(self) -> None:
        """Clear all rate limit history (useful in tests)."""
        self._history.clear()


_RATE_LIMITER_INSTANCE = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _RATE_LIMITER_INSTANCE
