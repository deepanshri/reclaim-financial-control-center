from typing import Any, Dict, List, Optional
from app.models.domain import EvidenceItem, Finding
from app.services.data_repository import DataRepository


class ReferenceAnomalyAuditor:
    """
    Audits reference anomalies against raw calculation findings.
    Attaches under-review items or reference data if present.
    """

    def __init__(self, repo: DataRepository):
        self.repo = repo

    def get_audited_reference_findings(
        self,
        confirmed_finding_ids: List[str],
        period: Optional[str] = None,
        year: Optional[int] = None,
        confirmed_types: Optional[List[str]] = None,
    ) -> List[Finding]:
        p_key = self.repo.normalize_period_key(period, year)
        ref_anomalies = self.repo.get_reference_anomalies(period=p_key)
        ref_evidence = self.repo.get_reference_evidence(period=p_key)

        types_set = set(confirmed_types or [])

        findings: List[Finding] = []
        for ref in ref_anomalies:
            anom_id = ref.get("anomaly_id", "")
            anom_type = ref.get("type", "")
            # Skip if already detected and confirmed by rule detectors
            if anom_id in confirmed_finding_ids or anom_type in types_set:
                continue

            status = ref.get("status", "under_review")
            impact_val = float(ref.get("financial_impact", 0.0))
            impact_paise = int(round(impact_val * 100))

            ev_list: List[EvidenceItem] = []
            for ev_row in ref_evidence:
                if ev_row.get("anomaly_id") == anom_id:
                    gross_p = int(round(float(ev_row.get("gross_amount", 0.0)) * 100))
                    impact_p = int(round(float(ev_row.get("difference", 0.0)) * 100)) if str(ev_row.get("difference", "")).replace(".", "").isdigit() else 0
                    ev_item = EvidenceItem(
                        evidence_id=ev_row.get("evidence_id", f"ev_ref_{anom_id}"),
                        source_record_id=ev_row.get("transaction_id", ""),
                        reference_id=ev_row.get("reference_id", ""),
                        date=ev_row.get("date", ref.get("detected_date", "")),
                        method=ev_row.get("method", "UPI"),
                        gross_amount_paise=gross_p,
                        expected_value=ev_row.get("expected_value", ""),
                        actual_value=ev_row.get("actual_value", ""),
                        difference=ev_row.get("difference", ""),
                        financial_impact_paise=impact_p,
                        evidence_note=ev_row.get("evidence_note", ""),
                    )
                    ev_list.append(ev_item)

            aff_count = int(ref.get("affected_transactions", 1)) if str(ref.get("affected_transactions", "1")).isdigit() else 1
            is_eligible = ref.get("is_recovery_eligible", "true").lower() in ["true", "1"]
            inelig_reason = ref.get("recovery_ineligibility_reason", "")
            # Settlement delay is never treated as permanent lost money.
            if anom_type == "settlement_delay":
                impact_paise = 0
                rec_paise = 0
                is_eligible = False
                if not inelig_reason:
                    inelig_reason = "Settlement delay is an SLA breach with no permanent monetary loss."
            else:
                rec_val = float(ref.get("recoverable_amount", 0.0) or 0.0)
                rec_paise = int(round(rec_val * 100)) if is_eligible else 0

            finding = Finding(
                finding_id=anom_id,
                type=ref.get("type", "other"),
                status=status,
                title=ref.get("title", "Under Review Issue"),
                description=ref.get("root_cause", "Under review by settlement audit rules."),
                simple_explanation=ref.get("root_cause", "This payment activity is currently being checked by Reclaim."),
                financial_impact_paise=impact_paise,
                currency=ref.get("currency", "INR"),
                affected_transaction_count=aff_count,
                detected_at=ref.get("detected_date", ""),
                start_date=ref.get("start_date", ref.get("detected_date", "")),
                end_date=ref.get("end_date", ref.get("detected_date", "")),
                confidence=0.75 if status == "under_review" else 0.50,
                root_cause_reference=ref.get("root_cause", "Review pending"),
                source_record_ids=[],
                evidence=ev_list,
                verification_method_a="Reference dataset audit validation",
                verification_method_b="Source cross-check",
                is_verified=status == "confirmed",
                is_recovery_eligible=is_eligible,
                recoverable_amount_paise=rec_paise,
                recovery_ineligibility_reason=inelig_reason,
            )
            findings.append(finding)

        return findings
