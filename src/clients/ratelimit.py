import os
import json
import time
import threading
from pathlib import Path
from fastapi import HTTPException

# Default: 100 requests per hour - sensible for an AI-powered API with costs
DEFAULT_MAX_REQUESTS = 100
DEFAULT_WINDOW_SECONDS = 3600  # 1 hour

# Storage path - use /data for Fly persistent volume, fallback to /tmp
STORAGE_DIR = Path(os.getenv("RATELIMIT_STORAGE_DIR", "/data/ratelimit"))
STORAGE_FILE = STORAGE_DIR / "limits.json"

_lock = threading.Lock()


def _ensure_storage():
    """Ensure storage directory exists."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _load_data() -> dict:
    """Load rate limit data from file."""
    try:
        if STORAGE_FILE.exists():
            with open(STORAGE_FILE, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def _save_data(data: dict):
    """Save rate limit data to file."""
    _ensure_storage()
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f)


def _cleanup_expired(data: dict, window_seconds: int) -> dict:
    """Remove expired entries."""
    now = time.time()
    cutoff = now - window_seconds
    return {
        key: [ts for ts in timestamps if ts > cutoff]
        for key, timestamps in data.items()
        if any(ts > cutoff for ts in timestamps)
    }


def ratelimit(
    key: str,
    max_requests: int = DEFAULT_MAX_REQUESTS,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
):
    """
    Simple file-based rate limiting using sliding window.

    Args:
        key: Unique identifier for the rate limit (e.g., endpoint path, IP, user ID)
        max_requests: Maximum requests allowed in the window (default: 100)
        window_seconds: Time window in seconds (default: 3600 = 1 hour)

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    now = time.time()
    cutoff = now - window_seconds

    with _lock:
        data = _load_data()

        # Cleanup expired entries periodically
        data = _cleanup_expired(data, window_seconds)

        # Get timestamps for this key
        timestamps = data.get(key, [])

        # Filter to only timestamps within the window
        timestamps = [ts for ts in timestamps if ts > cutoff]

        if len(timestamps) >= max_requests:
            # Calculate time until oldest request expires
            oldest = min(timestamps)
            reset_after = int(oldest + window_seconds - now) + 1

            _save_data(data)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {reset_after} seconds.",
                headers={"Retry-After": str(reset_after)},
            )

        # Add current timestamp
        timestamps.append(now)
        data[key] = timestamps
        _save_data(data)
