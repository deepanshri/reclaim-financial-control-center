# Reclaim AI — FastAPI Backend

Settlement auditor API for the Reclaim financial control center. Ledger data is a **synthetic demo dataset**, not a live Razorpay connection.

## Auth

Demo merchant:

- Merchant ID: `mid_demo_ZC771042`
- Password: `RECLAIM_DEMO_PASSWORD` (default `ReclaimDemo!2026`)

Protected APIs require `Authorization: Bearer <token>` or the `reclaim_session` cookie from `POST /api/auth/login`.

## Running the backend

```bash
backend\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Copy `.env.example` to `.env` and adjust secrets before any non-demo deployment.

- Health: `GET /api/health` (public)
- Docs: `http://localhost:8000/docs` (disabled when `RECLAIM_ENV=production`)

## Operational store

SQLite at `backend/data/operational.sqlite` stores:

- demo user + hashed password
- sessions
- recovery request overlay
- workspace settings
- support tickets
- audit run records

CSV files remain the source of truth for payments, fees, refunds, settlements, and bank credits.

## Tests

```bash
$env:PYTHONPATH="backend"
backend\.venv\Scripts\pytest backend\tests -v
```
