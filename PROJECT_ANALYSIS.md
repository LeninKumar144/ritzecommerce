# Project Analysis

## Repository status

Inspected workspace: `d:\projects\ritz_Ecommerce`.

| Check | Result |
| --- | --- |
| Source files | None |
| Configuration | None |
| Documentation | None before this phase |
| Git repository | Not initialized |
| Existing frameworks or dependencies | None |
| Reusable components | None |

At the start of Phase 1 the workspace was an empty project folder. There was no existing application to preserve, migrate, or extend.

Phase 2 added `backend/` only: FastAPI, configuration, a synchronous SQLAlchemy engine, Alembic, and health checks. Models, catalog APIs, the React app, and payments are still absent.

## Placement

The application will live at the repository root:

- `frontend/` — React storefront and admin UI
- `backend/` — FastAPI application, Alembic migrations, and tests
- `database/` — notes that accompany migrations; schema changes are applied only through Alembic
- `docs/` — supplementary guides added in later phases

Analysis documents stay at the repository root so they are visible without opening a subdirectory.

The prompt’s sample tree used a nested `product-shopping-app/` directory. That extra folder is not used, because this workspace is already the project root.

## Approved technology stack

| Area | Choice |
| --- | --- |
| Frontend | React, Vite, TypeScript |
| UI | Tailwind CSS |
| Routing and forms | React Router, React Hook Form, Zod |
| Server state | TanStack Query |
| HTTP client | Axios |
| Frontend tests | Vitest, React Testing Library |
| Backend | Python 3.12, FastAPI |
| Validation | Pydantic v2, pydantic-settings |
| ORM | SQLAlchemy 2.x |
| Database | MySQL 8.x, database name `product_shopping_db` |
| Driver | PyMySQL |
| Migrations | Alembic |
| Server | Uvicorn |
| Auth tokens | PyJWT |
| Password hashing | pwdlib with Argon2 |
| Payments | Official Razorpay Python SDK, test mode first |
| Backend tests | Pytest, HTTPX |

The following are excluded: Java, Spring Boot, Maven, JPA, Hibernate, and PostgreSQL.

## Runtime decisions

FastAPI routes and SQLAlchemy sessions are synchronous. PyMySQL and the Razorpay Python SDK are synchronous libraries. Asynchronous endpoints would not match those drivers.

Monetary amounts use `DECIMAL(12,2)` in INR. Razorpay amounts are converted to paise only when creating or verifying a gateway order. The frontend never supplies a price or total that the backend trusts.

Product images are stored as files under `backend/uploads/` during local development. MySQL stores the URL and metadata. Uploads are restricted to JPEG, PNG, and WebP, with a maximum file size enforced on the server.

Shop behavior that operators may change without a code release is loaded from environment variables: shop name, default GST rate, flat delivery fee, free-delivery threshold, and stock reservation window. The default shop name is **Ritz**.

## Authentication decision

Access tokens are JWTs stored in an `httpOnly`, `Secure`, `SameSite` cookie. The React app does not put access tokens in `localStorage`.

State-changing requests must send a CSRF token using the double-submit cookie pattern. A Vite development proxy makes the browser use one origin locally, so session cookies work without a cross-site setup.

Registration always creates a `CUSTOMER`. The `ADMIN` role is assigned only by a seed command that reads `ADMIN_EMAIL` and `ADMIN_PASSWORD` from the environment.

## Missing modules

Still to be built:

- Customer and admin HTTP APIs
- React storefront and admin dashboard
- Razorpay checkout, signature verification, and webhooks
- Invoice generation
- Frontend tests

Present after Phase 3:

- FastAPI app, configuration, logging, and CORS
- Synchronous SQLAlchemy engine and session dependency
- Alembic revision for the shopping schema, including seeded roles
- SQLAlchemy models, Pydantic schemas, repositories, and catalog and order services
- Health routes and schema constraint tests

## Risks

| Risk | Mitigation |
| --- | --- |
| Cookie session on two local origins (Vite and Uvicorn) | Vite proxy so the browser uses one origin in development |
| CSRF against cookie authentication | Double-submit CSRF token on unsafe methods |
| Overselling under concurrent checkout | Row locks and conditional stock updates inside a transaction |
| Abandoned Razorpay checkouts holding stock | Reservation expiry; release on failure, cancel, and expiry; release is idempotent |
| Duplicate webhook delivery | Unique Razorpay event id; processing is safe to repeat |
| Trusting the browser for payment success or totals | Server recalculates prices; payment is captured only after signature or webhook verification |
| Secret leakage | `.env` is gitignored; `.env.example` contains placeholders only; secrets are never logged |
| Destructive tests against a shared database | Tests use a separate database or fixtures, never production data |
| Product edits changing historical invoices | Order items store name, SKU, price, discount, and tax at purchase time |
| Deleting a product that already appears on orders | Products referenced by orders are not hard-deleted |

## Phase 1 scope

This phase writes the analysis and design documents only. Application code, migrations, and payment integration start in later phases after approval.

## Related documents

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DATABASE.md](DATABASE.md)
- [API.md](API.md)
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- [SETUP.md](SETUP.md)
