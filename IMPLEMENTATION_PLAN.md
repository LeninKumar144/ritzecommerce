# Implementation Plan

Phase 1 is repository analysis and these design documents. It does not add application code.

Phases 2 through 13 start only after approval of the next phase. Each phase is done only when its verification steps have actually been run.

The approved stack stays fixed: React, Vite, TypeScript, Tailwind CSS, Python, FastAPI, Pydantic, SQLAlchemy 2.x, MySQL 8.x, Alembic, and Razorpay. Do not replace any of those with Java, Spring Boot, PostgreSQL, JPA, or Hibernate.

## Phase 1 — Analysis and documentation

Status: completed by the documents in this repository.

Deliverables:

- [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DATABASE.md](DATABASE.md)
- [API.md](API.md)
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- [README.md](README.md)
- [SETUP.md](SETUP.md)
- `.gitignore`

Verification: the files exist and describe an empty workspace, the chosen stack, the schema, and the API. No server is started in this phase.

## Phase 2 — Backend foundation

Status: complete.

`backend/` contains a Python 3.13 virtual environment (3.12 is not installed on this machine; 3.13 is an approved version), `requirements.txt`, `pydantic-settings`, a synchronous SQLAlchemy engine, and Alembic configured for MySQL through PyMySQL. `backend/.env.example` has placeholders only. `.env` is not committed.

Verification that was run:

- `python -m pip install -r requirements.txt` succeeded
- `import app.main` succeeded
- `pytest` — 2 passed (`GET /health` and `GET /api/v1/health`)
- Uvicorn on `http://127.0.0.1:8000` served `/docs` (Swagger UI title Ritz) and `GET /health` returned 200 `{"status":"ok"}`, including from the Swagger Execute button
- `alembic upgrade head --sql` loaded the MySQL migration context. There are no revisions yet
- `alembic current` did not log in. `DB_USERNAME` and `DB_PASSWORD` are unset. An earlier attempt with an empty user reached MySQL 8 and received access denied, which confirms the server is running and the driver is wired up

Copy `backend/.env.example` to `backend/.env` and set the MySQL account before Phase 3 migrations.

## Phase 3 — Schema and application layers

Status: complete.

Models, Pydantic schemas, repositories, and services match [DATABASE.md](DATABASE.md). Revision `b0b1ced4a3fd` creates every table and seeds `CUSTOMER` and `ADMIN`.

Verification that was run:

- `alembic upgrade head` created 16 application tables in `product_shopping_db` and inserted both roles
- `alembic downgrade base` then `alembic upgrade head` succeeded
- `pytest` — 12 passed, including negative price rejection (`ck_products_price_non_negative`), duplicate SKU rejection, and role seed checks
- Constraint tests use `product_shopping_test`, not the development database

## Phase 4 — Authentication and roles

Status: complete.

Register, login, logout, refresh, and current user are under `/api/v1/auth`. Passwords are Argon2 hashes. Access and refresh tokens are httpOnly cookies, and unsafe methods require the `X-CSRF-Token` header. `python -m app.scripts.seed_admin` creates the administrator from `ADMIN_EMAIL` and `ADMIN_PASSWORD`.

Verification that was run:

- `pytest` — 18 passed, including registration, login, wrong password, inactive user, a customer calling `GET /api/v1/admin/health`, and logout
- Tests used `product_shopping_test`
- `alembic upgrade head` added `users.refresh_token_jti` on `product_shopping_db`

## Phase 5 — Categories and products

Status: complete.

Public catalog reads and admin category, product, image, and inventory routes are under `/api/v1`. Uploaded files live in `backend/uploads/` and are served from `/media`. Metadata stays in MySQL. Selling price is `price * (100 - discount_percent) / 100`, rounded half up to paise.

Verification that was run:

- `pytest` — 19 passed, including search, brand, price, stock, and featured filters, sort, inactive products hidden from anonymous shoppers and visible to an admin, duplicate SKU `409`, GIF upload `400`, PNG upload `201`, customer catalog write `403`, and category delete `409` while products exist
- `python -m app.scripts.seed_catalog` inserted Apparel and Home with three products and PNG images into `product_shopping_db`

## Phase 6 — Storefront UI

Status: complete.

The Vite app uses Tailwind, React Router, TanStack Query, React Hook Form, and Zod. Home, category, product listing, and product details read the live API. Add to cart and Buy now send an unsigned shopper to sign in. They do not write a cart.

Verification that was run:

- `npm test` — 5 passed (listing, search, sort, pagination, product details)
- `npm run build` succeeded
- Browser checks on a desktop width and a 390px mobile width: home, Apparel category, listing search for “linen”, brand and minimum-price filters, price sort, linen shirt details (SKU `RITZ-LINEN`, selling price ₹1,709.10), and Add to cart opening the sign-in page
- Pagination controls stay hidden while a page holds every product (3 products, page size 8). The Next control is covered by the Vitest case above

## Phase 7 — Cart and inventory

Implement cart APIs and the cart page. Totals come from the server.

Verification:

- Tests cover add, update, remove, clear, invalid quantity, and insufficient stock
- Two concurrent checkouts cannot oversell; that test can land in Phase 8 if checkout is the locking boundary, and this phase still tests stock rejection on add

## Phase 8 — Checkout, addresses, tax, and coupons

Implement addresses, coupon apply and remove, and checkout up to a `PENDING_PAYMENT` order with stock reservation. Do not mark the order paid in this phase.

Verification:

- Tests cover pricing, tax, delivery waiver, invalid coupons, address ownership, and stock reservation rollback
- The payable amount in the response matches a hand-calculated fixture

## Phase 9 — Razorpay

Create the Razorpay order on checkout, open Checkout in the frontend with the public key id, verify the payment signature, and process signed webhooks idempotently. Handle failure and cancellation by releasing stock once.

Verification:

- Signature tests use the documented Razorpay signing method and a test secret from the environment
- A second webhook with the same event id does not change stock twice
- The order stays unpaid when the signature is invalid
- No test uses a hard-coded payment-success shortcut

## Phase 10 — Orders and invoices

Implement customer order history, order detail, cancellation rules, and printable HTML invoices from snapshotted lines.

Verification:

- A customer receives 404 for another customer’s order
- An invoice still shows the original price after the product price changes
- Cancel releases stock only from `PENDING_PAYMENT`

## Phase 11 — Admin dashboard

Build the protected admin UI and the remaining admin list, status, coupon, review, and dashboard endpoints. Revenue uses captured payments only.

Verification:

- Dashboard numbers match fixture payments
- A customer session that opens an admin URL is turned away in the UI and receives 403 from the API
- Vitest covers the admin route guard

## Phase 12 — Test pass

Fill the remaining backend and frontend cases: failed payment, cancelled payment, duplicate callbacks, and unauthorized requests.

Verification:

- `pytest` and `npm test` are executed and the results are recorded
- Tests do not point at a production database

## Phase 13 — Security and deployment preparation

Review logging, CORS, cookie flags, upload limits, rate limits, and secret handling. Document production settings in [SETUP.md](SETUP.md).

Verification:

- `.env` is absent from the file list that would be committed
- Error responses for a forced exception omit stack traces
- Login rate limiting returns 429 in a test

## Working rules for every later phase

- Inspect existing files before editing them
- Implement one module at a time
- Run the phase tests and the relevant app or build
- Update the document that changed
- Leave later phases unstarted until the current phase is verified
