import os
from upstash_redis import Redis
from upstash_ratelimit import Ratelimit, FixedWindow
from fastapi import HTTPException

ratelimit_redis = None

def get_ratelimit_redis():
    global ratelimit_redis
    if ratelimit_redis is None and os.getenv("UPSTASH_REDIS_REST_URL"):
        ratelimit_redis = Redis.from_env()
    return ratelimit_redis


def ratelimit(path: str, max_requests: int, seconds: int):
    redis = get_ratelimit_redis()
    if redis is None:
        return  # Skip rate limiting if not configured

    rl = Ratelimit(
        redis=redis,
        limiter=FixedWindow(max_requests=max_requests, window=seconds),
        prefix="ratelimit:public",
    )

    response = rl.limit(path)

    if not response.allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {response.reset_after} seconds.",
            headers={"Retry-After": str(response.reset)},
        )
