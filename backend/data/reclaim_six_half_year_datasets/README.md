# Reclaim — Six Half-Year Synthetic Datasets

These six datasets are synthetic and deterministic. They are not real Razorpay merchant/customer data.

## Periods
- 2024 H1 — Jan 1 to Jun 30
- 2024 H2 — Jul 1 to Dec 31
- 2025 H1 — Jan 1 to Jun 30
- 2025 H2 — Jul 1 to Dec 31
- 2026 H1 — Jan 1 to Jun 30
- 2026 H2 — Jul 1 to Dec 31

Three periods were selected deterministically using seed 20260831 as **action_required** periods. The other three are **healthy** periods.

The selection is recorded in `selection.json`.

## Important
The backend must read the `dataset_meta.json` and source data for each half-year. Do not hardcode which periods are healthy/action-required in the React UI.

Healthy periods have no confirmed anomalies.
Action-required periods contain real source-data relationships supporting confirmed findings.

Every period is self-contained.

Each folder contains:
- dataset_meta.json
- payments.csv
- refunds.csv
- settlements.csv
- bank_credits.csv
- settlement_recon.csv
- fee_contracts.csv
- anomalies.csv
- anomaly_evidence.csv
- recovery_requests.csv
- summary.csv

## Intended UX
Selecting a half-year should ALWAYS show its statement/results.

Healthy:
“Healthy — no confirmed issues found.”

Action required:
“Action required — confirmed issue(s) found.”

Do not ask the user whether they want to view a healthy statement.

## Backend principle
Source data → calculation → finding → evidence → UI.

Do not trust old frontend mock data.
Do not invent anomalies just to fill the UI.
Do not expose technical reconciliation settings to normal merchants.
