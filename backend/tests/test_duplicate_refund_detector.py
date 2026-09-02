from app.services.data_repository import data_repository
from app.services.detectors.duplicate_refund_detector import DuplicateRefundDetector


def test_duplicate_refund_hero_scenario():
    detector = DuplicateRefundDetector(data_repository)
    findings = detector.detect(period="2026_H2")

    assert len(findings) == 1
    dup_finding = findings[0]

    assert dup_finding.finding_id == "anom_2026_H2_002"
    assert dup_finding.type == "duplicate_refund"
    assert dup_finding.status == "confirmed"

    # Crucial financial rule: impact is the EXCESS amount (₹22,800.00)
    assert dup_finding.financial_impact_inr == 22800.00
    assert dup_finding.financial_impact_paise == 2280000

    # Verify evidence references both refunds
    assert len(dup_finding.evidence) == 2
    ev1, ev2 = dup_finding.evidence[0], dup_finding.evidence[1]
    assert ev1.financial_impact_paise == 0
    assert ev2.financial_impact_paise == 2280000


def test_duplicate_refund_period_filtering():
    detector = DuplicateRefundDetector(data_repository)

    # Periods with duplicate refund
    assert len(detector.detect(period="2026_H2")) == 1
    assert len(detector.detect(period="2026_H1")) == 1
    assert len(detector.detect(period="2024_H2")) == 1

    # Periods without duplicate refund
    assert len(detector.detect(period="2025_H2")) == 0
    assert len(detector.detect(period="2025_H1")) == 0
    assert len(detector.detect(period="2024_H1")) == 0
