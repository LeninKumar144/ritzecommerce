"""Catalog API tests."""

import asyncio
import uuid
from decimal import Decimal

import httpx
from sqlalchemy import select

from app.core.cookies import CSRF_COOKIE, CSRF_HEADER
from app.core.rate_limit import login_rate_limiter
from app.db.session import SessionLocal
from app.main import app
from app.models import Category, Product, User
from app.services.auth import seed_admin_user

transport = httpx.ASGITransport(app=app)
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _reset_limit() -> None:
    login_rate_limiter.reset()


async def _client() -> httpx.AsyncClient:
    client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    await client.get("/api/v1/health")
    return client


def _csrf(client: httpx.AsyncClient) -> dict[str, str]:
    token = client.cookies.get(CSRF_COOKIE)
    assert token
    return {CSRF_HEADER: token}


def _cleanup(email: str, slug: str) -> None:
    with SessionLocal() as session:
        category = session.scalar(select(Category).where(Category.slug == slug))
        if category is not None:
            for product in list(category.products):
                for image in list(product.images):
                    session.delete(image)
                session.delete(product)
            session.delete(category)
        user = session.scalar(select(User).where(User.email == email))
        if user is not None:
            session.delete(user)
        session.commit()


def test_catalog_filters_hide_inactive_products_and_reject_bad_images() -> None:
    suffix = uuid.uuid4().hex[:8]
    email = f"admin-{suffix}@example.com"
    slug = f"shirts-{suffix}"
    sku = f"SKU-{suffix}"

    async def scenario() -> None:
        _reset_limit()
        with SessionLocal() as session:
            seed_admin_user(session, email, "at-least-8-chars")
        client = await _client()
        try:
            logged_in = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "at-least-8-chars"},
                headers=_csrf(client),
            )
            assert logged_in.status_code == 200
            headers = _csrf(client)
            created = await client.post(
                "/api/v1/admin/categories",
                json={"name": f"Shirts {suffix}", "slug": slug, "description": "Cotton shirts"},
                headers=headers,
            )
            assert created.status_code == 201
            category_id = created.json()["id"]
            product = await client.post(
                "/api/v1/admin/products",
                json={
                    "name": f"Cotton shirt {suffix}",
                    "sku": sku,
                    "category_id": category_id,
                    "brand": "Ritz",
                    "description": "Woven cotton shirt",
                    "specifications": {"material": "cotton"},
                    "price": "1499.00",
                    "discount_percent": "10.00",
                    "stock_quantity": 4,
                    "is_featured": True,
                },
                headers=headers,
            )
            assert product.status_code == 201
            product_id = product.json()["id"]
            product_slug = product.json()["slug"]
            cheap = await client.post(
                "/api/v1/admin/products",
                json={
                    "name": f"Plain tee {suffix}",
                    "sku": f"{sku}-TEE",
                    "category_id": category_id,
                    "brand": "Other",
                    "description": "Basic tee",
                    "price": "499.00",
                    "stock_quantity": 0,
                },
                headers=headers,
            )
            assert cheap.status_code == 201
            hidden = await client.post(
                "/api/v1/admin/products",
                json={
                    "name": f"Hidden shirt {suffix}",
                    "sku": f"{sku}-HIDE",
                    "category_id": category_id,
                    "brand": "Ritz",
                    "description": "Not for sale",
                    "price": "999.00",
                    "is_active": False,
                },
                headers=headers,
            )
            assert hidden.status_code == 201

            listed = await client.get("/api/v1/products", params={"search": suffix, "category": slug, "sort": "price_asc"})
            assert listed.status_code == 200
            body = listed.json()
            assert body["total"] == 2
            assert [item["brand"] for item in body["items"]] == ["Other", "Ritz"]
            assert body["items"][1]["selling_price"] == "1349.10"
            assert body["items"][1]["in_stock"] is True

            priced = await client.get("/api/v1/products", params={"search": suffix, "min_price": "1000", "brand": "Ritz"})
            assert priced.json()["total"] == 1
            stocked = await client.get("/api/v1/products", params={"search": suffix, "in_stock": False})
            assert stocked.json()["total"] == 1
            featured = await client.get("/api/v1/products", params={"search": suffix, "featured": True})
            assert featured.json()["total"] == 1

            anonymous = httpx.AsyncClient(transport=transport, base_url="http://testserver")
            missing = await anonymous.get(f"/api/v1/products/{hidden.json()['slug']}")
            assert missing.status_code == 404
            visible = await client.get(f"/api/v1/products/{hidden.json()['slug']}")
            assert visible.status_code == 200
            await anonymous.aclose()

            duplicate = await client.post(
                "/api/v1/admin/products",
                json={
                    "name": "Duplicate",
                    "sku": sku,
                    "category_id": category_id,
                    "brand": "Ritz",
                    "description": "Same sku",
                    "price": "10.00",
                },
                headers=headers,
            )
            assert duplicate.status_code == 409

            rejected = await client.post(
                f"/api/v1/admin/products/{product_id}/images",
                files={"file": ("note.gif", b"GIF89a", "image/gif")},
                headers=headers,
            )
            assert rejected.status_code == 400
            accepted = await client.post(
                f"/api/v1/admin/products/{product_id}/images",
                files={"file": ("dot.png", PNG, "image/png")},
                data={"is_primary": "true"},
                headers=headers,
            )
            assert accepted.status_code == 201

            detail = await client.get(f"/api/v1/products/{product_slug}")
            assert detail.status_code == 200
            assert detail.json()["sku"] == sku
            assert detail.json()["gallery"]

            customer = await _client()
            await customer.post(
                "/api/v1/auth/register",
                json={"email": f"shopper-{suffix}@example.com", "password": "at-least-8-chars", "full_name": "Asha Rao"},
                headers=_csrf(customer),
            )
            forbidden = await customer.post(
                "/api/v1/admin/products",
                json={
                    "name": "Nope",
                    "sku": f"{sku}-NO",
                    "category_id": category_id,
                    "brand": "Ritz",
                    "description": "Denied",
                    "price": "10.00",
                },
                headers=_csrf(customer),
            )
            assert forbidden.status_code == 403
            await customer.aclose()

            blocked = await client.delete(f"/api/v1/admin/categories/{category_id}", headers=headers)
            assert blocked.status_code == 409
        finally:
            await client.aclose()

    try:
        asyncio.run(scenario())
    finally:
        _cleanup(email, slug)
        _cleanup(f"shopper-{suffix}@example.com", slug)
