"""SQLAlchemy models for the shopping schema."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, CHAR, DATETIME, TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, created_at, mysql_args, primary_key, updated_at
from app.models.enums import DiscountType, OrderStatus, PaymentStatus

_unsigned_id = BIGINT(unsigned=True)


def _enum(enum_cls: type, name: str) -> Enum:
    return Enum(
        enum_cls,
        name=name,
        native_enum=True,
        values_callable=lambda obj: [item.value for item in obj],
    )


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = mysql_args()

    id: Mapped[int] = primary_key()
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    created_at: Mapped[datetime] = created_at()

    users: Mapped[list[User]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"
    __table_args__ = mysql_args()

    id: Mapped[int] = primary_key()
    role_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    refresh_token_jti: Mapped[str | None] = mapped_column(String(64))
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    role: Mapped[Role] = relationship(back_populates="users")
    addresses: Mapped[list[Address]] = relationship(back_populates="user")
    cart: Mapped[Cart | None] = relationship(back_populates="user")
    orders: Mapped[list[Order]] = relationship(back_populates="user")
    reviews: Mapped[list[Review]] = relationship(back_populates="user")
    wishlist_items: Mapped[list[WishlistItem]] = relationship(back_populates="user")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = mysql_args()

    id: Mapped[int] = primary_key()
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    products: Mapped[list[Product]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = mysql_args(
        CheckConstraint("price >= 0", name="price_non_negative"),
        CheckConstraint(
            "discount_percent >= 0 AND discount_percent <= 100",
            name="discount_percent_range",
        ),
        CheckConstraint("stock_quantity >= 0", name="stock_non_negative"),
        CheckConstraint(
            "tax_rate IS NULL OR (tax_rate >= 0 AND tax_rate <= 100)",
            name="tax_rate_range",
        ),
        Index("ix_products_brand", "brand"),
        Index("ix_products_price", "price"),
        Index("ix_products_is_active", "is_active"),
        Index("ix_products_created_at", "created_at"),
        Index("ix_products_active_category_price", "is_active", "category_id", "price"),
    )

    id: Mapped[int] = primary_key()
    category_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    brand: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    specifications: Mapped[dict] = mapped_column(JSON, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    stock_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    category: Mapped[Category] = relationship(back_populates="products")
    images: Mapped[list[ProductImage]] = relationship(back_populates="product")
    cart_items: Mapped[list[CartItem]] = relationship(back_populates="product")
    order_items: Mapped[list[OrderItem]] = relationship(back_populates="product")
    reviews: Mapped[list[Review]] = relationship(back_populates="product")
    wishlist_items: Mapped[list[WishlistItem]] = relationship(back_populates="product")


class ProductImage(Base):
    __tablename__ = "product_images"
    __table_args__ = mysql_args(Index("ix_product_images_product_id_sort_order", "product_id", "sort_order"))

    id: Mapped[int] = primary_key()
    product_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = created_at()

    product: Mapped[Product] = relationship(back_populates="images")


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = mysql_args()

    id: Mapped[int] = primary_key()
    user_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    line1: Mapped[str] = mapped_column(String(200), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(12), nullable=False)
    country: Mapped[str] = mapped_column(
        String(80), nullable=False, default="India", server_default=text("'India'")
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    user: Mapped[User] = relationship(back_populates="addresses")


class Coupon(Base):
    __tablename__ = "coupons"
    __table_args__ = mysql_args(
        CheckConstraint("discount_value >= 0", name="discount_value_non_negative"),
        CheckConstraint("min_order_amount >= 0", name="min_order_non_negative"),
        CheckConstraint("used_count >= 0", name="used_count_non_negative"),
    )

    id: Mapped[int] = primary_key()
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    discount_type: Mapped[DiscountType] = mapped_column(_enum(DiscountType, "discount_type"), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    min_order_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    max_discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    starts_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6))
    expires_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6))
    usage_limit: Mapped[int | None] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    carts: Mapped[list[Cart]] = relationship(back_populates="coupon")


class Cart(Base):
    __tablename__ = "carts"
    __table_args__ = mysql_args()

    id: Mapped[int] = primary_key()
    user_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    coupon_id: Mapped[int | None] = mapped_column(
        _unsigned_id,
        ForeignKey("coupons.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    user: Mapped[User] = relationship(back_populates="cart")
    coupon: Mapped[Coupon | None] = relationship(back_populates="carts")
    items: Mapped[list[CartItem]] = relationship(back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = mysql_args(
        UniqueConstraint("cart_id", "product_id", name="uq_cart_items_cart_product"),
        CheckConstraint("quantity >= 1", name="quantity_at_least_one"),
    )

    id: Mapped[int] = primary_key()
    cart_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    cart: Mapped[Cart] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="cart_items")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = mysql_args(
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
        Index("ix_orders_reservation_expires_at", "reservation_expires_at"),
    )

    id: Mapped[int] = primary_key()
    order_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[OrderStatus] = mapped_column(_enum(OrderStatus, "order_status"), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default=text("'INR'"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    product_discount_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    coupon_code: Mapped[str | None] = mapped_column(String(40))
    coupon_discount_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    tax_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    grand_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    ship_line1: Mapped[str] = mapped_column(String(200), nullable=False)
    ship_line2: Mapped[str | None] = mapped_column(String(200))
    ship_city: Mapped[str] = mapped_column(String(80), nullable=False)
    ship_state: Mapped[str] = mapped_column(String(80), nullable=False)
    ship_postal_code: Mapped[str] = mapped_column(String(12), nullable=False)
    ship_country: Mapped[str] = mapped_column(String(80), nullable=False)
    stock_reserved_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6))
    reservation_expires_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6))
    stock_released_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6))
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    user: Mapped[User] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(back_populates="order")
    payments: Mapped[list[Payment]] = relationship(back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = mysql_args()

    id: Mapped[int] = primary_key()
    order_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int | None] = mapped_column(
        _unsigned_id,
        ForeignKey("products.id", ondelete="SET NULL"),
    )
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product | None] = relationship(back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = mysql_args(Index("ix_payments_status", "status"))

    id: Mapped[int] = primary_key()
    order_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    razorpay_order_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default=text("'INR'"))
    status: Mapped[PaymentStatus] = mapped_column(_enum(PaymentStatus, "payment_status"), nullable=False)
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    order: Mapped[Order] = relationship(back_populates="payments")
    events: Mapped[list[PaymentEvent]] = relationship(back_populates="payment")
    refunds: Mapped[list[Refund]] = relationship(back_populates="payment")


class PaymentEvent(Base):
    __tablename__ = "payment_events"
    __table_args__ = mysql_args()

    id: Mapped[int] = primary_key()
    payment_id: Mapped[int | None] = mapped_column(
        _unsigned_id,
        ForeignKey("payments.id", ondelete="SET NULL"),
    )
    razorpay_event_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    payment: Mapped[Payment | None] = relationship(back_populates="events")


class Refund(Base):
    __tablename__ = "refunds"
    __table_args__ = mysql_args()

    id: Mapped[int] = primary_key()
    payment_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("payments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    razorpay_refund_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    payment: Mapped[Payment] = relationship(back_populates="refunds")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = mysql_args(
        UniqueConstraint("user_id", "product_id", name="uq_reviews_user_product"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="rating_range"),
    )

    id: Mapped[int] = primary_key()
    user_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(TINYINT, nullable=False)
    title: Mapped[str | None] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    user: Mapped[User] = relationship(back_populates="reviews")
    product: Mapped[Product] = relationship(back_populates="reviews")


class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    __table_args__ = mysql_args(
        UniqueConstraint("user_id", "product_id", name="uq_wishlist_items_user_product"),
    )

    id: Mapped[int] = primary_key()
    user_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        _unsigned_id,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = created_at()

    user: Mapped[User] = relationship(back_populates="wishlist_items")
    product: Mapped[Product] = relationship(back_populates="wishlist_items")
