# Ritz

Ritz is a product shopping and billing application. Customers browse categories, view products, cart items, and pay online. Administrators manage the catalog, inventory, customers, orders, and payments.

Phases 1–6 are in place: design documents, the FastAPI application, the MySQL schema, JWT cookie authentication, the catalog API, and the React storefront. Cart, checkout, and the admin UI come in later phases.

## Stack

- Frontend: React, Vite, TypeScript, Tailwind CSS
- Backend: Python 3.12, FastAPI, Pydantic, SQLAlchemy 2.x
- Database: MySQL 8.x (`product_shopping_db`), Alembic, PyMySQL
- Auth: JWT in httpOnly cookies, Argon2 password hashes, `CUSTOMER` and `ADMIN` roles
- Payments: Razorpay test mode, with server-side signature and webhook verification

## Documents

- [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md) — current repository and risks
- [ARCHITECTURE.md](ARCHITECTURE.md) — layers, auth, pricing, stock, and payments
- [DATABASE.md](DATABASE.md) — tables, constraints, and reservation rules
- [API.md](API.md) — `/api/v1` contracts
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — phases 2 through 13
- [SETUP.md](SETUP.md) — Windows setup commands for later phases

## Status

| Phase | State |
| --- | --- |
| 1. Analysis and documentation | Done |
| 2. FastAPI, MySQL, Alembic | Done |
| 3. Schema, models, schemas, repositories, services | Done. `alembic upgrade head` created the tables and seeded `CUSTOMER` and `ADMIN`. Downgrade and a second upgrade succeeded. |
| 4. Authentication and roles | Done. Cookie sessions, CSRF checks, and the admin seed command are in place. |
| 5. Catalog, images, and inventory | Done. Public reads, admin writes, and image files under `backend/uploads/`. |
| 6. Storefront | Done. Home, category, listing, and product details talk to the live API. |
| 7–13. Cart through security review | Not started |

The local interpreter is Python 3.13.11. Python 3.12 is also supported. MySQL 8 is installed as the `MySQL80` service.
