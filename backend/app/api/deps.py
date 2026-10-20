"""Request dependencies for CSRF and the current user."""

import secrets

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.cookies import CSRF_COOKIE, CSRF_HEADER, ACCESS_COOKIE
from app.core.security import InvalidToken, decode_token
from app.db.session import get_db
from app.models import User
from app.models.enums import RoleName
from app.repositories.users import UserRepository

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def enforce_csrf(request: Request) -> None:
    if request.method not in UNSAFE_METHODS:
        return
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get(CSRF_HEADER)
    if not cookie or not header or len(cookie) != len(header) or not secrets.compare_digest(cookie, header):
        raise HTTPException(status_code=403, detail="CSRF check failed")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (InvalidToken, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Not authenticated") from exc
    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role.name != RoleName.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access is required")
    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        return None
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (InvalidToken, ValueError):
        return None
    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        return None
    return user
