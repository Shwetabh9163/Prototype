"""
Traffic Management Prototype — Backend

This is the main FastAPI application that powers the traffic management
prototype. Each instance runs as a separate Docker container with its
own SERVER_ID, allowing Nginx to load-balance across them.

Endpoints:
  GET /         → Health check (returns server ID and status)
  GET /data     → Caching demo (Redis cache + simulated DB delay)
  GET /rate-test → Rate limiting demo (10 req/60s per IP via Redis)
  GET /flush-cache → Clear all cached data in Redis

Architecture:
  [Client] → [Nginx LB] → [This Server (1 of 3)] → [Redis]
"""

import os
import time
import asyncio
import json

from fastapi import FastAPI, Request, Query  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
import redis  # type: ignore

from rate_limit import check_rate_limit  # type: ignore


# ============================================================
# Configuration — read from environment variables (set by Docker)
# ============================================================

# Each container gets a unique SERVER_ID (e.g., "server-1", "server-2", "server-3")
SERVER_ID = os.getenv("SERVER_ID", "server-unknown")

# Redis connection settings — uses Docker service name "redis" as hostname
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Cache TTL (time-to-live) in seconds — how long cached data lives in Redis
CACHE_TTL = int(os.getenv("CACHE_TTL", 30))

# Simulated database delay in milliseconds — makes cache speedup visible
DB_DELAY_MS = int(os.getenv("DB_DELAY_MS", 200))

# Rate limit settings
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 10))        # max requests per window
RATE_WINDOW = int(os.getenv("RATE_WINDOW", 60))       # window in seconds


# ============================================================
# App Initialization
# ============================================================

app = FastAPI(
    title=f"Traffic Management Backend ({SERVER_ID})",
    description="Traffic Management Prototype — FastAPI Backend Server",
)

# Enable CORS so the frontend (served by Nginx or opened locally) can call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Allow all origins (prototype/demo)
    allow_credentials=True,
    allow_methods=["*"],           # Allow all HTTP methods
    allow_headers=["*"],           # Allow all headers
)

# Redis client — connects to the Redis container via Docker networking
# decode_responses=True means we get Python strings instead of bytes
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True,
    socket_connect_timeout=5,
)


# ============================================================
# Simulated "Database" — returns fake user data after a delay
# ============================================================

# This simulates what a real database query would return.
# In production, this would be a PostgreSQL/MySQL query.
FAKE_DB = {
    "user": {
        "name": "Aditi Sharma",
        "email": "demo@example.com",
        "role": "Senior Engineer",
        "joined": "2024-03-15",
        "posts": 142,
        "followers": 2847,
    },
    "feed": {
        "items": [
            {"id": 1, "text": "Deployed v2.3 to production", "time": "2 min ago"},
            {"id": 2, "text": "Fixed caching bug in feed service", "time": "15 min ago"},
            {"id": 3, "text": "Code review: auth middleware", "time": "1 hour ago"},
        ],
        "total": 847,
        "unread": 12,
    },
    "post": {
        "id": 42,
        "title": "Understanding Load Balancers",
        "author": "Shwetabh",
        "views": 15420,
        "likes": 892,
        "comments": 67,
    },
    "stats": {
        "daily_active_users": 14520,
        "requests_per_second": 8742,
        "avg_response_time_ms": 23,
        "cache_hit_rate": 0.985,
        "uptime_percent": 99.97,
    },
}


async def simulate_db_query(query_type: str) -> dict:
    """
    Simulate a slow database query.
    In a real app, this would be:  SELECT * FROM users WHERE id = ?
    The asyncio.sleep simulates network + query latency.
    """
    await asyncio.sleep(DB_DELAY_MS / 1000.0)  # Convert ms to seconds
    return FAKE_DB.get(query_type, {"message": "No data found"})


# ============================================================
# Endpoint: Health Check
# ============================================================

@app.get("/")
async def health_check():
    """
    Simple health check endpoint.
    Nginx uses this to verify the server is alive.
    Returns the server's unique ID so we can see load balancing in action.
    """
    try:
        redis_ping = redis_client.ping()
    except Exception:
        redis_ping = False

    return {
        "status": "ok",
        "server_id": SERVER_ID,
        "redis_connected": redis_ping,
        "message": f"Backend {SERVER_ID} is running",
    }


# ============================================================
# Endpoint: Data with Caching
# ============================================================

@app.get("/data")
async def get_data(
    request: Request,
    user: str = Query(default="user", description="Query type: user, feed, post, stats"),
):
    """
    Main data endpoint with Redis caching.

    Flow:
    1. Check if data exists in Redis cache
    2. If YES (cache hit)  → return immediately (fast, ~1-5ms)
    3. If NO  (cache miss) → query "database" (slow, ~200ms),
                              store result in Redis, then return

    The response always includes:
    - server_id: which backend handled this request
    - source: "cache" or "database"
    - response_time_ms: how long the request took
    - data: the actual payload
    """
    start_time = time.time()

    # Build the Redis cache key
    cache_key = f"cache:{user}"

    try:
        # Step 1: Try to get data from Redis cache
        cached_data = redis_client.get(cache_key)

        if cached_data:
            # ✅ CACHE HIT — data was already in Redis
            elapsed_ms: float = float(round((time.time() - start_time) * 1000, 2))  # type: ignore
            return JSONResponse(content={
                "server_id": SERVER_ID,
                "source": "cache",
                "response_time_ms": elapsed_ms,
                "cache_key": cache_key,
                "ttl_remaining": redis_client.ttl(cache_key),
                "data": json.loads(cached_data),
            })

        # ❌ CACHE MISS — need to query the "database"
        db_result = await simulate_db_query(user)

        # Store the result in Redis with a TTL (auto-expires)
        redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(db_result),
        )

        elapsed_ms: float = float(round((time.time() - start_time) * 1000, 2))  # type: ignore
        return JSONResponse(content={
            "server_id": SERVER_ID,
            "source": "database",
            "response_time_ms": elapsed_ms,
            "cache_key": cache_key,
            "ttl_remaining": CACHE_TTL,
            "data": db_result,
        })

    except redis.ConnectionError:
        # If Redis is down, fall back to direct "DB" query (no caching)
        db_result = await simulate_db_query(user)
        elapsed_ms: float = float(round((time.time() - start_time) * 1000, 2))  # type: ignore
        return JSONResponse(content={
            "server_id": SERVER_ID,
            "source": "database (redis unavailable)",
            "response_time_ms": elapsed_ms,
            "data": db_result,
        })


# ============================================================
# Endpoint: Rate Limiter Test
# ============================================================

@app.get("/rate-test")
async def rate_limit_test(request: Request):
    """
    Rate-limited endpoint to demonstrate request throttling.

    Uses Redis INCR + EXPIRE pattern:
    - Each IP gets a counter in Redis
    - Counter increments with each request
    - After 10 requests in 60 seconds → HTTP 429 (Too Many Requests)
    - Counter auto-resets when the Redis key expires

    Headers returned:
    - X-RateLimit-Limit: max requests allowed
    - X-RateLimit-Remaining: requests left in window
    - X-RateLimit-Reset: seconds until window resets
    """

    # Get the client's real IP address
    # X-Real-IP is set by Nginx when proxying requests
    client_ip = request.headers.get("X-Real-IP", request.client.host)

    try:
        is_allowed, remaining, ttl = await check_rate_limit(
            redis_client,
            client_ip,
            limit=RATE_LIMIT,
            window=RATE_WINDOW,
        )

        # Common headers for rate limit transparency
        headers = {
            "X-RateLimit-Limit": str(RATE_LIMIT),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(ttl),
            "X-Server-ID": SERVER_ID,
        }

        if is_allowed:
            # ✅ Request allowed — under the rate limit
            return JSONResponse(
                content={
                    "status": "ok",
                    "server_id": SERVER_ID,
                    "client_ip": client_ip,
                    "remaining": remaining,
                    "limit": RATE_LIMIT,
                    "window_seconds": RATE_WINDOW,
                    "reset_in": ttl,
                    "message": f"Request allowed. {remaining} requests remaining.",
                },
                headers=headers,
            )
        else:
            # 🚫 Rate limit exceeded — return 429
            return JSONResponse(
                status_code=429,
                content={
                    "status": "rate_limited",
                    "server_id": SERVER_ID,
                    "client_ip": client_ip,
                    "remaining": 0,
                    "limit": RATE_LIMIT,
                    "window_seconds": RATE_WINDOW,
                    "reset_in": ttl,
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Try again in {ttl} seconds.",
                },
                headers=headers,
            )

    except redis.ConnectionError:
        # If Redis is down, allow the request (fail-open strategy)
        # In production, you might choose fail-closed instead
        return JSONResponse(content={
            "status": "ok",
            "server_id": SERVER_ID,
            "client_ip": client_ip,
            "remaining": -1,
            "message": "Rate limiter unavailable (Redis down). Request allowed.",
        })


# ============================================================
# Endpoint: Flush Cache
# ============================================================

@app.get("/flush-cache")
async def flush_cache():
    """
    Clear all cached data from Redis.
    Used by the frontend's "Clear Cache" button.
    Only deletes keys starting with "cache:" — doesn't touch rate limit keys.
    """
    try:
        # Find all cache keys and delete them
        cache_keys = redis_client.keys("cache:*")
        if cache_keys:
            redis_client.delete(*cache_keys)

        return {
            "status": "ok",
            "server_id": SERVER_ID,
            "keys_deleted": len(cache_keys) if cache_keys else 0,
            "message": "Cache cleared successfully.",
        }
    except redis.ConnectionError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "server_id": SERVER_ID,
                "message": "Unable to connect to Redis.",
            },
        )


# ============================================================
# Startup Event
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Log server startup info."""
    print(f"{'='*50}")
    print(f"  Traffic Management Backend — {SERVER_ID}")
    print(f"  Redis: {REDIS_HOST}:{REDIS_PORT}")
    print(f"  Cache TTL: {CACHE_TTL}s")
    print(f"  Rate Limit: {RATE_LIMIT} req / {RATE_WINDOW}s")
    print(f"{'='*50}")
