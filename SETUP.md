# Setup

`backend/` and `frontend/` are both in the repository.

Local services:

- MySQL 8.x on `localhost:3306`. On this machine the Windows service `MySQL80` is running.
- Database name `product_shopping_db`
- Python 3.12 or 3.13. This machine has Python 3.13.11, and the virtual environment was created with that interpreter.
- Node.js with npm, for the frontend in Phase 6

## Environment variables

Create `backend/.env` from `backend/.env.example`. Do not commit `.env`. Alembic online commands stop with a clear error until `DB_USERNAME` and `DB_PASSWORD` are set. The API process itself starts without those values because it does not connect to MySQL until a route asks for a session.

```text
APP_ENV=development

DB_HOST=localhost
DB_PORT=3306
DB_NAME=product_shopping_db
DB_USERNAME=
DB_PASSWORD=

JWT_SECRET=
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=

FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000

SHOP_NAME=Ritz
DEFAULT_TAX_RATE=18.00
DELIVERY_FEE=49.00
FREE_DELIVERY_THRESHOLD=999.00
STOCK_RESERVATION_MINUTES=15

ADMIN_EMAIL=
ADMIN_PASSWORD=
```

`ADMIN_EMAIL` and `ADMIN_PASSWORD` are used only by the admin seed command. Leave them empty until you are ready to create the first administrator.

Razorpay values are test-mode keys. The key secret and webhook secret stay on the server.

## MySQL

Create the database once, then let Alembic create tables:

```sql
CREATE DATABASE product_shopping_db CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
```

Use a dedicated MySQL user for the application. A second database, such as `product_shopping_test`, is required for Pytest so tests never run against production data.

## Backend

From the repository root in PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Then open `http://localhost:8000/docs`.

Create the first administrator after `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set in `backend/.env`:

```powershell
python -m app.scripts.seed_admin
```

The command refuses to run when either value is empty. It does not print the password.

If activation is blocked by execution policy, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that PowerShell window and activate again.

Confirm Python before creating the virtual environment:

```powershell
python --version
```

Use Python 3.12 or 3.13. This machine uses Python 3.13.11.

## Frontend

The storefront is in `frontend/`. Start the API first, from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then, from `frontend/`:

```powershell
npm install
npm run dev
```

The Vite dev server proxies `/api` and `/media` to `http://127.0.0.1:8000` so session cookies stay on one origin. Open `http://127.0.0.1:5173`.

Seed the sample catalog from `backend/` when the shop should not be empty:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_catalog
```

## Tests

Backend, from `backend/` with the virtual environment active. `pytest` creates and migrates `product_shopping_test`. Alembic commands use `product_shopping_db` from `backend/.env`.

```powershell
pytest
```

Frontend, from `frontend/`:

```powershell
npm test
```

Record the command output in the phase summary. Do not claim a suite passed unless it was executed.

## Production notes

Production uses the same variables with `APP_ENV=production`, a long random `JWT_SECRET`, live Razorpay keys only when the integration is ready, `Secure` cookies, and CORS limited to the real `FRONTEND_URL`. Schema changes ship as new Alembic revisions. Uploaded images need a durable directory or an object store; local `backend/uploads/` is for development.
