"""Public product routes."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.db.session import get_db
from app.models import User
from app.models.enums import RoleName
from app.schemas.catalog import ProductDetail, ProductList, ProductSort
from app.services.catalog import CatalogError, CatalogService

router = APIRouter(prefix="/products", tags=["products"])


def _is_admin(user: User | None) -> bool:
    return user is not None and user.role.name == RoleName.ADMIN.value


@router.get("/brands", response_model=list[str])
def list_brands(db: Session = Depends(get_db)) -> list[str]:
    return CatalogService(db).list_brands()


@router.get("", response_model=ProductList)
def list_products(
    search: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    in_stock: bool | None = None,
    featured: bool | None = None,
    sort: ProductSort = "newest",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ProductList:
    return CatalogService(db).list_products(
        search=search,
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        featured=featured,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/{slug}", response_model=ProductDetail)
def get_product(
    slug: str,
    review_page: int = Query(default=1, ge=1),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> ProductDetail:
    try:
        return CatalogService(db).get_product(
            slug,
            include_inactive=_is_admin(user),
            review_page=review_page,
            review_page_size=5,
        )
    except CatalogError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
