"""
Rate Limiting Module — Redis-based sliding window counter.

Uses the Redis INCR + EXPIRE pattern to count requests per IP
within a fixed time window. This is the same approach used by
production systems like Cloudflare, GitHub API, and Twitter API.

Algorithm:
  1. Create a Redis key like "rate_limit:192.168.1.42"
  2. INCR the key (atomically increment by 1)
  3. If the key is new (count == 1), set EXPIRE to window seconds
  4. If count > limit → block the request (HTTP 429)
  5. After the window expires, Redis auto-deletes the key → counter resets
"""

import redis  # type: ignore
from typing import Tuple


async def check_rate_limit(
    redis_client: redis.Redis,
    client_ip: str,
    limit: int = 10,
    window: int = 60,
) -> Tuple[bool, int, int]:
    """
    Check if a client IP has exceeded the rate limit.

    Args:
        redis_client: Redis connection instance
        client_ip: The client's IP address (used as the rate limit key)
        limit: Maximum number of requests allowed in the window (default: 10)
        window: Time window in seconds (default: 60)

    Returns:
        Tuple of (is_allowed, remaining_requests, ttl_seconds)
        - is_allowed: True if request should be permitted
        - remaining_requests: How many requests the client has left
        - ttl_seconds: Seconds until the rate limit window resets
    """

    # Build the Redis key — unique per IP address
    key = f"rate_limit:{client_ip}"

    # Atomically increment the counter for this IP
    # If the key doesn't exist yet, Redis creates it with value 1
    current_count = redis_client.incr(key)

    # If this is the FIRST request in the window (count == 1),
    # set the expiration timer so the key auto-deletes after `window` seconds
    if current_count == 1:
        redis_client.expire(key, window)

    # Get the remaining TTL (time-to-live) for the key
    ttl = redis_client.ttl(key)

    # If TTL is -1, it means the key exists but has no expiration
    # This shouldn't happen in normal flow, but handle it defensively
    if ttl == -1:
        redis_client.expire(key, window)
        ttl = window

    # Calculate how many requests remain in this window
    remaining = max(0, limit - current_count)

    # Determine if the request is allowed
    is_allowed = current_count <= limit

    return is_allowed, remaining, ttl
