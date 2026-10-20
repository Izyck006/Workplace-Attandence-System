"""In-memory thread-safe rate limiter middleware for FastAPI."""
import time
from collections import defaultdict
from threading import Lock
from fastapi import Request
from fastapi.responses import JSONResponse


class RateLimiter:
    def __init__(self):
        self._records = defaultdict(list)
        self._lock = Lock()
        self._last_cleanup = time.time()

    def get_client_ip(self, request: Request) -> str:
        # Check standard reverse-proxy headers (Render / Cloudflare / AWS)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()
        return request.client.host if request.client else "127.0.0.1"

    def check(self, key: str, max_requests: int, window_seconds: int = 60) -> tuple[bool, int]:
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            # Periodic cleanup every 5 minutes
            if now - self._last_cleanup > 300:
                self._cleanup_locked(now)

            timestamps = [t for t in self._records[key] if t > cutoff]
            if len(timestamps) >= max_requests:
                earliest = timestamps[0]
                retry_after = max(1, int(window_seconds - (now - earliest)))
                self._records[key] = timestamps
                return False, retry_after

            timestamps.append(now)
            self._records[key] = timestamps
            return True, 0

    def _cleanup_locked(self, now: float):
        keys_to_delete = []
        for key, timestamps in self._records.items():
            valid = [t for t in timestamps if t > now - 120]
            if not valid:
                keys_to_delete.append(key)
            else:
                self._records[key] = valid
        for k in keys_to_delete:
            del self._records[k]
        self._last_cleanup = now


rate_limiter = RateLimiter()
