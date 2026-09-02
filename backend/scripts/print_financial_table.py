"""Print the final financial table from the live engine."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.data_repository import DataRepository
from app.services.financial_engine import FinancialEngine

repo = DataRepository()
repo.load()
eng = FinancialEngine(repo)

PERIODS = ["2024_H1", "2024_H2", "2025_H1", "2025_H2", "2026_H1", "2026_H2"]
print("period,volume,pays,refunds,ma,pr,requested,recovered,under_review,not_recovered,status,health")
for p in PERIODS:
    s = eng.get_financial_status(period=p)
    pays = repo.get_all_payments(period=p)
    refs = repo.get_all_refunds(period=p)
    print(
        f"{p},{s['total_payment_volume_inr']:.2f},{len(pays)},{len(refs)},"
        f"{s['money_affected_inr']:.2f},{s['potential_recovery_inr']:.2f},"
        f"{s['recovery_requested_inr']:.2f},{s['recovered_inr']:.2f},"
        f"{s['under_review_inr']:.2f},{s['not_recovered_inr']:.2f},"
        f"{s['severity_label']},{s['health_score']}"
    )
    findings = [f for f in eng.get_findings(period=p) if f.status == "confirmed"]
    for f in findings:
        print(
            f"  FINDING {f.finding_id} type={f.type} MA={f.financial_impact_inr:.2f} "
            f"PR={f.recoverable_amount_inr:.2f} eligible={f.is_recovery_eligible}"
        )
