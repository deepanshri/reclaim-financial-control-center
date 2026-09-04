from app.services.financial_engine import financial_engine


def test_financial_engine_status_action_period():
    status = financial_engine.get_financial_status(period="2026_H2")
    assert status["total_payment_volume_inr"] > 0
    assert status["total_fees_inr"] > 0
    assert status["confirmed_loss_inr"] > 0
    assert status["health_score"] >= 0 and status["health_score"] <= 100
    assert status["confirmed_finding_count"] >= 5
    assert status["is_action_required"] is True
    assert status["review_status"] == "action_required"


def test_financial_engine_status_healthy_period():
    status = financial_engine.get_financial_status(period="2024_H1")
    assert status["total_payment_volume_inr"] > 0
    assert 0 < status["confirmed_loss_inr"] < 100000.0
    assert status["confirmed_finding_count"] >= 1
    assert status["health_score"] >= 80
    assert status["is_action_required"] is False
    assert status["review_status"] == "healthy"
    assert status["severity_level"] == "healthy"
    assert status["severity_label"] == "MONITOR"


def test_financial_engine_recovery_totals():
    requests = financial_engine.get_recovery_requests(period="2026_H2")
    assert len(requests) >= 2

    total_requested = sum(r.amount_requested_inr for r in requests)
    total_recovered = sum(r.amount_recovered_inr for r in requests if r.status == "resolved")
    assert total_requested > 0
    assert total_recovered > 0


def test_financial_engine_available_periods():
    periods = financial_engine.get_available_periods()
    assert len(periods) == 6
    action_periods = [p["key"] for p in periods if p["is_action_required"]]
    healthy_periods = [p["key"] for p in periods if not p["is_action_required"]]
    assert sorted(action_periods) == ["2024_H2", "2025_H1", "2026_H1", "2026_H2"]
    assert sorted(healthy_periods) == ["2024_H1", "2025_H2"]


def test_statement_activity_ledger():
    items, total, summary = financial_engine.get_statement_ledger(period="2026_H2", page=1, page_size=20)
    assert total > 0
    assert len(items) == 20
    assert summary["total_payments_inr"] > 0
    assert summary["matching_rate_percent"] > 90


def test_statement_first_page_is_not_only_refunds():
    """The T+1 refund tail must not sort ahead of the period's own activity."""
    items, _, _ = financial_engine.get_statement_ledger(period="2026_H2", page=1, page_size=25)
    types = {item["type"] for item in items}
    assert types != {"Refund"}
    assert "Payment" in types


def test_statement_is_chronological_and_keeps_every_source_type():
    items, total, _ = financial_engine.get_statement_ledger(
        period="2026_H2", page=1, page_size=100_000
    )
    assert len(items) == total

    timestamps = [item["timestamp"] for item in items]
    assert timestamps == sorted(timestamps)

    # Every ledger row is unique and every type present in the dataset survives.
    assert len({item["id"] for item in items}) == len(items)
    assert {item["type"] for item in items} == {"Payment", "Fee", "Bank Deposit", "Refund"}

    # Rows dated past the six calendar months are the genuine T+1 tail and stay labelled.
    spillover = [item for item in items if not item["date"].startswith("2026-")]
    assert spillover, "2026_H2 carries a T+1 settlement/refund tail"
    assert all("T+1" in item["status"] for item in spillover)
    assert items[-1] in spillover


def test_statement_type_filter_applies_to_the_whole_period():
    _, all_total, _ = financial_engine.get_statement_ledger(period="2026_H2", page=1, page_size=1)
    seen = 0
    for ledger_type in ["Payment", "Fee", "Bank Deposit", "Refund"]:
        items, total, _ = financial_engine.get_statement_ledger(
            period="2026_H2", page=1, page_size=10, txn_type=ledger_type
        )
        assert total > 0
        assert all(item["type"] == ledger_type for item in items)
        seen += total
    assert seen == all_total
