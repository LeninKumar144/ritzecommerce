"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.cookies import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from app.core.rate_limit import enforce_login_rate_limit
from app.db.session import get_db
from app.models import User
from app.schemas.users import AuthUser, LoginRequest, UserCreate
from app.services.auth import (
    AuthService,
    EmailAlreadyRegistered,
    InactiveAccount,
    InvalidCredentials,
    InvalidSession,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_user(user: User) -> AuthUser:
    return AuthUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role.name,
        is_active=user.is_active,
    )


@router.post("/register", response_model=AuthUser, status_code=201)
def register(data: UserCreate, response: Response, db: Session = Depends(get_db)) -> AuthUser:
    try:
        result = AuthService(db).register(data)
    except EmailAlreadyRegistered as exc:
        raise HTTPException(status_code=409, detail="Email is already registered") from exc
    set_auth_cookies(response, result.access_token, result.refresh_token)
    return _auth_user(result.user)


@router.post("/login", response_model=AuthUser)
def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthUser:
    enforce_login_rate_limit(request)
    try:
        result = AuthService(db).login(data.email, data.password)
    except InvalidCredentials as exc:
        raise HTTPException(status_code=401, detail="Invalid email or password") from exc
    except InactiveAccount as exc:
        raise HTTPException(status_code=403, detail="Account is inactive") from exc
    set_auth_cookies(response, result.access_token, result.refresh_token)
    return _auth_user(result.user)


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    AuthService(db).logout(user)
    clear_auth_cookies(response)
    response.status_code = 204
    return response


@router.post("/refresh", response_model=AuthUser)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> AuthUser:
    try:
        result = AuthService(db).refresh(request.cookies.get(REFRESH_COOKIE))
    except InvalidSession as exc:
        raise HTTPException(status_code=401, detail="Invalid session") from exc
    set_auth_cookies(response, result.access_token, result.refresh_token)
    return _auth_user(result.user)


@router.get("/me", response_model=AuthUser)
def me(user: User = Depends(get_current_user)) -> AuthUser:
    return _auth_user(user)
