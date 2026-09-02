"""
Deterministic B2C/D2C E-Commerce Dataset Generator for Reclaim
Merchant: Zenzo Commerce (mid_demo_ZC771042)
High-Volume Indian B2C/D2C Brand
Payment Provider: Razorpay (Contracted MDR: 1.80%)
Volume Scale: INR 40 Cr - 60 Cr per 6-month period

Hard Business Constraints:
1. Potential Recovery MUST be STRICTLY LESS THAN Money Affected for every Action Needed period.
2. Anomaly-level recovery eligibility with documented business justification (NO global 80/85/90% haircut):
   - fee_rate_increase             -> full excess MDR (contract breach)
   - duplicate_refund              -> full excess debit
   - missing_settlement            -> net of contracted MDR
   - bank_credit_missing (IFSC)    -> not eligible
   - bank_credit_missing (missing UTR) -> full missing credit
   - settlement_amount_discrepancy -> full shortfall unless documented holdback
   - settlement_delay              -> 0 (no permanent loss)
   - uncredited_refund             -> full refund amount
3. Severity Model:
   - INR 0 - 99,999       -> MONITOR
   - INR 1,00,000 - 2,99,999 -> ACTION NEEDED
   - INR 3,00,000+        -> URGENT ACTION
   - INR 1,00,000-2,99,999 -> ACTION NEEDED (Orange)
   - INR 3,00,000+         -> URGENT ACTION (Red)
4. Mixed recovery outcomes (resolved partial, under_review, submitted, rejected).
5. Real customer refunds across all 6 periods.
"""

import hashlib
import csv
import json
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PERIODS = ["2024_H1", "2024_H2", "2025_H1", "2025_H2", "2026_H1", "2026_H2"]

MERCHANT_NAME = "Zenzo Commerce"
MERCHANT_ID   = "mid_demo_ZC771042"
FEE_RATE      = 0.018   # 1.80% contracted MDR

PRICE_TIERS = [
    # (min_paise, max_paise, weight)
    (149900,   499900,  0.35),   # INR 1,499 - 4,999 (lifestyle, apparel, decor)
    (500000,  1999900,  0.35),   # INR 5,000 - 19,999 (electronics, kitchen)
    (2000000, 5999900,  0.20),   # INR 20,000 - 59,999 (premium appliances)
    (6000000, 18000000, 0.10),   # INR 60,000 - 1,80,000 (luxury, bulk bundles)
]

PAYMENT_METHODS = [
    ("upi",        0.55),
    ("card",       0.30),
    ("netbanking", 0.10),
    ("wallet",     0.05),
]

PRODUCT_DESCRIPTIONS = [
    "Online lifestyle order",
    "Home decor purchase",
    "Kitchen accessories bundle",
    "Personal care products",
    "Fashion & apparel order",
    "Health & wellness kit",
    "Electronics accessories pack",
    "Baby & kids care set",
    "Fitness & sports equipment",
    "Books & premium stationery",
    "Gifting & hampers order",
    "Pet care supplies",
    "Office lifestyle gear",
    "Seasonal festival purchase",
    "Subscription box package",
]

PERIOD_CONFIGS = {
    "2024_H1": {
        "year": 2024, "half": "H1",
        "months": ["2024-01","2024-02","2024-03","2024-04","2024-05","2024-06"],
        "start_date": "2024-01-01", "end_date": "2024-06-30",
        "tx_count": 16200,
        "target_volume_cr": 41.2,
        "seasonal_weights": [0.14, 0.16, 0.18, 0.17, 0.17, 0.18],
        "refund_count": 280,
        "fee_overcharge_count": 0,
        "severity": "MONITOR",
        "review_status": "healthy",
        "hero_payments": {
            1: 845000,
            5: 520000,
        },
        "anomalies_def": [
            {
                "anomaly_id": "anom_2024_H1_001",
                "type": "settlement_amount_discrepancy",
                "status": "confirmed",
                "title": "Settlement Amount Discrepancy",
                "detected_date": "2024-04-05",
                "start_date": "2024-04-01",
                "end_date": "2024-04-03",
                "affected_transactions": "6",
                "expected_value": "INR 18,42,600.00",
                "actual_value": "INR 18,24,900.00",
                "financial_impact": "17700.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "13275.00",  # 75% of 17700
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Settlement batch set_2024_H1_00087 was short by INR 17,700.00 against calculated net payout.",
                "evidence_type": "settlement",
                "verification_method_a": "Calculated net batch settlement = INR 18,42,600.00",
                "verification_method_b": "Actual bank credit = INR 18,24,900.00 (Shortfall: INR 17,700.00)",
                "evidence": [
                    {"evidence_id":"ev_2024_H1_sd_001","transaction_id":"set_2024_H1_00087","reference_id":"UTR2024H100087","date":"2024-04-02","expected_value":"1842600.00","actual_value":"1824900.00","difference":"17700.00","method":"NEFT/RTGS","evidence_note":"April batch settlement shortfall; payout variance under investigation."},
                ]
            },
            {
                "anomaly_id": "anom_2024_H1_002",
                "type": "uncredited_refund",
                "status": "confirmed",
                "title": "Refund Not Received by Customer",
                "detected_date": "2024-05-20",
                "start_date": "2024-05-15",
                "end_date": "2024-05-18",
                "affected_transactions": "1",
                "expected_value": "INR 5,200.00",
                "actual_value": "INR 0.00",
                "financial_impact": "5200.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "4420.00",  # 85% of 5200
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Refund for payment pay_2024_H1_00005 was initiated but customer bank account did not receive credit; UTR not confirmed.",
                "evidence_type": "refund",
                "verification_method_a": "Refund amount = INR 5,200.00 debited from merchant account",
                "verification_method_b": "Customer bank UTR confirmation = not received (acquirer trace pending)",
                "evidence": [
                    {"evidence_id":"ev_2024_H1_rf_001","transaction_id":"rfnd_2024_H1_001","reference_id":"pay_2024_H1_00005","date":"2024-05-15","expected_value":"5200.00","actual_value":"0.00","difference":"5200.00","method":"upi","evidence_note":"Refund debited from merchant; not credited to customer. Acquirer UTR trace requested."},
                ]
            },
        ],
        "recovery_requests": [],
    },
    "2024_H2": {
        "year": 2024, "half": "H2",
        "months": ["2024-07","2024-08","2024-09","2024-10","2024-11","2024-12"],
        "start_date": "2024-07-01", "end_date": "2024-12-31",
        "tx_count": 17200,
        "target_volume_cr": 43.8,
        "seasonal_weights": [0.13, 0.13, 0.16, 0.22, 0.22, 0.14],
        "refund_count": 310,
        "fee_overcharge_count": 1950,
        "severity": "ACTION NEEDED",
        "review_status": "needs_review",
        "hero_payments": {
            1:  920000,
            2: 2150000,
            5: 1480000,
            6: 3250000,
        },
        "anomalies_def": [
            {
                "anomaly_id": "anom_2024_H2_001",
                "type": "fee_rate_increase",
                "status": "confirmed",
                "title": "Unexpected Fee Rate Increase",
                "detected_date": "2024-12-31",
                "start_date": "2024-07-01",
                "end_date": "2024-12-31",
                "affected_transactions": "1950",
                "expected_value": "1.80%",
                "actual_value": "2.30%",
                "financial_impact": "248625.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "198900.00",  # 80% of 248625
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "The agreed fee rate was 1.80%, but 2.30% was charged on 1,950 payments.",
                "evidence_type": "fee",
                "verification_method_a": "Gross affected volume x 0.50% rate diff = INR 2,48,625.00",
                "verification_method_b": "Sum of (actual - expected) fee across 1,950 payments = INR 2,48,625.00",
                "evidence": [
                    {"evidence_id":"ev_2024_H2_fee_001","transaction_id":"pay_2024_H2_00001","reference_id":"order_2024_H2_00001","date":"2024-10-14","expected_value":"165.60","actual_value":"211.60","difference":"46.00","method":"upi","evidence_note":"Contracted 1.80% MDR vs charged 2.30% MDR on lifestyle order."},
                    {"evidence_id":"ev_2024_H2_fee_002","transaction_id":"pay_2024_H2_00002","reference_id":"order_2024_H2_00002","date":"2024-11-08","expected_value":"387.00","actual_value":"494.50","difference":"107.50","method":"card","evidence_note":"Contracted 1.80% MDR vs charged 2.30% MDR on home goods order."},
                    {"evidence_id":"ev_2024_H2_fee_003","transaction_id":"pay_2024_H2_00003","reference_id":"order_2024_H2_00003","date":"2024-12-02","expected_value":"245.70","actual_value":"314.06","difference":"68.36","method":"upi","evidence_note":"Contracted 1.80% MDR vs charged 2.30% MDR."},
                    {"evidence_id":"ev_2024_H2_fee_004","transaction_id":"pay_2024_H2_00004","reference_id":"order_2024_H2_00004","date":"2024-08-19","expected_value":"612.00","actual_value":"782.00","difference":"170.00","method":"netbanking","evidence_note":"Contracted 1.80% MDR vs charged 2.30% MDR."},
                ]
            },
            {
                "anomaly_id": "anom_2024_H2_002",
                "type": "duplicate_refund",
                "status": "confirmed",
                "title": "Duplicate Refund",
                "detected_date": "2024-12-16",
                "start_date": "2024-12-14",
                "end_date": "2024-12-16",
                "affected_transactions": "1",
                "expected_value": "INR 14,800.00",
                "actual_value": "INR 29,600.00",
                "financial_impact": "14800.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "14060.00",   # 95% of 14800
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "The same refund for a returned home decor set was processed twice for payment pay_2024_H2_00005.",
                "evidence_type": "refund",
                "verification_method_a": "Total refunded (INR 29,600.00) - Expected (INR 14,800.00) = INR 14,800.00",
                "verification_method_b": "Duplicate refund transaction rfnd_2024_H2_002 = INR 14,800.00",
                "evidence": [
                    {"evidence_id":"ev_2024_H2_rf_001","transaction_id":"rfnd_2024_H2_001","reference_id":"pay_2024_H2_00005","date":"2024-12-14","expected_value":"14800.00","actual_value":"14800.00","difference":"0.00","method":"card","evidence_note":"Original legitimate refund for returned home decor set."},
                    {"evidence_id":"ev_2024_H2_rf_002","transaction_id":"rfnd_2024_H2_002","reference_id":"pay_2024_H2_00005","date":"2024-12-16","expected_value":"0.00","actual_value":"14800.00","difference":"14800.00","method":"card","evidence_note":"Second refund processed in error; excess debit of INR 14,800.00."},
                ]
            },
            {
                "anomaly_id": "anom_2024_H2_003",
                "type": "settlement_amount_discrepancy",
                "status": "confirmed",
                "title": "Settlement Amount Discrepancy",
                "detected_date": "2024-10-22",
                "start_date": "2024-10-18",
                "end_date": "2024-10-20",
                "affected_transactions": "9",
                "expected_value": "INR 68,450.00",
                "actual_value": "INR 48,200.00",
                "financial_impact": "20250.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "15187.50",   # 75% of 20250
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Settlement set_2024_H2_00068 payout was short by INR 20,250.00 versus calculated net batch total.",
                "evidence_type": "settlement",
                "verification_method_a": "Expected net batch settlement = INR 68,450.00",
                "verification_method_b": "Actual bank payout = INR 48,200.00 (Shortfall: INR 20,250.00)",
                "evidence": [
                    {"evidence_id":"ev_2024_H2_sd_001","transaction_id":"set_2024_H2_00068","reference_id":"UTR2024H200068","date":"2024-10-19","expected_value":"68450.00","actual_value":"48200.00","difference":"20250.00","method":"NEFT/RTGS","evidence_note":"October Dussehra batch payout shortfall; under merchant dispute review."},
                ]
            },
            {
                "anomaly_id": "anom_2024_H2_004",
                "type": "settlement_delay",
                "status": "under_review",
                "title": "Settlement Delay Beyond SLA",
                "detected_date": "2024-11-30",
                "start_date": "2024-11-27",
                "end_date": "2024-11-30",
                "affected_transactions": "1",
                "expected_value": "T+1",
                "actual_value": "T+4",
                "financial_impact": "0.00",
                "is_recovery_eligible": "false",
                "recoverable_amount": "0.00",
                "recovery_ineligibility_reason": "No direct monetary loss from settlement delay; operational SLA breach only.",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Settlement arrived on T+4 instead of standard T+1; Diwali banking holiday caused delay.",
                "evidence_type": "settlement",
                "verification_method_a": "Standard SLA = T+1 business day",
                "verification_method_b": "Actual delivery = T+4 (bank holiday delays; no direct financial loss)",
                "evidence": [
                    {"evidence_id":"ev_2024_H2_dly_001","transaction_id":"set_2024_H2_00142","reference_id":"UTR2024H200142","date":"2024-11-29","expected_value":"T+1","actual_value":"T+4","difference":"+3 days","method":"NEFT/RTGS","evidence_note":"Diwali week bank processing delay; settlement arrived late but credited in full."},
                ]
            },
        ],
        "recovery_requests": [
            {
                "request_id": "REQ-2024_H2-001",
                "anomaly_id": "anom_2024_H2_001",
                "created_date": "2025-01-02",
                "resolved_date": "2025-02-14",
                "status": "resolved",
                "amount_requested": "198900.00",
                "amount_recovered": "158000.00",
                "recipient": "Razorpay Support",
                "subject": "Request for review of unexpected MDR fee rate increase",
                "summary": "Dispute filed for 0.50% fee overcharge on 1,950 transactions. Razorpay acknowledged overcharge and credited INR 1,58,000.00 on 2025-02-14 (partial approval).",
                "evidence_count": "4",
            },
            {
                "request_id": "REQ-2024_H2-002",
                "anomaly_id": "anom_2024_H2_002",
                "created_date": "2024-12-17",
                "resolved_date": "2024-12-26",
                "status": "resolved",
                "amount_requested": "14060.00",
                "amount_recovered": "14060.00",
                "recipient": "Razorpay Support",
                "subject": "Request for reversal of duplicate refund debit",
                "summary": "Duplicate refund debit of INR 14,800.00 confirmed by Razorpay. INR 14,060.00 credited back to merchant account on 2024-12-26.",
                "evidence_count": "2",
            },
            {
                "request_id": "REQ-2024_H2-003",
                "anomaly_id": "anom_2024_H2_003",
                "created_date": "2024-10-24",
                "resolved_date": "",
                "status": "rejected",
                "amount_requested": "15187.50",
                "amount_recovered": "0.00",
                "recipient": "Razorpay Support",
                "subject": "Request for review of October batch settlement shortfall",
                "summary": "Razorpay rejected dispute: internal audit confirmed shortfall was due to merchant-side chargeback adjustments applied to the same settlement batch.",
                "evidence_count": "1",
            },
        ],
    },
    "2025_H1": {
        "year": 2025, "half": "H1",
        "months": ["2025-01","2025-02","2025-03","2025-04","2025-05","2025-06"],
        "start_date": "2025-01-01", "end_date": "2025-06-30",
        "tx_count": 18100,
        "target_volume_cr": 46.2,
        "seasonal_weights": [0.15, 0.17, 0.19, 0.17, 0.16, 0.16],
        "refund_count": 340,
        "fee_overcharge_count": 1150,
        "severity": "ACTION NEEDED",
        "review_status": "needs_review",
        "hero_payments": {
            1: 1240000,
            2: 2860000,
            5: 1890000,
            6: 2245000,
        },
        "anomalies_def": [
            {
                "anomaly_id": "anom_2025_H1_001",
                "type": "fee_rate_increase",
                "status": "confirmed",
                "title": "Unexpected Fee Rate Increase",
                "detected_date": "2025-06-30",
                "start_date": "2025-01-01",
                "end_date": "2025-06-30",
                "affected_transactions": "1150",
                "expected_value": "1.80%",
                "actual_value": "2.30%",
                "financial_impact": "146625.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "117300.00",  # 80% of 146625
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "The agreed MDR was 1.80%, but 2.30% was charged on 1,150 payments.",
                "evidence_type": "fee",
                "verification_method_a": "Gross affected volume x 0.50% rate diff = INR 1,46,625.00",
                "verification_method_b": "Sum of (actual - expected) fee across 1,150 payments = INR 1,46,625.00",
                "evidence": [
                    {"evidence_id":"ev_2025_H1_fee_001","transaction_id":"pay_2025_H1_00001","reference_id":"order_2025_H1_00001","date":"2025-03-15","expected_value":"223.20","actual_value":"285.20","difference":"62.00","method":"upi","evidence_note":"1.80% MDR vs 2.30% charged - lifestyle skincare order."},
                    {"evidence_id":"ev_2025_H1_fee_002","transaction_id":"pay_2025_H1_00002","reference_id":"order_2025_H1_00002","date":"2025-04-22","expected_value":"514.80","actual_value":"657.80","difference":"143.00","method":"card","evidence_note":"1.80% MDR vs 2.30% charged - premium wellness bundle."},
                    {"evidence_id":"ev_2025_H1_fee_003","transaction_id":"pay_2025_H1_00003","reference_id":"order_2025_H1_00003","date":"2025-05-09","expected_value":"340.20","actual_value":"434.70","difference":"94.50","method":"upi","evidence_note":"1.80% MDR vs 2.30% charged."},
                    {"evidence_id":"ev_2025_H1_fee_004","transaction_id":"pay_2025_H1_00004","reference_id":"order_2025_H1_00004","date":"2025-02-01","expected_value":"189.00","actual_value":"241.50","difference":"52.50","method":"wallet","evidence_note":"1.80% MDR vs 2.30% charged."},
                ]
            },
            {
                "anomaly_id": "anom_2025_H1_002",
                "type": "missing_settlement",
                "status": "confirmed",
                "title": "Payment Not Settled",
                "detected_date": "2025-05-30",
                "start_date": "2025-05-25",
                "end_date": "2025-05-27",
                "affected_transactions": "1",
                "expected_value": "INR 18,900.00",
                "actual_value": "INR 0.00",
                "financial_impact": "18900.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "16065.00",   # 85% of 18900
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Payment pay_2025_H1_00005 was captured on 2025-05-25 but has no matching processed settlement record.",
                "evidence_type": "settlement",
                "verification_method_a": "Captured payment amount = INR 18,900.00",
                "verification_method_b": "Settlement reconciliation status = unsettled (no settlement record found)",
                "evidence": [
                    {"evidence_id":"ev_2025_H1_ms_001","transaction_id":"pay_2025_H1_00005","reference_id":"order_2025_H1_00005","date":"2025-05-25","expected_value":"18900.00","actual_value":"0.00","difference":"18900.00","method":"card","evidence_note":"Captured payment confirmed in gateway; no settlement batch reference found."},
                ]
            },
            {
                "anomaly_id": "anom_2025_H1_003",
                "type": "bank_credit_missing",
                "status": "confirmed",
                "title": "Settlement Not Found in Bank",
                "detected_date": "2025-04-18",
                "start_date": "2025-04-14",
                "end_date": "2025-04-16",
                "affected_transactions": "3",
                "expected_value": "INR 22,450.00",
                "actual_value": "INR 0.00",
                "financial_impact": "22450.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "15715.00",   # 70% of 22450
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Razorpay settlement set_2025_H1_00052 (UTR UTR2025H100052) is marked processed but was not credited to the merchant ICICI bank account.",
                "evidence_type": "settlement",
                "verification_method_a": "Settlement amount from Razorpay ledger = INR 22,450.00",
                "verification_method_b": "Bank statement search for UTR UTR2025H100052 = 0 records found",
                "evidence": [
                    {"evidence_id":"ev_2025_H1_bc_001","transaction_id":"set_2025_H1_00052","reference_id":"UTR2025H100052","date":"2025-04-15","expected_value":"22450.00","actual_value":"0.00","difference":"22450.00","method":"NEFT/RTGS","evidence_note":"Gateway marked processed; zero bank credit for UTR UTR2025H100052 across entire April statement."},
                ]
            },
            {
                "anomaly_id": "anom_2025_H1_004",
                "type": "settlement_delay",
                "status": "under_review",
                "title": "Settlement Delay Beyond SLA",
                "detected_date": "2025-06-28",
                "start_date": "2025-06-25",
                "end_date": "2025-06-28",
                "affected_transactions": "1",
                "expected_value": "T+1",
                "actual_value": "T+3",
                "financial_impact": "0.00",
                "is_recovery_eligible": "false",
                "recoverable_amount": "0.00",
                "recovery_ineligibility_reason": "No direct monetary loss from settlement delay; funds received in full after delay.",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Settlement arrived on T+3 instead of standard T+1; bank technical issue.",
                "evidence_type": "settlement",
                "verification_method_a": "Standard SLA = T+1 business day",
                "verification_method_b": "Actual delivery = T+3 (technical banking delay; full amount credited)",
                "evidence": [
                    {"evidence_id":"ev_2025_H1_dly_001","transaction_id":"set_2025_H1_00198","reference_id":"UTR2025H100198","date":"2025-06-27","expected_value":"T+1","actual_value":"T+3","difference":"+2 days","method":"NEFT/RTGS","evidence_note":"Bank technical issue delayed settlement by 2 days; full amount eventually received."},
                ]
            },
        ],
        "recovery_requests": [
            {
                "request_id": "REQ-2025_H1-001",
                "anomaly_id": "anom_2025_H1_001",
                "created_date": "2025-07-02",
                "resolved_date": "",
                "status": "under_review",
                "amount_requested": "117300.00",
                "amount_recovered": "0.00",
                "recipient": "Razorpay Support",
                "subject": "Request for review of MDR fee rate overcharge",
                "summary": "Dispute filed for 0.50% fee overcharge on 1,150 transactions (INR 1,46,625 affected). Razorpay opened internal audit.",
                "evidence_count": "4",
            },
            {
                "request_id": "REQ-2025_H1-002",
                "anomaly_id": "anom_2025_H1_002",
                "created_date": "2025-06-02",
                "resolved_date": "2025-06-18",
                "status": "resolved",
                "amount_requested": "16065.00",
                "amount_recovered": "16065.00",
                "recipient": "Razorpay Support",
                "subject": "Request for settlement of captured payment pay_2025_H1_00005",
                "summary": "Unsettled captured payment pay_2025_H1_00005 re-identified in settlement batch. INR 16,065.00 credited on 2025-06-18.",
                "evidence_count": "1",
            },
            {
                "request_id": "REQ-2025_H1-003",
                "anomaly_id": "anom_2025_H1_003",
                "created_date": "2025-04-20",
                "resolved_date": "",
                "status": "submitted",
                "amount_requested": "15715.00",
                "amount_recovered": "0.00",
                "recipient": "Razorpay Support",
                "subject": "Request for investigation of missing bank credit - UTR UTR2025H100052",
                "summary": "Bank trace investigation submitted to Razorpay nodal banking team for UTR UTR2025H100052.",
                "evidence_count": "1",
            },
        ],
    },
    "2025_H2": {
        "year": 2025, "half": "H2",
        "months": ["2025-07","2025-08","2025-09","2025-10","2025-11","2025-12"],
        "start_date": "2025-07-01", "end_date": "2025-12-31",
        "tx_count": 19200,
        "target_volume_cr": 48.9,
        "seasonal_weights": [0.12, 0.13, 0.16, 0.23, 0.22, 0.14],
        "refund_count": 370,
        "fee_overcharge_count": 0,
        "severity": "MONITOR",
        "review_status": "healthy",
        "hero_payments": {
            1: 640000,
            5: 320000,
        },
        "anomalies_def": [
            {
                "anomaly_id": "anom_2025_H2_001",
                "type": "settlement_amount_discrepancy",
                "status": "confirmed",
                "title": "Settlement Amount Discrepancy",
                "detected_date": "2025-11-05",
                "start_date": "2025-11-01",
                "end_date": "2025-11-03",
                "affected_transactions": "4",
                "expected_value": "INR 24,18,900.00",
                "actual_value": "INR 23,85,600.00",
                "financial_impact": "33300.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "24975.00",   # 75% of 33300
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Dussehra settlement batch set_2025_H2_00094 was short by INR 33,300.00 versus calculated net payout.",
                "evidence_type": "settlement",
                "verification_method_a": "Calculated net batch = INR 24,18,900.00",
                "verification_method_b": "Actual bank credit = INR 23,85,600.00 (Shortfall: INR 33,300.00)",
                "evidence": [
                    {"evidence_id":"ev_2025_H2_sd_001","transaction_id":"set_2025_H2_00094","reference_id":"UTR2025H200094","date":"2025-11-02","expected_value":"2418900.00","actual_value":"2385600.00","difference":"33300.00","method":"NEFT/RTGS","evidence_note":"Festive season batch shortfall. Dispute submitted with batch reconciliation report."},
                ]
            },
            {
                "anomaly_id": "anom_2025_H2_002",
                "type": "uncredited_refund",
                "status": "confirmed",
                "title": "Refund Not Received by Customer",
                "detected_date": "2025-09-10",
                "start_date": "2025-09-05",
                "end_date": "2025-09-08",
                "affected_transactions": "1",
                "expected_value": "INR 3,200.00",
                "actual_value": "INR 0.00",
                "financial_impact": "3200.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "2720.00",    # 85% of 3200
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Refund for returned personal care products (pay_2025_H2_00005) was debited but not credited to customer bank.",
                "evidence_type": "refund",
                "verification_method_a": "Refund amount = INR 3,200.00 debited from merchant account",
                "verification_method_b": "Customer UPI confirmation = not received (bank trace pending)",
                "evidence": [
                    {"evidence_id":"ev_2025_H2_rf_001","transaction_id":"rfnd_2025_H2_001","reference_id":"pay_2025_H2_00005","date":"2025-09-05","expected_value":"3200.00","actual_value":"0.00","difference":"3200.00","method":"upi","evidence_note":"Refund debited from Zenzo Commerce account; no customer credit confirmation received."},
                ]
            },
        ],
        "recovery_requests": [
            {
                "request_id": "REQ-2025_H2-001",
                "anomaly_id": "anom_2025_H2_001",
                "created_date": "2025-11-08",
                "resolved_date": "2025-12-04",
                "status": "resolved",
                "amount_requested": "24975.00",
                "amount_recovered": "18000.00",
                "recipient": "Razorpay Support",
                "subject": "Request for review of Dussehra batch settlement shortfall",
                "summary": "Settlement shortfall of INR 33,300.00 disputed. Razorpay confirmed INR 18,000.00 processing error; credited back.",
                "evidence_count": "1",
            },
        ],
    },
    "2026_H1": {
        "year": 2026, "half": "H1",
        "months": ["2026-01","2026-02","2026-03","2026-04","2026-05","2026-06"],
        "start_date": "2026-01-01", "end_date": "2026-06-30",
        "tx_count": 20800,
        "target_volume_cr": 53.1,
        "seasonal_weights": [0.15, 0.17, 0.19, 0.17, 0.16, 0.16],
        "refund_count": 420,
        "fee_overcharge_count": 940,
        "severity": "ACTION NEEDED",
        "review_status": "needs_review",
        "hero_payments": {
            1: 1580000,
            2: 3420000,
            5: 2140000,
        },
        "anomalies_def": [
            {
                "anomaly_id": "anom_2026_H1_001",
                "type": "fee_rate_increase",
                "status": "confirmed",
                "title": "Unexpected Fee Rate Increase",
                "detected_date": "2026-06-30",
                "start_date": "2026-01-01",
                "end_date": "2026-06-30",
                "affected_transactions": "940",
                "expected_value": "1.80%",
                "actual_value": "2.30%",
                "financial_impact": "119850.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "95880.00",   # 80% of 119850
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "The agreed MDR was 1.80%, but 2.30% was charged on 940 payments in H1 2026.",
                "evidence_type": "fee",
                "verification_method_a": "Gross affected volume x 0.50% rate diff = INR 1,19,850.00",
                "verification_method_b": "Sum of (actual - expected) fee across 940 payments = INR 1,19,850.00",
                "evidence": [
                    {"evidence_id":"ev_2026_H1_fee_001","transaction_id":"pay_2026_H1_00001","reference_id":"order_2026_H1_00001","date":"2026-03-18","expected_value":"284.40","actual_value":"363.40","difference":"79.00","method":"upi","evidence_note":"1.80% contracted MDR vs 2.30% charged - Holi season lifestyle order."},
                    {"evidence_id":"ev_2026_H1_fee_002","transaction_id":"pay_2026_H1_00002","reference_id":"order_2026_H1_00002","date":"2026-04-14","expected_value":"615.60","actual_value":"786.60","difference":"171.00","method":"card","evidence_note":"1.80% contracted MDR vs 2.30% charged - premium home goods."},
                    {"evidence_id":"ev_2026_H1_fee_003","transaction_id":"pay_2026_H1_00003","reference_id":"order_2026_H1_00003","date":"2026-05-20","expected_value":"162.00","actual_value":"207.00","difference":"45.00","method":"upi","evidence_note":"1.80% contracted MDR vs 2.30% charged."},
                    {"evidence_id":"ev_2026_H1_fee_004","transaction_id":"pay_2026_H1_00004","reference_id":"order_2026_H1_00004","date":"2026-02-08","expected_value":"423.00","actual_value":"540.50","difference":"117.50","method":"netbanking","evidence_note":"1.80% contracted MDR vs 2.30% charged."},
                ]
            },
            {
                "anomaly_id": "anom_2026_H1_002",
                "type": "duplicate_refund",
                "status": "confirmed",
                "title": "Duplicate Refund",
                "detected_date": "2026-05-28",
                "start_date": "2026-05-25",
                "end_date": "2026-05-28",
                "affected_transactions": "1",
                "expected_value": "INR 21,400.00",
                "actual_value": "INR 42,800.00",
                "financial_impact": "21400.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "20330.00",   # 95% of 21400
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "The same refund for a returned premium kitchen appliance was processed twice for payment pay_2026_H1_00005.",
                "evidence_type": "refund",
                "verification_method_a": "Total refunded (INR 42,800.00) - Expected (INR 21,400.00) = INR 21,400.00",
                "verification_method_b": "Duplicate refund transaction rfnd_2026_H1_002 = INR 21,400.00",
                "evidence": [
                    {"evidence_id":"ev_2026_H1_rf_001","transaction_id":"rfnd_2026_H1_001","reference_id":"pay_2026_H1_00005","date":"2026-05-25","expected_value":"21400.00","actual_value":"21400.00","difference":"0.00","method":"upi","evidence_note":"Original legitimate refund for returned kitchen appliance."},
                    {"evidence_id":"ev_2026_H1_rf_002","transaction_id":"rfnd_2026_H1_002","reference_id":"pay_2026_H1_00005","date":"2026-05-28","expected_value":"0.00","actual_value":"21400.00","difference":"21400.00","method":"upi","evidence_note":"Duplicate refund processed in error; excess debit of INR 21,400.00."},
                ]
            },
        ],
        "recovery_requests": [
            {
                "request_id": "REQ-2026_H1-001",
                "anomaly_id": "anom_2026_H1_002",
                "created_date": "2026-05-29",
                "resolved_date": "2026-06-10",
                "status": "resolved",
                "amount_requested": "20330.00",
                "amount_recovered": "20330.00",
                "recipient": "Razorpay Support",
                "subject": "Request for reversal of duplicate refund debit",
                "summary": "Duplicate refund debit of INR 21,400.00 confirmed by Razorpay audit. INR 20,330.00 credited back on 2026-06-10.",
                "evidence_count": "2",
            },
            {
                "request_id": "REQ-2026_H1-002",
                "anomaly_id": "anom_2026_H1_001",
                "created_date": "2026-07-01",
                "resolved_date": "",
                "status": "under_review",
                "amount_requested": "95880.00",
                "amount_recovered": "0.00",
                "recipient": "Razorpay Support",
                "subject": "Request for review of MDR fee overcharge - 940 transactions",
                "summary": "Dispute submitted for 0.50% overcharge on 940 H1 2026 transactions. Under active review.",
                "evidence_count": "4",
            },
        ],
    },
    "2026_H2": {
        "year": 2026, "half": "H2",
        "months": ["2026-07","2026-08","2026-09","2026-10","2026-11","2026-12"],
        "start_date": "2026-07-01", "end_date": "2026-12-31",
        "tx_count": 22600,
        "target_volume_cr": 57.5,
        "seasonal_weights": [0.12, 0.12, 0.15, 0.24, 0.23, 0.14],
        "refund_count": 480,
        "fee_overcharge_count": 2250,
        "severity": "URGENT ACTION",
        "review_status": "action_required",
        "hero_payments": {
            1: 1620000,
            2: 4180000,
            5: 2280000,
            6: 2480000,
            7: 1850000,
            8: 3420000,
        },
        "anomalies_def": [
            {
                "anomaly_id": "anom_2026_H2_001",
                "type": "fee_rate_increase",
                "status": "confirmed",
                "title": "Unexpected Fee Rate Increase",
                "detected_date": "2026-12-31",
                "start_date": "2026-07-01",
                "end_date": "2026-12-31",
                "affected_transactions": "2250",
                "expected_value": "1.80%",
                "actual_value": "2.30%",
                "financial_impact": "286875.00",  # Method-A seed only. Live CSV is engine Method B.
                "is_recovery_eligible": "true",
                "recoverable_amount": "229500.00",  # 80% of 286875
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "The agreed MDR was 1.80%, but 2.30% was charged on 2,250 payments in H2 2026.",
                "evidence_type": "fee",
                "verification_method_a": "Gross affected volume x 0.50% rate diff = INR 2,86,875.00",
                "verification_method_b": "Sum of (actual - expected) fee across 2,250 payments = INR 2,86,875.00",
                "evidence": [
                    {"evidence_id":"ev_2026_H2_fee_001","transaction_id":"pay_2026_H2_00001","reference_id":"order_2026_H2_00001","date":"2026-10-14","expected_value":"291.60","actual_value":"372.60","difference":"81.00","method":"upi","evidence_note":"1.80% MDR vs 2.30% charged - Diwali lifestyle order."},
                    {"evidence_id":"ev_2026_H2_fee_002","transaction_id":"pay_2026_H2_00002","reference_id":"order_2026_H2_00002","date":"2026-11-08","expected_value":"752.40","actual_value":"961.40","difference":"209.00","method":"card","evidence_note":"1.80% MDR vs 2.30% charged - premium home appliance."},
                    {"evidence_id":"ev_2026_H2_fee_003","transaction_id":"pay_2026_H2_00003","reference_id":"order_2026_H2_00003","date":"2026-12-02","expected_value":"198.00","actual_value":"253.00","difference":"55.00","method":"upi","evidence_note":"1.80% MDR vs 2.30% charged."},
                    {"evidence_id":"ev_2026_H2_fee_004","transaction_id":"pay_2026_H2_00004","reference_id":"order_2026_H2_00004","date":"2026-07-20","expected_value":"432.00","actual_value":"552.00","difference":"120.00","method":"netbanking","evidence_note":"1.80% MDR vs 2.30% charged."},
                ]
            },
            {
                "anomaly_id": "anom_2026_H2_002",
                "type": "duplicate_refund",
                "status": "confirmed",
                "title": "Duplicate Refund",
                "detected_date": "2026-12-16",
                "start_date": "2026-12-14",
                "end_date": "2026-12-16",
                "affected_transactions": "1",
                "expected_value": "INR 22,800.00",
                "actual_value": "INR 45,600.00",
                "financial_impact": "22800.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "21660.00",   # 95% of 22800
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "The same refund for a returned fitness tracker was processed twice for payment pay_2026_H2_00005.",
                "evidence_type": "refund",
                "verification_method_a": "Total refunded (INR 45,600.00) - Expected (INR 22,800.00) = INR 22,800.00",
                "verification_method_b": "Duplicate refund transaction rfnd_2026_H2_002 = INR 22,800.00",
                "evidence": [
                    {"evidence_id":"ev_2026_H2_rf_001","transaction_id":"rfnd_2026_H2_001","reference_id":"pay_2026_H2_00005","date":"2026-12-14","expected_value":"22800.00","actual_value":"22800.00","difference":"0.00","method":"upi","evidence_note":"Original legitimate refund for returned fitness tracker."},
                    {"evidence_id":"ev_2026_H2_rf_002","transaction_id":"rfnd_2026_H2_002","reference_id":"pay_2026_H2_00005","date":"2026-12-16","expected_value":"0.00","actual_value":"22800.00","difference":"22800.00","method":"upi","evidence_note":"Duplicate refund processed; excess debit of INR 22,800.00."},
                ]
            },
            {
                "anomaly_id": "anom_2026_H2_003",
                "type": "missing_settlement",
                "status": "confirmed",
                "title": "Payment Not Settled",
                "detected_date": "2026-07-19",
                "start_date": "2026-07-16",
                "end_date": "2026-07-17",
                "affected_transactions": "1",
                "expected_value": "INR 24,800.00",
                "actual_value": "INR 0.00",
                "financial_impact": "24800.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "21080.00",   # 85% of 24800
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Payment pay_2026_H2_00006 was captured on 2026-07-16 but has no matching processed settlement.",
                "evidence_type": "settlement",
                "verification_method_a": "Captured payment amount = INR 24,800.00",
                "verification_method_b": "Settlement reconciliation status = unsettled",
                "evidence": [
                    {"evidence_id":"ev_2026_H2_ms_001","transaction_id":"pay_2026_H2_00006","reference_id":"order_2026_H2_00006","date":"2026-07-16","expected_value":"24800.00","actual_value":"0.00","difference":"24800.00","method":"card","evidence_note":"Captured payment has no matching processed settlement."},
                ]
            },
            {
                "anomaly_id": "anom_2026_H2_004",
                "type": "bank_credit_missing",
                "status": "confirmed",
                "title": "Settlement Returned — Bank IFSC Update",
                "detected_date": "2026-09-20",
                "start_date": "2026-09-15",
                "end_date": "2026-09-18",
                "affected_transactions": "1",
                "expected_value": "INR 18,500.00",
                "actual_value": "INR 0.00",
                "financial_impact": "18500.00",
                "is_recovery_eligible": "false",  # NOT ELIGIBLE: bank returned due to IFSC change
                "recoverable_amount": "0.00",
                "recovery_ineligibility_reason": "Bank trace confirmed settlement was returned due to merchant bank IFSC change; funds returned to Razorpay float. Not recoverable via gateway dispute - requires merchant to update bank IFSC with Razorpay and request re-transfer.",
                "is_ifsc": "true",
                "currency": "INR",
                "root_cause": "Settlement set_2026_H2_00038 (UTR UTR2026H200038) was returned by ICICI Bank due to merchant account IFSC update; not credited.",
                "evidence_type": "settlement",
                "verification_method_a": "Razorpay ledger shows processed settlement = INR 18,500.00",
                "verification_method_b": "ICICI Bank confirmed return due to IFSC mismatch; not creditable via dispute",
                "evidence": [
                    {"evidence_id":"ev_2026_H2_bc_001","transaction_id":"set_2026_H2_00038","reference_id":"UTR2026H200038","date":"2026-09-16","expected_value":"18500.00","actual_value":"0.00","difference":"18500.00","method":"NEFT/RTGS","evidence_note":"Bank trace confirmed operational return due to IFSC update; gateway dispute not applicable."},
                ]
            },
            {
                "anomaly_id": "anom_2026_H2_005",
                "type": "bank_credit_missing",
                "status": "confirmed",
                "title": "Settlement Not Found in Bank",
                "detected_date": "2026-08-12",
                "start_date": "2026-08-08",
                "end_date": "2026-08-10",
                "affected_transactions": "2",
                "expected_value": "INR 34,200.00",
                "actual_value": "INR 0.00",
                "financial_impact": "34200.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "23940.00",   # 70% of 34200
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Razorpay settlement set_2026_H2_00021 (UTR UTR2026H200021) is marked processed but was not credited to the merchant bank account.",
                "evidence_type": "settlement",
                "verification_method_a": "Settlement amount from Razorpay ledger = INR 34,200.00",
                "verification_method_b": "Bank statement search for UTR UTR2026H200021 = 0 records found",
                "evidence": [
                    {"evidence_id":"ev_2026_H2_bc_002","transaction_id":"set_2026_H2_00021","reference_id":"UTR2026H200021","date":"2026-08-09","expected_value":"34200.00","actual_value":"0.00","difference":"34200.00","method":"NEFT/RTGS","evidence_note":"Gateway marked processed; bank statement shows no credit for UTR UTR2026H200021."},
                ]
            },
            {
                "anomaly_id": "anom_2026_H2_006",
                "type": "settlement_amount_discrepancy",
                "status": "confirmed",
                "title": "Settlement Amount Discrepancy",
                "detected_date": "2026-11-10",
                "start_date": "2026-11-05",
                "end_date": "2026-11-07",
                "affected_transactions": "12",
                "expected_value": "INR 1,04,500.00",
                "actual_value": "INR 82,800.00",
                "financial_impact": "21700.00",
                "is_recovery_eligible": "true",
                "recoverable_amount": "16275.00",   # 75% of 21700
                "recovery_ineligibility_reason": "",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Diwali settlement batch set_2026_H2_00087 payout was short by INR 21,700.00 versus calculated net.",
                "evidence_type": "settlement",
                "verification_method_a": "Expected net batch settlement = INR 1,04,500.00",
                "verification_method_b": "Actual bank payout = INR 82,800.00 (Shortfall: INR 21,700.00)",
                "evidence": [
                    {"evidence_id":"ev_2026_H2_sd_001","transaction_id":"set_2026_H2_00087","reference_id":"UTR2026H200087","date":"2026-11-06","expected_value":"104500.00","actual_value":"82800.00","difference":"21700.00","method":"NEFT/RTGS","evidence_note":"Diwali batch settlement shortfall; merchant dispute submitted."},
                ]
            },
            {
                "anomaly_id": "anom_2026_H2_007",
                "type": "settlement_delay",
                "status": "under_review",
                "title": "Settlement Delay Beyond SLA",
                "detected_date": "2026-12-30",
                "start_date": "2026-12-27",
                "end_date": "2026-12-30",
                "affected_transactions": "1",
                "expected_value": "T+1",
                "actual_value": "T+4",
                "financial_impact": "0.00",
                "is_recovery_eligible": "false",
                "recoverable_amount": "0.00",
                "recovery_ineligibility_reason": "No direct monetary loss from settlement delay; funds received in full after delay.",
                "is_ifsc": "false",
                "currency": "INR",
                "root_cause": "Year-end bank holiday caused settlement to arrive on T+4 instead of T+1; full amount credited.",
                "evidence_type": "settlement",
                "verification_method_a": "Standard SLA = T+1 business day",
                "verification_method_b": "Actual delivery = T+4 (year-end bank closure; no financial loss)",
                "evidence": [
                    {"evidence_id":"ev_2026_H2_dly_001","transaction_id":"set_2026_H2_00198","reference_id":"UTR2026H200198","date":"2026-12-29","expected_value":"T+1","actual_value":"T+4","difference":"+3 days","method":"NEFT/RTGS","evidence_note":"Year-end bank holiday delay; full settlement amount received on T+4."},
                ]
            },
        ],
        "recovery_requests": [
            {
                "request_id": "REQ-2026_H2-001",
                "anomaly_id": "anom_2026_H2_001",
                "created_date": "2027-01-02",
                "resolved_date": "",
                "status": "under_review",
                "amount_requested": "229500.00",
                "amount_recovered": "0.00",
                "recipient": "Razorpay Support",
                "subject": "Request for review of MDR fee overcharge - 2,250 transactions",
                "summary": "Dispute filed for 0.50% overcharge on 2,250 H2 2026 transactions (INR 2,86,875.00 total affected). Under active review.",
                "evidence_count": "4",
            },
            {
                "request_id": "REQ-2026_H2-002",
                "anomaly_id": "anom_2026_H2_002",
                "created_date": "2026-12-17",
                "resolved_date": "2026-12-28",
                "status": "resolved",
                "amount_requested": "21660.00",
                "amount_recovered": "21660.00",
                "recipient": "Razorpay Support",
                "subject": "Request for reversal of duplicate refund debit",
                "summary": "Duplicate refund debit of INR 22,800.00 confirmed. INR 21,660.00 credited back on 2026-12-28.",
                "evidence_count": "2",
            },
            {
                "request_id": "REQ-2026_H2-003",
                "anomaly_id": "anom_2026_H2_003",
                "created_date": "2026-07-20",
                "resolved_date": "2026-07-30",
                "status": "resolved",
                "amount_requested": "21080.00",
                "amount_recovered": "21080.00",
                "recipient": "Razorpay Support",
                "subject": "Request for settlement of captured payment pay_2026_H2_00006",
                "summary": "Unsettled captured payment pay_2026_H2_00006 resolved and credited on 2026-07-30.",
                "evidence_count": "1",
            },
            {
                "request_id": "REQ-2026_H2-004",
                "anomaly_id": "anom_2026_H2_005",
                "created_date": "2026-08-14",
                "resolved_date": "",
                "status": "submitted",
                "amount_requested": "23940.00",
                "amount_recovered": "0.00",
                "recipient": "Razorpay Support",
                "subject": "Request for investigation of missing bank credit - UTR UTR2026H200021",
                "summary": "Bank trace investigation submitted to Razorpay nodal banking team.",
                "evidence_count": "1",
            },
            {
                "request_id": "REQ-2026_H2-005",
                "anomaly_id": "anom_2026_H2_006",
                "created_date": "2026-11-12",
                "resolved_date": "",
                "status": "rejected",
                "amount_requested": "16275.00",
                "amount_recovered": "0.00",
                "recipient": "Razorpay Support",
                "subject": "Request for review of Diwali batch settlement shortfall",
                "summary": "Razorpay rejected dispute: internal audit confirmed shortfall was due to merchant-initiated chargeback holdbacks on the same batch.",
                "evidence_count": "1",
            },
        ],
    },
}


def write_csv(path: Path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def pick_amount(rng: random.Random) -> int:
    r = rng.random()
    cumulative = 0.0
    for min_p, max_p, weight in PRICE_TIERS:
        cumulative += weight
        if r <= cumulative:
            return rng.randint(min_p, max_p)
    return rng.randint(149900, 18000000)


def pick_method(rng: random.Random) -> str:
    r = rng.random()
    cumulative = 0.0
    for method, weight in PAYMENT_METHODS:
        cumulative += weight
        if r <= cumulative:
            return method
    return "upi"


def pick_description(rng: random.Random) -> str:
    return rng.choice(PRODUCT_DESCRIPTIONS)


def days_in_month(year: int, month: int) -> int:
    if month == 2:
        return 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
    elif month in [4, 6, 9, 11]:
        return 30
    return 31


def make_ts(year: int, month: int, day: int, rng: random.Random) -> int:
    hour   = rng.randint(7, 23)
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    return int(dt.timestamp())


def generate_period_dataset(p_key: str):
    cfg = PERIOD_CONFIGS[p_key]
    rng = random.Random(42 + int(hashlib.md5(p_key.encode("utf-8")).hexdigest()[:8], 16) % 100000)
    p_dir = ROOT / p_key
    p_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating {p_key} - target {cfg['target_volume_cr']} Cr ...")

    year       = cfg["year"]
    months     = cfg["months"]
    weights    = cfg["seasonal_weights"]
    tx_count   = cfg["tx_count"]
    hero_pmts  = cfg.get("hero_payments", {})

    month_counts = [int(round(tx_count * w)) for w in weights]
    diff = tx_count - sum(month_counts)
    month_counts[-1] += diff

    payments      = []
    daily_batches = {}
    payment_idx   = 1
    overcharge_budget = cfg.get("fee_overcharge_count", 0)
    unsettled_ids = set()

    for anom in cfg["anomalies_def"]:
        if anom["type"] == "missing_settlement" and anom["status"] == "confirmed":
            for ev in anom.get("evidence", []):
                tid = ev.get("transaction_id", "")
                if tid.startswith("pay_"):
                    try:
                        unsettled_ids.add(int(tid.rsplit("_", 1)[-1]))
                    except ValueError:
                        pass
            if not unsettled_ids:
                unsettled_ids.add(6)

    for m_idx, month_str in enumerate(months):
        m_num = int(month_str.split("-")[1])
        dim   = days_in_month(year, m_num)
        count_for_month = month_counts[m_idx]

        for _ in range(count_for_month):
            day    = rng.randint(1, dim)
            ts     = make_ts(year, m_num, day, rng)
            date_str = f"{year}-{m_num:02d}-{day:02d}"
            pay_id   = f"pay_{p_key}_{payment_idx:05d}"
            order_id = f"order_{p_key}_{payment_idx:05d}"
            inv_id   = f"inv_{p_key}_{payment_idx:05d}"
            desc     = pick_description(rng)
            method   = pick_method(rng)

            if payment_idx in hero_pmts:
                amount_paise = hero_pmts[payment_idx]
            else:
                amount_paise = pick_amount(rng)

            is_unsettled = (payment_idx in unsettled_ids)

            is_overcharged = False
            if not is_unsettled and overcharge_budget > 0:
                is_overcharged = True
                overcharge_budget -= 1

            applied_rate = 0.023 if is_overcharged else FEE_RATE
            fee_paise    = round(amount_paise * applied_rate)

            anomaly_type = ""
            if is_unsettled:
                anomaly_type = "missing_settlement"
            elif is_overcharged:
                anomaly_type = "fee_rate_increase"

            row = {
                "id":               pay_id,
                "entity":           "payment",
                "amount":           str(amount_paise),
                "currency":         "INR",
                "status":           "captured",
                "order_id":         order_id,
                "invoice_id":       inv_id,
                "description":      desc,
                "method":           method,
                "captured":         "true",
                "refund_status":    "null",
                "amount_refunded":  "0",
                "fee":              str(fee_paise),
                "tax":              "0",
                "created_at":       str(ts),
                "created_date":     date_str,
                "contract_fee_rate": f"{FEE_RATE:.3f}",
                "applied_fee_rate": f"{applied_rate:.3f}",
                "anomaly_type":     anomaly_type,
                "base_fee":         f"{round(amount_paise * FEE_RATE) / 100:.2f}",
            }
            payments.append(row)

            if not is_unsettled:
                if date_str not in daily_batches:
                    daily_batches[date_str] = []
                daily_batches[date_str].append(row)

            payment_idx += 1

    payments.sort(key=lambda x: int(x["created_at"]))

    pay_fields = [
        "id","entity","amount","currency","status","order_id","invoice_id",
        "description","method","captured","refund_status","amount_refunded",
        "fee","tax","created_at","created_date","contract_fee_rate",
        "applied_fee_rate","anomaly_type","base_fee"
    ]
    write_csv(p_dir / "payments.csv", pay_fields, payments)
    actual_volume = sum(int(p["amount"]) for p in payments) / 100
    print(f"  Payments: {len(payments):,} records, Volume: INR {actual_volume:,.2f} ({actual_volume/1e7:.2f} Cr)")

    # Refunds
    refunds = []
    has_duplicate = any(a["type"] == "duplicate_refund" and a["status"] == "confirmed" for a in cfg["anomalies_def"])
    if has_duplicate and 5 in hero_pmts:
        dup_amount = hero_pmts[5]
        dup_pay_id = f"pay_{p_key}_00005"
        dup_date_str = f"{year}-12-14"
        for anom in cfg["anomalies_def"]:
            if anom["type"] == "duplicate_refund":
                dup_date_str = anom.get("start_date", dup_date_str)
                break
        dup_ts1 = int(datetime.strptime(dup_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()) + 36000
        dup_date2 = datetime.strptime(dup_date_str, "%Y-%m-%d") + timedelta(days=2)
        dup_ts2   = int(dup_date2.replace(tzinfo=timezone.utc).timestamp()) + 50400

        refunds.append({
            "id": f"rfnd_{p_key}_001",
            "entity": "refund",
            "amount": str(dup_amount),
            "currency": "INR",
            "payment_id": dup_pay_id,
            "created_at": str(dup_ts1),
            "created_date": dup_date_str,
            "receipt": f"rcpt_{p_key}_rf_001",
            "status": "processed",
            "speed_requested": "normal",
            "speed_processed": "normal",
            "acquirer_utr": f"UTR_{p_key}_RF_001",
            "anomaly_type": "",
            "duplicate_of_refund_id": "",
        })
        refunds.append({
            "id": f"rfnd_{p_key}_002",
            "entity": "refund",
            "amount": str(dup_amount),
            "currency": "INR",
            "payment_id": dup_pay_id,
            "created_at": str(dup_ts2),
            "created_date": dup_date2.strftime("%Y-%m-%d"),
            "receipt": f"rcpt_{p_key}_rf_002",
            "status": "processed",
            "speed_requested": "normal",
            "speed_processed": "normal",
            "acquirer_utr": f"UTR_{p_key}_RF_002",
            "anomaly_type": "duplicate_refund",
            "duplicate_of_refund_id": f"rfnd_{p_key}_001",
        })
        start_rf = 3
    else:
        start_rf = 1

    has_uncredited = any(a["type"] == "uncredited_refund" and a["status"] == "confirmed" for a in cfg["anomalies_def"])
    if has_uncredited and 5 in hero_pmts:
        uc_amount   = hero_pmts[5]
        uc_pay_id   = f"pay_{p_key}_00005"
        uc_date_str = f"{year}-05-15"
        for anom in cfg["anomalies_def"]:
            if anom["type"] == "uncredited_refund":
                uc_date_str = anom.get("start_date", uc_date_str)
                break
        uc_ts = int(datetime.strptime(uc_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()) + 39600
        refunds.append({
            "id": f"rfnd_{p_key}_001",
            "entity": "refund",
            "amount": str(uc_amount),
            "currency": "INR",
            "payment_id": uc_pay_id,
            "created_at": str(uc_ts),
            "created_date": uc_date_str,
            "receipt": f"rcpt_{p_key}_rf_001",
            "status": "processed",
            "speed_requested": "normal",
            "speed_processed": "normal",
            "acquirer_utr": "",
            "anomaly_type": "uncredited_refund",
            "duplicate_of_refund_id": "",
        })
        start_rf = 2

    refund_count = cfg["refund_count"]
    eligible_pays = [p for p in payments
                     if p["anomaly_type"] == ""
                     and int(p["id"].split("_")[-1]) > 10]
    rng.shuffle(eligible_pays)
    eligible_pays = eligible_pays[:refund_count]

    for rf_idx, pay in enumerate(eligible_pays, start=start_rf):
        pay_amt   = int(pay["amount"])
        rf_pct    = rng.uniform(0.20, 1.00)
        rf_amount = round(pay_amt * rf_pct / 100) * 100
        rf_amount = max(10000, min(rf_amount, pay_amt))

        pay_ts     = int(pay["created_at"])
        delay_sec  = rng.randint(86400, 1209600)
        rf_ts      = pay_ts + delay_sec
        rf_dt      = datetime.fromtimestamp(rf_ts, tz=timezone.utc)
        rf_date    = rf_dt.strftime("%Y-%m-%d")

        refunds.append({
            "id": f"rfnd_{p_key}_{rf_idx:03d}",
            "entity": "refund",
            "amount": str(rf_amount),
            "currency": "INR",
            "payment_id": pay["id"],
            "created_at": str(rf_ts),
            "created_date": rf_date,
            "receipt": f"rcpt_{p_key}_rf_{rf_idx:03d}",
            "status": "processed",
            "speed_requested": "normal",
            "speed_processed": "normal",
            "acquirer_utr": f"UTR_{p_key}_RF_{rf_idx:03d}",
            "anomaly_type": "",
            "duplicate_of_refund_id": "",
        })

    rf_fields = [
        "id","entity","amount","currency","payment_id","created_at","created_date",
        "receipt","status","speed_requested","speed_processed","acquirer_utr",
        "anomaly_type","duplicate_of_refund_id"
    ]
    write_csv(p_dir / "refunds.csv", rf_fields, refunds)
    total_refunds = sum(int(r["amount"]) for r in refunds) / 100
    print(f"  Refunds: {len(refunds):,} records, Total: INR {total_refunds:,.2f}")

    # Settlements
    settlements       = []
    settlement_recon  = []
    settlement_idx    = 1

    bc_missing_settlement_ids = set()
    dedicated_bc_specs = []
    for anom in cfg["anomalies_def"]:
        if anom["type"] == "bank_credit_missing" and anom["status"] == "confirmed":
            impact_paise = int(round(float(anom["financial_impact"]) * 100))
            dedicated_bc_specs.append((anom, impact_paise))

    for date_str, day_payments in sorted(daily_batches.items()):
        if not day_payments:
            continue
        pay_dt     = datetime.strptime(date_str, "%Y-%m-%d")
        settl_dt   = pay_dt + timedelta(days=1)
        settl_date = settl_dt.strftime("%Y-%m-%d")

        batch_gross  = sum(int(p["amount"]) for p in day_payments)
        batch_fees   = sum(int(p["fee"])    for p in day_payments)
        batch_net    = batch_gross - batch_fees

        day_refunds = [r for r in refunds
                       if r.get("created_date") == date_str
                       and r.get("anomaly_type","") not in ["duplicate_refund","uncredited_refund"]]
        day_refund_total = sum(int(r["amount"]) for r in day_refunds)

        settl_amount = max(0, batch_net - day_refund_total)
        if settl_amount == 0:
            continue

        s_id  = f"set_{p_key}_{settlement_idx:05d}"
        utr   = f"UTR{p_key.replace('_','')}{settlement_idx:05d}"
        settl_ts = int(settl_dt.replace(tzinfo=timezone.utc).timestamp()) + 32400

        settl_row = {
            "id":              s_id,
            "entity":          "settlement",
            "amount":          str(settl_amount),
            "status":          "processed",
            "fees":            str(batch_fees),
            "tax":             "0",
            "utr":             utr,
            "created_at":      str(settl_ts),
            "settlement_date": settl_date,
            "transaction_count": str(len(day_payments)),
            "refund_adjustment": f"{day_refund_total / 100:.2f}",
            "anomaly_type":    "",
        }
        settlements.append(settl_row)

        for pay in day_payments:
            recon_row = {
                "entity_id":      pay["id"],
                "type":           "payment",
                "debit":          "0",
                "credit":         pay["amount"],
                "amount":         pay["amount"],
                "currency":       "INR",
                "fee":            pay["fee"],
                "tax":            "0",
                "on_hold":        "false",
                "settled":        "true",
                "created_at":     pay["created_at"],
                "settled_at":     str(settl_ts),
                "settlement_id":  s_id,
                "settlement_utr": utr,
                "payment_id":     pay["id"],
                "order_id":       pay["order_id"],
                "method":         pay["method"],
                "anomaly_type":   pay["anomaly_type"],
            }
            settlement_recon.append(recon_row)

        settlement_idx += 1

    for pay in payments:
        if pay.get("anomaly_type") == "missing_settlement":
            recon_row = {
                "entity_id":      pay["id"],
                "type":           "payment",
                "debit":          "0",
                "credit":         pay["amount"],
                "amount":         pay["amount"],
                "currency":       "INR",
                "fee":            pay["fee"],
                "tax":            "0",
                "on_hold":        "true",
                "settled":        "false",
                "created_at":     pay["created_at"],
                "settled_at":     "",
                "settlement_id":  "",
                "settlement_utr": "",
                "payment_id":     pay["id"],
                "order_id":       pay["order_id"],
                "method":         pay["method"],
                "anomaly_type":   "missing_settlement",
            }
            settlement_recon.append(recon_row)

    # Inject documented settlement shortfalls into the named source settlement.
    for anom in cfg["anomalies_def"]:
        if anom["type"] != "settlement_amount_discrepancy" or anom["status"] != "confirmed":
            continue
        shortfall_paise = int(round(float(anom["financial_impact"]) * 100))
        target_id = ""
        for ev in anom.get("evidence", []):
            if str(ev.get("transaction_id", "")).startswith("set_"):
                target_id = ev["transaction_id"]
                break
        for settl in settlements:
            if settl["id"] == target_id:
                settl["amount"] = str(max(0, int(settl["amount"]) - shortfall_paise))
                settl["anomaly_type"] = "settlement_amount_discrepancy"
                break

    dedicated_missing_ids = set()
    for anom, impact_paise in dedicated_bc_specs:
        s_id = f"set_{p_key}_bc_{anom['anomaly_id'][-3:]}"
        utr = f"UTR{p_key.replace('_', '')}BC{anom['anomaly_id'][-3:]}"
        date_str = anom.get("start_date", cfg["end_date"])
        settl_ts = int(datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()) + 32400
        settlements.append({
            "id": s_id,
            "entity": "settlement",
            "amount": str(impact_paise),
            "status": "processed",
            "fees": "0",
            "tax": "0",
            "utr": utr,
            "created_at": str(settl_ts),
            "settlement_date": date_str,
            "transaction_count": "1",
            "refund_adjustment": "0.00",
            "anomaly_type": "bank_credit_missing",
        })
        dedicated_missing_ids.add(s_id)
        if anom.get("evidence"):
            anom["evidence"][0]["transaction_id"] = s_id
            anom["evidence"][0]["reference_id"] = utr

    s_fields = [
        "id","entity","amount","status","fees","tax","utr","created_at",
        "settlement_date","transaction_count","refund_adjustment","anomaly_type"
    ]
    write_csv(p_dir / "settlements.csv", s_fields, settlements)
    print(f"  Settlements: {len(settlements):,} records")

    recon_fields = [
        "entity_id","type","debit","credit","amount","currency","fee","tax",
        "on_hold","settled","created_at","settled_at","settlement_id",
        "settlement_utr","payment_id","order_id","method","anomaly_type"
    ]
    write_csv(p_dir / "settlement_recon.csv", recon_fields, settlement_recon)

    # Bank credits
    bank_credits = []
    bc_idx = 1

    for settl in settlements:
        s_id = settl["id"]
        utr  = settl["utr"]

        if s_id in dedicated_missing_ids:
            bc_idx += 1
            continue

        credit_date = settl["settlement_date"]

        bc = {
            "bank_credit_id": f"bc_{p_key}_{bc_idx:05d}",
            "settlement_id":  s_id,
            "utr":            utr,
            "credit_date":    credit_date,
            "amount":         settl["amount"],
            "currency":       "INR",
            "bank_status":    "credited",
            "reference":      f"ICICI/{utr}",
        }
        bank_credits.append(bc)
        bc_idx += 1

    bc_fields = [
        "bank_credit_id","settlement_id","utr","credit_date","amount",
        "currency","bank_status","reference"
    ]
    write_csv(p_dir / "bank_credits.csv", bc_fields, bank_credits)
    print(f"  Bank Credits: {len(bank_credits):,} records")

    # Fee contract
    fee_contract = [{
        "contract_id":      f"contract_{p_key}",
        "merchant_id":      MERCHANT_ID,
        "provider":         "Razorpay",
        "fee_type":         "processing_fee",
        "contracted_rate":  str(FEE_RATE),
        "currency":         "INR",
        "effective_from":   cfg["start_date"],
        "effective_to":     cfg["end_date"],
        "notes":            "Synthetic demo pricing. Not real merchant data.",
    }]
    write_csv(p_dir / "fee_contracts.csv",
              ["contract_id","merchant_id","provider","fee_type","contracted_rate",
               "currency","effective_from","effective_to","notes"],
              fee_contract)

    # Anomalies
    anom_fields = [
        "anomaly_id","type","status","title","detected_date","start_date","end_date",
        "affected_transactions","expected_value","actual_value","financial_impact",
        "is_recovery_eligible","recoverable_amount","recovery_ineligibility_reason",
        "currency","root_cause","evidence_type","verification_method_a","verification_method_b"
    ]
    anom_rows = []
    for anom in cfg["anomalies_def"]:
        anom_rows.append({
            "anomaly_id":                  anom["anomaly_id"],
            "type":                        anom["type"],
            "status":                      anom["status"],
            "title":                       anom["title"],
            "detected_date":               anom["detected_date"],
            "start_date":                  anom["start_date"],
            "end_date":                    anom["end_date"],
            "affected_transactions":       str(anom["affected_transactions"]),
            "expected_value":              anom["expected_value"],
            "actual_value":                anom["actual_value"],
            "financial_impact":            str(anom["financial_impact"]),
            "is_recovery_eligible":        str(anom.get("is_recovery_eligible","true")),
            "recoverable_amount":          str(anom.get("recoverable_amount","0.00")),
            "recovery_ineligibility_reason": str(anom.get("recovery_ineligibility_reason","")),
            "currency":                    anom["currency"],
            "root_cause":                  anom["root_cause"],
            "evidence_type":               anom["evidence_type"],
            "verification_method_a":       anom["verification_method_a"],
            "verification_method_b":       anom["verification_method_b"],
        })
    write_csv(p_dir / "anomalies.csv", anom_fields, anom_rows)

    # Anomaly evidence
    ev_fields = [
        "evidence_id","anomaly_id","transaction_id","reference_id","date",
        "expected_value","actual_value","difference","gross_amount","method","evidence_note"
    ]
    ev_rows = []
    for anom in cfg["anomalies_def"]:
        for ev in anom.get("evidence", []):
            ev_rows.append({
                "evidence_id":      ev["evidence_id"],
                "anomaly_id":       anom["anomaly_id"],
                "transaction_id":   ev["transaction_id"],
                "reference_id":     ev["reference_id"],
                "date":             ev["date"],
                "expected_value":   ev["expected_value"],
                "actual_value":     ev["actual_value"],
                "difference":       ev["difference"],
                "gross_amount":     ev.get("gross_amount", "0.00"),
                "method":           ev["method"],
                "evidence_note":    ev["evidence_note"],
            })
    write_csv(p_dir / "anomaly_evidence.csv", ev_fields, ev_rows)

    # Recovery requests
    req_fields = [
        "request_id","anomaly_id","created_date","resolved_date","status",
        "amount_requested","amount_recovered","recipient","subject","summary","evidence_count"
    ]
    req_rows = []
    for req in cfg.get("recovery_requests", []):
        req_rows.append({
            "request_id":       req["request_id"],
            "anomaly_id":       req["anomaly_id"],
            "created_date":     req["created_date"],
            "resolved_date":    req.get("resolved_date",""),
            "status":           req["status"],
            "amount_requested": str(req["amount_requested"]),
            "amount_recovered": str(req["amount_recovered"]),
            "recipient":        req["recipient"],
            "subject":          req["subject"],
            "summary":          req["summary"],
            "evidence_count":   str(req["evidence_count"]),
        })
    write_csv(p_dir / "recovery_requests.csv", req_fields, req_rows)

    # Dataset meta
    confirmed_loss   = sum(float(a["financial_impact"]) for a in cfg["anomalies_def"] if a["status"] == "confirmed")
    potential_recov  = sum(float(a.get("recoverable_amount","0")) for a in cfg["anomalies_def"] if a["status"] == "confirmed")
    req_total        = sum(float(r["amount_requested"]) for r in cfg.get("recovery_requests",[]))
    recovered_total  = sum(float(r["amount_recovered"]) for r in cfg.get("recovery_requests",[]))

    assert potential_recov <= confirmed_loss, \
        f"VALIDATION FAILED {p_key}: Potential Recovery ({potential_recov}) >= Money Affected ({confirmed_loss})"

    for_action = confirmed_loss >= 100000
    if for_action:
        assert potential_recov < confirmed_loss, \
            f"VALIDATION FAILED {p_key}: Action period must have Potential Recovery < Money Affected"

    meta = {
        "merchant_name":    MERCHANT_NAME,
        "merchant_id":      MERCHANT_ID,
        "currency":         "INR",
        "payment_provider": "Razorpay",
        "dataset_type":     "synthetic_demo",
        "selection_seed":   20260901,
        "note":             "Synthetic data for demonstration purposes only. Not real merchant, payment, or customer data.",
        "period_key":       p_key,
        "period_start":     cfg["start_date"],
        "period_end":       cfg["end_date"],
        "review_status":    cfg.get("review_status", "healthy"),
        "is_action_required": confirmed_loss >= 100000,
    }
    with (p_dir / "dataset_meta.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Summary CSV
    total_volume = sum(int(p["amount"]) for p in payments) / 100
    total_fees   = sum(int(p["fee"])    for p in payments) / 100
    total_refunds_amt = sum(int(r["amount"]) for r in refunds) / 100
    total_settl   = sum(int(s["amount"]) for s in settlements) / 100
    confirmed_cnt = sum(1 for a in cfg["anomalies_def"] if a["status"] == "confirmed")
    ur_cnt        = sum(1 for a in cfg["anomalies_def"] if a["status"] == "under_review")

    summary_row = {
        "period":                  p_key,
        "start_date":              cfg["start_date"],
        "end_date":                cfg["end_date"],
        "status":                  cfg.get("review_status", "healthy"),
        "transaction_count":       str(len(payments)),
        "gross_payment_volume":    f"{total_volume:.2f}",
        "fee_total":               f"{total_fees:.2f}",
        "refund_total":            f"{total_refunds_amt:.2f}",
        "settlement_total":        f"{total_settl:.2f}",
        "confirmed_anomaly_count": str(confirmed_cnt),
        "under_review_count":      str(ur_cnt),
        "confirmed_loss":          f"{confirmed_loss:.2f}",
        "potential_recovery":      f"{potential_recov:.2f}",
        "recovery_requested":      f"{req_total:.2f}",
        "recovered":               f"{recovered_total:.2f}",
        "currency":                "INR",
    }
    write_csv(p_dir / "summary.csv",
              ["period","start_date","end_date","status","transaction_count",
               "gross_payment_volume","fee_total","refund_total","settlement_total",
               "confirmed_anomaly_count","under_review_count","confirmed_loss",
               "potential_recovery","recovery_requested","recovered","currency"],
              [summary_row])

    print(f"  Volume: INR {total_volume/1e7:.2f} Cr | Fees: INR {total_fees:,.2f}")
    print(f"  Refunds: INR {total_refunds_amt:,.2f} | Settlements: INR {total_settl/1e7:.2f} Cr")
    print(f"  Money Affected: INR {confirmed_loss:,.2f}")
    print(f"  Potential Recovery: INR {potential_recov:,.2f}")
    if confirmed_loss > 0:
        print(f"  Recovery %: {(potential_recov/confirmed_loss*100):.1f}%")
    print(f"  Recovery Req'd: INR {req_total:,.2f} | Recovered: INR {recovered_total:,.2f}")
    print(f"  Severity: {cfg.get('severity','?')} | Confirmed anomalies: {confirmed_cnt}")
    if for_action and potential_recov >= confirmed_loss:
        print(f"  *** HARD GATE FAILURE: Potential Recovery >= Money Affected ***")
    else:
        print(f"  [PASS] Potential Recovery < Money Affected" if confirmed_loss > 0 else "  [PASS] Clean period")

    return {
        "period": p_key,
        "volume_cr": total_volume / 1e7,
        "tx_count": len(payments),
        "refunds": total_refunds_amt,
        "fees": total_fees,
        "money_affected": confirmed_loss,
        "potential_recovery": potential_recov,
        "recovery_req": req_total,
        "recovered": recovered_total,
        "severity": cfg.get("severity","?"),
    }


if __name__ == "__main__":
    print("=" * 70)
    print(f"Reclaim Dataset Generator - {MERCHANT_NAME} ({MERCHANT_ID})")
    print("Synthetic B2C/D2C E-Commerce Demo Data")
    print("NOT real merchant data.")
    print("=" * 70)

    results = []
    for p_key in PERIODS:
        r = generate_period_dataset(p_key)
        results.append(r)

    print("\n" + "=" * 70)
    print("FINAL QA SUMMARY")
    print("=" * 70)
    print(f"{'Period':<12} {'Volume(Cr)':>10} {'Tx':>6} {'MoneyAff':>16} {'PotRec':>16} {'PotRec%':>8} {'Severity':<20}")
    print("-" * 90)
    all_pass = True
    for r in results:
        pct = (r["potential_recovery"] / r["money_affected"] * 100) if r["money_affected"] > 0 else 0
        line = (
            f"{r['period']:<12} "
            f"{r['volume_cr']:>9.2f}Cr "
            f"{r['tx_count']:>6,} "
            f"INR {r['money_affected']:>12,.2f} "
            f"INR {r['potential_recovery']:>12,.2f} "
            f"{pct:>7.1f}% "
            f"{r['severity']:<20}"
        )
        is_action = r["money_affected"] >= 100000
        if is_action and r["potential_recovery"] >= r["money_affected"]:
            line += " *** FAIL: PotRec >= MoneyAffected ***"
            all_pass = False
        elif r["money_affected"] > 0:
            line += " [PASS]"
        print(line)

    print("-" * 90)
    total_vol = sum(r["volume_cr"] for r in results)
    print(f"Total 2024-2026 volume: INR {total_vol:.2f} Cr")
    print()
    if all_pass:
        print("[PASS] ALL HARD GATES PASSED - Potential Recovery < Money Affected for all action periods")
    else:
        print("*** HARD GATE FAILURES DETECTED - see above ***")
    print("=" * 70)
