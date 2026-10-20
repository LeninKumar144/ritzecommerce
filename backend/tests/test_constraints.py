"""Database constraint tests."""

from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.models import Category, Product, Role
from app.schemas import ProductCreate


def _category() -> Category:
    return Category(name="Shirts", slug="shirts", description="Cotton shirts")


def _product(category_id: int, **overrides) -> Product:
    values = {
        "category_id": category_id,
        "name": "Cotton shirt",
        "slug": "cotton-shirt",
        "sku": "SHIRT-001",
        "brand": "Ritz",
        "description": "Woven cotton shirt",
        "specifications": {"material": "cotton"},
        "price": Decimal("1499.00"),
        "discount_percent": Decimal("10.00"),
        "tax_rate": Decimal("18.00"),
        "stock_quantity": 5,
    }
    values.update(overrides)
    return Product(**values)


def test_migration_seeds_customer_and_admin_roles(db_session) -> None:
    names = set(db_session.scalars(select(Role.name)))
    assert names == {"ADMIN", "CUSTOMER"}


def test_negative_price_is_rejected(db_session) -> None:
    category = _category()
    db_session.add(category)
    db_session.flush()
    db_session.add(_product(category.id, price=Decimal("-1.00")))
    with pytest.raises((IntegrityError, OperationalError)):
        db_session.flush()


def test_duplicate_sku_is_rejected(db_session) -> None:
    category = _category()
    db_session.add(category)
    db_session.flush()
    db_session.add(_product(category.id))
    db_session.flush()
    db_session.add(_product(category.id, slug="cotton-shirt-2"))
    with pytest.raises((IntegrityError, OperationalError)):
        db_session.flush()


def test_product_schema_rejects_negative_price() -> None:
    with pytest.raises(ValidationError):
        ProductCreate(
            name="Cotton shirt",
            slug="cotton-shirt",
            sku="SHIRT-001",
            category_id=1,
            brand="Ritz",
            description="Woven cotton shirt",
            price=Decimal("-1.00"),
        )
