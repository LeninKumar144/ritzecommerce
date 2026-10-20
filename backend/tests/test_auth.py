"""Authentication API tests. These commit to product_shopping_test and then delete the user."""

import asyncio
import uuid

import httpx
import pytest
from sqlalchemy import select

from app.core.cookies import CSRF_COOKIE, CSRF_HEADER
from app.core.rate_limit import login_rate_limiter
from app.db.session import SessionLocal
from app.main import app
from app.models import User
from app.services.auth import require_admin_seed_config, seed_admin_user

transport = httpx.ASGITransport(app=app)


@pytest.fixture(autouse=True)
def _reset_login_limit() -> None:
    login_rate_limiter.reset()


def _delete_user(email: str) -> None:
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == email))
        if user is not None:
            session.delete(user)
            session.commit()


async def _client() -> httpx.AsyncClient:
    client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    await client.get("/api/v1/health")
    return client


def _csrf(client: httpx.AsyncClient) -> dict[str, str]:
    token = client.cookies.get(CSRF_COOKIE)
    assert token
    return {CSRF_HEADER: token}


def test_register_login_logout_and_admin_block() -> None:
    email = f"customer-{uuid.uuid4().hex}@example.com"
    password = "at-least-8-chars"

    async def scenario() -> None:
        client = await _client()
        try:
            registered = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": "Asha Rao",
                    "phone": "9876543210",
                },
                headers=_csrf(client),
            )
            assert registered.status_code == 201
            body = registered.json()
            assert body["email"] == email
            assert body["role"] == "CUSTOMER"
            assert "password" not in body
            cookie_headers = registered.headers.get_list("set-cookie")
            assert any("access_token=" in item and "HttpOnly" in item for item in cookie_headers)

            me = await client.get("/api/v1/auth/me")
            assert me.status_code == 200
            assert me.json()["full_name"] == "Asha Rao"

            forbidden = await client.get("/api/v1/admin/health")
            assert forbidden.status_code == 403

            logged_out = await client.post("/api/v1/auth/logout", headers=_csrf(client))
            assert logged_out.status_code == 204
            assert (await client.get("/api/v1/auth/me")).status_code == 401

            await client.get("/api/v1/health")
            logged_in = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password},
                headers=_csrf(client),
            )
            assert logged_in.status_code == 200
            assert logged_in.json()["role"] == "CUSTOMER"
        finally:
            await client.aclose()

    try:
        asyncio.run(scenario())
    finally:
        _delete_user(email)


def test_wrong_password_and_unknown_user_share_one_message() -> None:
    email = f"customer-{uuid.uuid4().hex}@example.com"

    async def scenario() -> None:
        client = await _client()
        try:
            await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "at-least-8-chars", "full_name": "Asha Rao"},
                headers=_csrf(client),
            )
            wrong = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "wrong-password"},
                headers=_csrf(client),
            )
            unknown = await client.post(
                "/api/v1/auth/login",
                json={"email": f"missing-{uuid.uuid4().hex}@example.com", "password": "wrong-password"},
                headers=_csrf(client),
            )
            assert wrong.status_code == 401
            assert unknown.status_code == 401
            assert wrong.json()["detail"] == unknown.json()["detail"]
        finally:
            await client.aclose()

    try:
        asyncio.run(scenario())
    finally:
        _delete_user(email)


def test_inactive_user_cannot_login() -> None:
    email = f"customer-{uuid.uuid4().hex}@example.com"

    async def scenario() -> None:
        client = await _client()
        try:
            created = await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "at-least-8-chars", "full_name": "Asha Rao"},
                headers=_csrf(client),
            )
            assert created.status_code == 201
            with SessionLocal() as session:
                user = session.scalar(select(User).where(User.email == email))
                assert user is not None
                user.is_active = False
                session.commit()
            inactive = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "at-least-8-chars"},
                headers=_csrf(client),
            )
            assert inactive.status_code == 403
        finally:
            await client.aclose()

    try:
        asyncio.run(scenario())
    finally:
        _delete_user(email)


def test_register_without_csrf_is_forbidden() -> None:
    async def scenario() -> None:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"customer-{uuid.uuid4().hex}@example.com",
                    "password": "at-least-8-chars",
                    "full_name": "Asha Rao",
                },
            )
            assert response.status_code == 403

    asyncio.run(scenario())


def test_admin_seed_creates_admin(db_session) -> None:
    email = f"admin-{uuid.uuid4().hex}@example.com"
    assert seed_admin_user(db_session, email, "at-least-8-chars") == "created"
    user = db_session.scalar(select(User).where(User.email == email))
    assert user is not None
    assert user.role.name == "ADMIN"


def test_admin_seed_requires_configuration() -> None:
    with pytest.raises(ValueError):
        require_admin_seed_config("", "")
