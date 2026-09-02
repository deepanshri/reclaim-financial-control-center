import pytest
from pathlib import Path
from app.services.data_loader import DataLoader, DatasetValidationError, PERIOD_KEYS


def test_data_loader_validates_and_loads():
    loader = DataLoader()
    loader.load_dataset()
    assert len(loader.get_all_period_keys()) == 6
    status = loader.get_dataset_status(period="2026_H2")

    assert status["merchant_name"] == "Zenzo Commerce"
    assert status["payment_provider"] == "Razorpay"
    assert status["payment_record_count"] > 0
    assert status["confirmed_anomaly_count"] >= 5


def test_data_loader_missing_file_behavior(tmp_path: Path):
    empty_loader = DataLoader(data_dir=tmp_path)
    with pytest.raises(DatasetValidationError) as excinfo:
        empty_loader.load_dataset()
    assert "missing" in str(excinfo.value).lower() or "not exist" in str(excinfo.value).lower()


def test_data_loader_monetary_preservation():
    loader = DataLoader()
    loader.load_dataset()
    payments, total = loader.get_payments(period="2026_H2", page=1, page_size=10)
    assert total > 0
    for p in payments:
        amount = int(p["amount"])
        assert isinstance(amount, int)
        assert amount > 0


def test_data_loader_all_six_periods():
    loader = DataLoader()
    loader.load_dataset()
    for p_key in PERIOD_KEYS:
        p_data = loader.get_period_data(p_key)
        assert len(p_data.payments) > 0
        assert len(p_data.settlements) > 0
