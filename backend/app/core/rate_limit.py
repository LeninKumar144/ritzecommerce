"""In-memory login rate limit. It resets when the process restarts."""

import threading
import time

from fastapi import HTTPException, Request

from app.core.config import get_settings


class LoginRateLimiter:
    def __init__(self) -> None:
        self._attempts: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._attempts.clear()

    def check(self, key: str) -> None:
        settings = get_settings()
        now = time.monotonic()
        window = settings.login_rate_window_seconds
        with self._lock:
            recent = [stamp for stamp in self._attempts.get(key, []) if now - stamp < window]
            if len(recent) >= settings.login_rate_limit:
                raise HTTPException(status_code=429, detail="Too many login attempts")
            recent.append(now)
            self._attempts[key] = recent


login_rate_limiter = LoginRateLimiter()


def enforce_login_rate_limit(request: Request) -> None:
    host = request.client.host if request.client else "unknown"
    login_rate_limiter.check(host)
