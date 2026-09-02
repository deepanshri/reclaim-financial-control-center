# Reclaim — Financial Control Center

Settlement auditor for Indian Razorpay merchants. This repository ships a **synthetic demo dataset** (Zenzo Commerce / `mid_demo_ZC771042`), not a live payment gateway.

## Stack

- Frontend: Vite + React 19 + Tailwind CSS 4
- Backend: FastAPI
- Ledger: CSV datasets under `backend/data/reclaim_six_half_year_datasets/`
- Operational store: SQLite (`backend/data/operational.sqlite`) for sessions, recovery overlay, settings, tickets, and audit runs

## Demo login

- Merchant ID: `mid_demo_ZC771042`
- Password: `ReclaimDemo!2026` (override with `RECLAIM_DEMO_PASSWORD`)

## Run locally

1. Copy `.env.example` to `.env`.
2. Start the API:

```bash
backend\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

3. Start the UI:

```bash
npm install
npm run dev
```

The Vite dev server (and `npm run preview`) proxy `/api` to `http://127.0.0.1:8000`. Leave `VITE_API_BASE_URL` empty so the session cookie stays same-origin.

## Checks

```bash
npm run lint
npm run build
$env:PYTHONPATH="backend"
backend\.venv\Scripts\pytest backend\tests -q
```

See `backend/README.md` for API auth, docs, and the operational store.
