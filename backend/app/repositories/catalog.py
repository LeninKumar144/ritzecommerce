"""Persistence helpers. They do not commit."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, Product, Role


class RoleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_names(self) -> list[str]:
        return list(self.session.scalars(select(Role.name).order_by(Role.name)))


class CategoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, category: Category) -> Category:
        self.session.add(category)
        return category


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, product: Product) -> Product:
        self.session.add(product)
        return product

    def get_by_sku(self, sku: str) -> Product | None:
        return self.session.scalar(select(Product).where(Product.sku == sku))
