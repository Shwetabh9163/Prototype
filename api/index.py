"""Vercel API entrypoint using FastAPI

This module is deployed as a serverless function on Vercel.  By placing
it under `api/index.py` we ensure that requests to `/api/*` are handled by
this application, using the paths defined below.

The original prototype used Docker, Nginx and multiple backend instances;
here we simply expose the same endpoints from a single FastAPI app.  A
Redis instance is still required if you want to exercise caching or rate
limiting; you can provide a hosted Redis URL via the `REDIS_URL`
environment variable (Upstash works nicely with Vercel).  When no
`REDIS_URL` is set the code falls back to `REDIS_HOST`/`REDIS_PORT` which
is convenient for local development.
"""

import os
import time
import asyncio
import json

from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis

from api.rate_limit import check_rate_limit

# ------------------------------------------------------------
# Configuration (env vars)
# ------------------------------------------------------------
SERVER_ID = os.getenv("SERVER_ID", "server-vercel")

# Redis connection: prefer a full URL (Upstash or other cloud Redis).
REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    # `from_url` supports both redis:// and rediss:// schemes.
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
else:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=0,
        decode_responses=True,
        socket_connect_timeout=5,
    )

CACHE_TTL = int(os.getenv("CACHE_TTL", 30))
DB_DELAY_MS = int(os.getenv("DB_DELAY_MS", 200))
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 10))
RATE_WINDOW = int(os.getenv("RATE_WINDOW", 60))

# ------------------------------------------------------------
# FastAPI application setup
# ------------------------------------------------------------
app = FastAPI(
    title=f"Traffic Management Backend ({SERVER_ID})",
    description="Traffic Management Prototype — FastAPI Backend Server",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Fake database for demo purposes
# ------------------------------------------------------------
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
    await asyncio.sleep(DB_DELAY_MS / 1000.0)
    return FAKE_DB.get(query_type, {"message": "No data found"})


# ------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------

@app.get("/")
async def health_check():
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


@app.get("/data")
async def get_data(request: Request, user: str = Query(default="user")):
    start_time = time.time()
    cache_key = f"cache:{user}"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            elapsed_ms = float(round((time.time() - start_time) * 1000, 2))
            return JSONResponse(content={
                "server_id": SERVER_ID,
                "source": "cache",
                "response_time_ms": elapsed_ms,
                "cache_key": cache_key,
                "ttl_remaining": redis_client.ttl(cache_key),
                "data": json.loads(cached_data),
            })
        db_result = await simulate_db_query(user)
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(db_result))
        elapsed_ms = float(round((time.time() - start_time) * 1000, 2))
        return JSONResponse(content={
            "server_id": SERVER_ID,
            "source": "database",
            "response_time_ms": elapsed_ms,
            "cache_key": cache_key,
            "ttl_remaining": CACHE_TTL,
            "data": db_result,
        })
    except redis.ConnectionError:
        db_result = await simulate_db_query(user)
        elapsed_ms = float(round((time.time() - start_time) * 1000, 2))
        return JSONResponse(content={
            "server_id": SERVER_ID,
            "source": "database (redis unavailable)",
            "response_time_ms": elapsed_ms,
            "data": db_result,
        })


@app.get("/rate-test")
async def rate_limit_test(request: Request):
    client_ip = request.headers.get("X-Real-IP", request.client.host)
    try:
        is_allowed, remaining, ttl = await check_rate_limit(
            redis_client,
            client_ip,
            limit=RATE_LIMIT,
            window=RATE_WINDOW,
        )
        headers = {
            "X-RateLimit-Limit": str(RATE_LIMIT),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(ttl),
            "X-Server-ID": SERVER_ID,
        }
        if is_allowed:
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
        return JSONResponse(content={
            "status": "ok",
            "server_id": SERVER_ID,
            "client_ip": client_ip,
            "remaining": -1,
            "message": "Rate limiter unavailable (Redis down). Request allowed.",
        })


@app.get("/flush-cache")
async def flush_cache():
    try:
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


@app.on_event("startup")
async def startup_event():
    print("=" * 50)
    print(f"  Traffic Management Backend — {SERVER_ID}")
    print(f"  Redis URL: {REDIS_URL or f'{REDIS_HOST}:{REDIS_PORT}'}")
    print(f"  Cache TTL: {CACHE_TTL}s")
    print(f"  Rate Limit: {RATE_LIMIT} req / {RATE_WINDOW}s")
    print("=" * 50)
