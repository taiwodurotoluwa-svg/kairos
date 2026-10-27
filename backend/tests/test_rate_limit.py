from __future__ import annotations

import pytest

from app.errors import KairosError
from app.schemas import ErrorCode
from app.services.rate_limit import RateLimiter


def test_rate_limiter_allows_under_limit():
    limiter = RateLimiter(limit_per_minute=5)
    # 5 requests should pass without error
    for _ in range(5):
        limiter.check_rate_limit("192.168.1.1")


def test_rate_limiter_raises_429_when_exceeded():
    limiter = RateLimiter(limit_per_minute=3)
    for _ in range(3):
        limiter.check_rate_limit("10.0.0.1")

    # 4th request must raise KairosError with 429 and RATE_LIMITED
    with pytest.raises(KairosError) as exc_info:
        limiter.check_rate_limit("10.0.0.1")

    err = exc_info.value
    assert err.status_code == 429
    assert err.code == ErrorCode.RATE_LIMITED
    assert "retry_after" in err.details
    assert err.details["retry_after"] >= 1


def test_rate_limiter_per_ip_isolation():
    limiter = RateLimiter(limit_per_minute=2)
    limiter.check_rate_limit("1.1.1.1")
    limiter.check_rate_limit("1.1.1.1")

    # IP 1 is blocked
    with pytest.raises(KairosError):
        limiter.check_rate_limit("1.1.1.1")

    # IP 2 is not affected
    limiter.check_rate_limit("2.2.2.2")
    limiter.check_rate_limit("2.2.2.2")


def test_rate_limiter_reset():
    limiter = RateLimiter(limit_per_minute=1)
    limiter.check_rate_limit("3.3.3.3")

    with pytest.raises(KairosError):
        limiter.check_rate_limit("3.3.3.3")

    limiter.reset()
    # Now it passes again
    limiter.check_rate_limit("3.3.3.3")
