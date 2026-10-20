"""Registration, login, refresh, logout, and admin seeding."""

import secrets
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    InvalidToken,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.models.enums import RoleName
from app.repositories.users import UserRepository
from app.schemas.users import UserCreate


class EmailAlreadyRegistered(Exception):
    """The email is already stored."""


class InvalidCredentials(Exception):
    """The email or password does not match."""


class InactiveAccount(Exception):
    """The account exists but is disabled."""


class InvalidSession(Exception):
    """The refresh token is missing, expired, or already rotated."""


@dataclass
class AuthResult:
    user: User
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def register(self, data: UserCreate) -> AuthResult:
        email = data.email.lower()
        if self.users.get_by_email(email) is not None:
            raise EmailAlreadyRegistered
        role = self.users.get_role(RoleName.CUSTOMER.value)
        user = User(
            role=role,
            email=email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
            is_active=True,
        )
        self.session.add(user)
        return self._start_session(user)

    def login(self, email: str, password: str) -> AuthResult:
        user = self.users.get_by_email(email.lower())
        password_ok = verify_password(password, user.password_hash if user else None)
        if user is None or not password_ok:
            raise InvalidCredentials
        if not user.is_active:
            raise InactiveAccount
        return self._start_session(user)

    def refresh(self, raw_token: str | None) -> AuthResult:
        if not raw_token:
            raise InvalidSession
        try:
            payload = decode_token(raw_token, expected_type="refresh")
            user_id = int(payload["sub"])
        except (InvalidToken, ValueError) as exc:
            raise InvalidSession from exc
        user = self.users.get_by_id(user_id)
        if user is None or not user.is_active or user.refresh_token_jti != payload["jti"]:
            raise InvalidSession
        return self._start_session(user)

    def logout(self, user: User) -> None:
        user.refresh_token_jti = None
        self.session.commit()

    def _start_session(self, user: User) -> AuthResult:
        user.refresh_token_jti = secrets.token_urlsafe(16)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise EmailAlreadyRegistered from exc
        self.session.refresh(user)
        role_name = user.role.name
        return AuthResult(
            user=user,
            access_token=create_access_token(user.id, role_name),
            refresh_token=create_refresh_token(user.id, role_name, user.refresh_token_jti),
        )


def require_admin_seed_config(email: str, password: str) -> None:
    if not email or not password:
        raise ValueError("ADMIN_EMAIL and ADMIN_PASSWORD are required")
    if len(password) < 8:
        raise ValueError("ADMIN_PASSWORD must be at least 8 characters")


def seed_admin_user(session: Session, email: str, password: str) -> str:
    require_admin_seed_config(email, password)
    users = UserRepository(session)
    normalized = email.lower()
    admin_role = users.get_role(RoleName.ADMIN.value)
    existing = users.get_by_email(normalized)
    if existing is None:
        session.add(
            User(
                role=admin_role,
                email=normalized,
                password_hash=hash_password(password),
                full_name="Administrator",
                is_active=True,
            )
        )
        session.commit()
        return "created"
    existing.role = admin_role
    existing.password_hash = hash_password(password)
    existing.is_active = True
    session.commit()
    return "updated"
