from app.services.data_repository import data_repository
from app.services.detectors.missing_settlement_detector import MissingSettlementDetector


def test_missing_settlement_detector():
    detector = MissingSettlementDetector(data_repository)
    findings = detector.detect(period="2026_H2")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.finding_id == "anom_2026_H2_003"
    assert finding.type == "missing_settlement"
    assert finding.status == "confirmed"
    assert finding.financial_impact_inr == 22800.00


def test_missing_settlement_period_filtering():
    detector = MissingSettlementDetector(data_repository)

    assert len(detector.detect(period="2026_H2")) == 1
    assert len(detector.detect(period="2025_H1")) == 1
    assert len(detector.detect(period="2024_H2")) == 0

    assert len(detector.detect(period="2026_H1")) == 0
    assert len(detector.detect(period="2025_H2")) == 0
    assert len(detector.detect(period="2024_H1")) == 0
