# API

Base path: `/api/v1`.

Interactive documentation: `/docs` (Swagger UI) and `/openapi.json`.

Authentication uses an httpOnly access-token cookie. Unsafe methods (`POST`, `PUT`, `PATCH`, `DELETE`) also require the CSRF header `X-CSRF-Token`, whose value matches the readable CSRF cookie. `GET` requests do not require the CSRF header.

Public catalog routes do not require a session. Customer routes require a `CUSTOMER` or `ADMIN` session and operate on the authenticated user only. Admin routes require the `ADMIN` role.

Another customer’s order, address, cart, or review is returned as `404` so the API does not reveal that the resource exists.

## Status codes

| Code | When |
| --- | --- |
| 200 | Read or update succeeded |
| 201 | Resource created |
| 204 | Delete succeeded with no body |
| 400 | Business rule rejected the request |
| 401 | Missing or invalid session |
| 403 | Authenticated role is not allowed, or CSRF check failed |
| 404 | Resource is missing or not owned by the caller |
| 409 | Unique conflict or stock conflict |
| 422 | Body or query failed schema validation |
| 429 | Rate limit exceeded |
| 500 | Unexpected error, no stack trace in the body |

Error body:

```json
{
  "detail": "Human-readable message"
}
```

Validation errors use FastAPI’s standard 422 shape.

## Auth

| Method | Path | Auth | Success |
| --- | --- | --- | --- |
| POST | `/auth/register` | Public | 201 |
| POST | `/auth/login` | Public | 200 |
| POST | `/auth/logout` | Session | 204 |
| POST | `/auth/refresh` | Refresh cookie | 200 |
| GET | `/auth/me` | Session | 200 |

`POST /auth/register`

```json
{
  "email": "customer@example.com",
  "password": "at-least-8-chars",
  "full_name": "Asha Rao",
  "phone": "9876543210"
}
```

Creates a `CUSTOMER`. Duplicate email returns 409. Response sets auth cookies and returns the user profile. Passwords are never returned.

`POST /auth/login`

```json
{
  "email": "customer@example.com",
  "password": "at-least-8-chars"
}
```

Unknown user or wrong password returns 401 with the same message. Inactive users return 403. Login is rate limited.

`POST /auth/logout` clears access, refresh, and CSRF cookies.

Unsafe requests, including register, login, logout, and refresh, require a CSRF token. A response sets the readable `csrf_token` cookie when the request did not already include one. The client sends that value in the `X-CSRF-Token` header. A mismatch returns 403.

`GET /auth/me` returns `id`, `email`, `full_name`, `phone`, `role`, and `is_active`.

`GET /admin/health` returns 200 for an administrator, 403 for a customer, and 401 when there is no session. It is the authorization check for the admin API until the dashboard routes are added.

## Categories

| Method | Path | Auth | Success |
| --- | --- | --- | --- |
| GET | `/categories` | Public | 200 |
| GET | `/categories/{slug}` | Public | 200 |
| POST | `/admin/categories` | Admin | 201 |
| PATCH | `/admin/categories/{id}` | Admin | 200 |
| DELETE | `/admin/categories/{id}` | Admin | 204 |

Public list returns active categories only: `id`, `name`, `slug`, `description`, `image_url`.

Admin create and update accept `name`, `description`, `image_url` or a multipart image, and `is_active`. Duplicate name returns 409. Delete is rejected with 409 when products still reference the category.

## Products

| Method | Path | Auth | Success |
| --- | --- | --- | --- |
| GET | `/products` | Public | 200 |
| GET | `/products/brands` | Public | 200 |
| GET | `/products/{slug}` | Public | 200 |
| POST | `/admin/products` | Admin | 201 |
| PATCH | `/admin/products/{id}` | Admin | 200 |
| DELETE | `/admin/products/{id}` | Admin | 204 |
| POST | `/admin/products/{id}/images` | Admin | 201 |
| DELETE | `/admin/products/{id}/images/{image_id}` | Admin | 204 |
| PATCH | `/admin/products/{id}/inventory` | Admin | 200 |

`GET /products` query parameters:

| Parameter | Meaning |
| --- | --- |
| `search` | Name, brand, or SKU |
| `category` | Category slug |
| `brand` | Exact brand |
| `min_price`, `max_price` | Selling price bounds |
| `in_stock` | `true` or `false` |
| `sort` | `newest`, `price_asc`, `price_desc`, `name`, `popular` |
| `featured` | `true` limits the list to featured products |
| `page` | Default 1 |
| `page_size` | Default 20, maximum 100 |

Customers receive active products only. Each item includes primary image, name, selling price, list price, discount percent, stock availability, and slug. The response includes `items`, `page`, `page_size`, and `total`.

`GET /products/{slug}` adds description, specifications, SKU, gallery, tax rate, and a page of reviews. Inactive products return 404 to customers and 200 to admins.

Admin product body:

```json
{
  "name": "Cotton shirt",
  "sku": "SHIRT-001",
  "category_id": 1,
  "brand": "Ritz",
  "description": "Woven cotton shirt",
  "specifications": {"material": "cotton"},
  "price": "1499.00",
  "discount_percent": "10.00",
  "tax_rate": "18.00",
  "stock_quantity": 25,
  "is_active": true,
  "is_featured": false
}
```

`price` must be `>= 0`. `discount_percent` must be from 0 to 100. `stock_quantity` must be `>= 0`. Duplicate SKU returns 409.

Image upload is `multipart/form-data` with `file` and optional `alt_text` and `is_primary`. Allowed types are JPEG, PNG, and WebP. Oversize or other types return 400.

`DELETE /admin/products/{id}` deactivates the product when order items reference it, and returns 200 with the updated product. It removes the row only when nothing references it, and then returns 204.

`PATCH /admin/products/{id}/inventory` sets `stock_quantity` and rejects negative values.

## Addresses

All routes require a session and touch only the caller’s rows.

| Method | Path | Success |
| --- | --- | --- |
| GET | `/addresses` | 200 |
| POST | `/addresses` | 201 |
| PATCH | `/addresses/{id}` | 200 |
| DELETE | `/addresses/{id}` | 204 |

Body fields: `full_name`, `phone`, `line1`, `line2`, `city`, `state`, `postal_code`, `country`, `is_default`. Setting `is_default` clears the previous default for that user.

## Cart

All cart routes require a session. Prices in the response are computed on the server from current product rows.

| Method | Path | Success |
| --- | --- | --- |
| GET | `/cart` | 200 |
| POST | `/cart/items` | 200 |
| PATCH | `/cart/items/{item_id}` | 200 |
| DELETE | `/cart/items/{item_id}` | 200 |
| DELETE | `/cart` | 204 |
| POST | `/cart/coupon` | 200 |
| DELETE | `/cart/coupon` | 200 |

`POST /cart/items`

```json
{
  "product_id": 10,
  "quantity": 1
}
```

Quantity must be an integer `>= 1`. Inactive products and quantities above available stock return 409. Adding an existing product increases quantity.

Cart response:

```json
{
  "items": [
    {
      "id": 1,
      "product_id": 10,
      "name": "Cotton shirt",
      "image_url": "/media/products/10/shirt.jpg",
      "quantity": 1,
      "unit_list_price": "1499.00",
      "unit_selling_price": "1349.10",
      "line_subtotal": "1349.10"
    }
  ],
  "subtotal": "1349.10",
  "coupon_code": null,
  "coupon_discount": "0.00",
  "tax_total": "242.84",
  "delivery_fee": "49.00",
  "grand_total": "1640.94"
}
```

`POST /cart/coupon` accepts `{ "code": "SAVE10" }`. Ineligible coupons return 400 and leave the cart unchanged.

## Wishlist and reviews

Session required.

| Method | Path | Success |
| --- | --- | --- |
| GET | `/wishlist` | 200 |
| POST | `/wishlist` | 201 |
| DELETE | `/wishlist/{product_id}` | 204 |
| GET | `/products/{slug}/reviews` | 200, public |
| POST | `/products/{slug}/reviews` | 201 |
| DELETE | `/admin/reviews/{id}` | 204 |

Wishlist create body: `{ "product_id": 10 }`. A duplicate returns 409.

Review body: `{ "rating": 5, "title": "Excellent", "body": "Fits well." }`. Rating must be 1 through 5. A second review by the same user on the same product returns 409.

## Checkout and payments

| Method | Path | Auth | Success |
| --- | --- | --- | --- |
| POST | `/checkout` | Session | 201 |
| POST | `/payments/verify` | Session | 200 |
| POST | `/payments/webhook` | Razorpay signature | 200 |
| POST | `/payments/{payment_id}/cancel` | Session, owner | 200 |
| POST | `/admin/payments/{payment_id}/refund` | Admin | 201 |

`POST /checkout`

```json
{
  "address_id": 3,
  "contact_phone": "9876543210"
}
```

The server loads the caller’s cart and address, rejects an empty cart, rechecks product status and stock, recalculates every amount, creates an order in `PENDING_PAYMENT`, reserves stock, and creates a Razorpay order for `grand_total` in paise.

Response:

```json
{
  "order_id": 50,
  "order_number": "RITZ-20261003-0050",
  "amount": "1640.94",
  "currency": "INR",
  "razorpay_key_id": "rzp_test_placeholder",
  "razorpay_order_id": "order_test_123"
}
```

The response never includes the Razorpay key secret.

`POST /payments/verify`

```json
{
  "razorpay_order_id": "order_test_123",
  "razorpay_payment_id": "pay_test_123",
  "razorpay_signature": "signature"
}
```

The backend verifies the signature. A valid captured payment confirms the order. An invalid signature returns 400 and does not confirm the order. Repeating a successful verification returns the confirmed order and does not change stock again.

`POST /payments/webhook` reads the raw body, verifies `X-Razorpay-Signature` with the webhook secret, and stores `razorpay_event_id`. A duplicate event returns 200 without a second state change. Failed and cancelled payment events release reserved stock once.

`POST /payments/{payment_id}/cancel` releases stock when the order is still `PENDING_PAYMENT`.

`POST /admin/payments/{payment_id}/refund`

```json
{
  "amount": "1640.94",
  "reason": "Customer return",
  "restock": true
}
```

Amount cannot exceed the captured amount minus prior refunds. The refund is created through the Razorpay API. `restock: true` returns item quantities once for a full refund.

## Orders and invoices

| Method | Path | Auth | Success |
| --- | --- | --- | --- |
| GET | `/orders` | Session | 200 |
| GET | `/orders/{id}` | Owner | 200 |
| GET | `/orders/{id}/invoice` | Owner | 200 |
| POST | `/orders/{id}/cancel` | Owner | 200 |
| GET | `/admin/orders` | Admin | 200 |
| GET | `/admin/orders/{id}` | Admin | 200 |
| PATCH | `/admin/orders/{id}/status` | Admin | 200 |

Customer list is paginated and limited to the caller. Order detail includes items with snapshotted names and prices, delivery snapshot, totals, and payment status.

`GET /orders/{id}/invoice` returns `text/html` suitable for print, and `?format=pdf` is reserved for a later phase if a PDF renderer is added. The first implementation returns printable HTML. The invoice includes shop details, invoice number, order id and date, customer details, line items, discounts, tax, delivery, total, and payment reference and status.

`POST /orders/{id}/cancel` is allowed for the owner while the order is `PENDING_PAYMENT` or `CONFIRMED` and has not shipped. Pending orders release stock. Confirmed orders require a refund flow rather than a silent stock return.

Admin status updates must follow the transitions in [DATABASE.md](DATABASE.md). Illegal transitions return 409.

## Admin dashboard and remaining admin routes

| Method | Path | Auth | Success |
| --- | --- | --- | --- |
| GET | `/admin/dashboard` | Admin | 200 |
| GET | `/admin/customers` | Admin | 200 |
| PATCH | `/admin/customers/{id}` | Admin | 200 |
| GET | `/admin/payments` | Admin | 200 |
| GET | `/admin/coupons` | Admin | 200 |
| POST | `/admin/coupons` | Admin | 201 |
| PATCH | `/admin/coupons/{id}` | Admin | 200 |
| DELETE | `/admin/coupons/{id}` | Admin | 204 |

`GET /admin/dashboard` returns:

- `total_products`
- `total_categories`
- `total_customers`
- `total_orders`
- `total_sales` and `total_revenue` from captured payments only
- `pending_orders`
- `completed_orders` (`DELIVERED`)
- `recent_orders`

Admin lists support `search`, `page`, and `page_size`. Customer update can set `is_active` and cannot change a password to a chosen plaintext value without a dedicated reset flow. Coupon delete is rejected with 409 when orders already snapshot that code; the client should deactivate the coupon instead.

## Authorization summary

| Caller | Allowed |
| --- | --- |
| Anonymous | Register, login, active categories, active products, public reviews |
| Customer | Own profile, addresses, cart, wishlist, reviews, checkout, own orders and invoices |
| Admin | Everything a customer can do on their own records, plus `/admin/*` |

Customers who call `/admin/*` receive 403.

## Related documents

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DATABASE.md](DATABASE.md)
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
