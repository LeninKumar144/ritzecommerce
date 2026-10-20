"""Catalog request and response schemas."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    image_url: str | None
    is_active: bool


class CategoryPublic(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    image_url: str | None


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=220)
    sku: str = Field(min_length=1, max_length=64)
    category_id: int = Field(gt=0)
    brand: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1)
    specifications: dict[str, str] = Field(default_factory=dict)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, max_digits=5, decimal_places=2)
    tax_rate: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    stock_quantity: int = Field(default=0, ge=0)
    is_active: bool = True
    is_featured: bool = False


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=220)
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    category_id: int | None = Field(default=None, gt=0)
    brand: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1)
    specifications: dict[str, str] | None = None
    price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    tax_rate: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    is_featured: bool | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    sku: str
    category_id: int
    brand: str
    description: str
    specifications: dict
    price: Decimal
    discount_percent: Decimal
    tax_rate: Decimal | None
    stock_quantity: int
    is_active: bool
    is_featured: bool


class InventoryUpdate(BaseModel):
    stock_quantity: int = Field(ge=0)


class ProductImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    url: str
    alt_text: str | None
    sort_order: int
    is_primary: bool


class ProductCard(BaseModel):
    id: int
    name: str
    slug: str
    brand: str
    image_url: str | None
    list_price: Decimal
    selling_price: Decimal
    discount_percent: Decimal
    in_stock: bool


class ProductList(BaseModel):
    items: list[ProductCard]
    page: int
    page_size: int
    total: int


class ReviewCard(BaseModel):
    id: int
    rating: int
    title: str | None
    body: str
    author_name: str


class ProductDetail(ProductCard):
    sku: str
    description: str
    specifications: dict
    tax_rate: Decimal | None
    stock_quantity: int
    gallery: list[ProductImageRead]
    reviews: list[ReviewCard]
    review_page: int
    review_total: int


ProductSort = Literal["newest", "price_asc", "price_desc", "name", "popular"]
