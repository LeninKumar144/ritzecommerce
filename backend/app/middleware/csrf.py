"""Issues a CSRF cookie when the browser does not already have one."""

import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.cookies import CSRF_COOKIE, set_csrf_cookie


class EnsureCsrfCookieMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if CSRF_COOKIE not in request.cookies:
            set_csrf_cookie(response, secrets.token_urlsafe(32))
        return response
