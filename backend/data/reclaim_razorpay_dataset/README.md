# Reclaim Razorpay Demo Dataset

Synthetic deterministic demo data; not real merchant/customer data. It is structured to resemble public Razorpay payment, refund, settlement, and settlement-reconciliation entities.

Period: 2024-01-01 through 2026-08-31. UI year selector: 2026, 2025, 2024.

Public Razorpay documentation supports payment fields such as id, amount in smallest currency unit, currency, status, method, order_id, refund_status, amount_refunded, captured, fee, tax and created_at. Refunds include id, amount, payment_id, status, created_at and acquirer reference information. Settlements include id, amount, status, fees, tax, UTR and created_at. Settlement recon records include entity_id, type, debit, credit, amount, fee, tax, settled, settlement_id, payment_id, settlement_utr and related payment metadata.

## Files
merchant.json
payments.csv
refunds.csv
settlements.csv
settlement_recon.csv
bank_credits.csv
fee_contracts.csv
anomalies.csv
anomaly_evidence.csv
recovery_requests.csv
monthly_summary.csv
validate_dataset.py

## Hero anomaly
Unexpected Fee Rate Increase
Contracted rate: 1.80%
Applied rate: 2.30%
Affected payments: 1,248
Affected gross: ₹2,490,000
Impact: ₹12,450
Math: ₹2,490,000 × 0.50% = ₹12,450.
Cause: promotional fee waiver ended 2026-04-30; standard rate applied from 2026-05-05.

## Confirmed refund anomaly
Duplicate Refund
Original refund: ₹4,200
Second refund: ₹4,200
Excess debit: ₹4,200

## Recovery semantics
Potential loss, amount requested, and amount recovered are separate concepts. The two demo requests are marked resolved and have recovered amounts of ₹12,450 and ₹4,200, so total recovered is ₹16,650.

## Implementation principle
Use the dataset as source of truth. Financial values should flow: source data → calculation → UI. Use integer paise for monetary calculation in the backend where possible. Razorpay-like source amount fields in CSVs are integer currency subunits; analytical/custom fields may use human-readable INR.
