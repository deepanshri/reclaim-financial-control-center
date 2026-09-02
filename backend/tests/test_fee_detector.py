from app.services.data_repository import data_repository
from app.services.detectors.fee_detector import FeeAnomalyDetector


def test_fee_detector_hero_scenario():
    detector = FeeAnomalyDetector(data_repository)
    findings = detector.detect(period="2026_H2")

    assert len(findings) == 1
    hero = findings[0]

    # Verify hero fields
    assert hero.finding_id == "anom_2026_H2_001"
    assert hero.type == "fee_rate_increase"
    assert hero.status == "confirmed"
    assert hero.affected_transaction_count > 0
    assert hero.financial_impact_inr > 100000.0
    assert hero.is_verified is True
    assert len(hero.evidence) == 4

    # Check evidence structure
    for ev in hero.evidence:
        assert ev.source_record_id.startswith("pay_")
        assert ev.gross_amount_inr > 0
        assert "1.80%" in ev.expected_value
        assert "2.30%" in ev.actual_value
        assert "+0.50%" in ev.difference


def test_fee_detector_period_filtering():
    detector = FeeAnomalyDetector(data_repository)

    # Periods with fee rate overcharge
    assert len(detector.detect(period="2026_H2")) == 1
    assert len(detector.detect(period="2026_H1")) == 1
    assert len(detector.detect(period="2025_H1")) == 1
    assert len(detector.detect(period="2024_H2")) == 1

    # Periods without fee rate anomalies have 0 fee anomalies
    assert len(detector.detect(period="2025_H2")) == 0
    assert len(detector.detect(period="2024_H1")) == 0
