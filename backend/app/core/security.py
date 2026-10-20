"""Password hashing and JWT creation."""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hasher = PasswordHash.recommended()
_dummy_hash: str | None = None


class InvalidToken(Exception):
    """Raised when a JWT is missing, expired, or the wrong type."""


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password("dummy-password-value")
    if not password_hash:
        password_hasher.verify(password, _dummy_hash)
        return False
    return bool(password_hasher.verify(password, password_hash))


def _secret() -> str:
    secret = get_settings().jwt_secret
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters")
    return secret


def create_access_token(user_id: int, role: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def create_refresh_token(user_id: int, role: str, jti: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "refresh",
        "jti": jti,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_refresh_token_expire_minutes),
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, _secret(), algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise InvalidToken from exc
    if payload.get("type") != expected_type or "sub" not in payload:
        raise InvalidToken
    if expected_type == "refresh" and not payload.get("jti"):
        raise InvalidToken
    return payload
