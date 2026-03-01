"""Rate limiting helper used by the Vercel API.

This is identical to the original `backend/rate_limit.py` but moved so the
serverless functions can import it locally.
"""

import redis  # type: ignore
from typing import Tuple


async def check_rate_limit(
    redis_client: redis.Redis,
    client_ip: str,
    limit: int = 10,
    window: int = 60,
) -> Tuple[bool, int, int]:
    """Return (allowed, remaining, ttl) for the given IP address."""

    key = f"rate_limit:{client_ip}"
    current_count = redis_client.incr(key)
    if current_count == 1:
        redis_client.expire(key, window)
    ttl = redis_client.ttl(key)
    if ttl == -1:
        redis_client.expire(key, window)
        ttl = window
    remaining = max(0, limit - current_count)
    is_allowed = current_count <= limit
    return is_allowed, remaining, ttl
