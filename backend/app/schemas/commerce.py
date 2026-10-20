"""Commerce schemas for coupons, carts, orders, payments, reviews, and wishlists."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DiscountType, OrderStatus, PaymentStatus


class CouponCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    discount_type: DiscountType
    discount_value: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    min_order_amount: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    max_discount_amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    usage_limit: int | None = Field(default=None, ge=1)
    is_active: bool = True


class CouponRead(CouponCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    used_count: int


class CartItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None
    product_name: str
    sku: str
    unit_price: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    quantity: int
    line_total: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    user_id: int
    status: OrderStatus
    currency: str
    subtotal: Decimal
    product_discount_total: Decimal
    coupon_code: str | None
    coupon_discount_total: Decimal
    tax_total: Decimal
    delivery_fee: Decimal
    grand_total: Decimal


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    razorpay_order_id: str
    razorpay_payment_id: str | None
    amount: Decimal
    currency: str
    status: PaymentStatus


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: str | None = Field(default=None, max_length=160)
    body: str = Field(min_length=1)


class ReviewRead(ReviewCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int


class WishlistCreate(BaseModel):
    product_id: int = Field(gt=0)
