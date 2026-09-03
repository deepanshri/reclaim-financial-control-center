from app.services.data_loader import DataLoader
from app.services.data_repository import DataRepository
from app.services.financial_engine import FinancialEngine
from tests.http import authenticated_client


def test_repository_loads_only_requested_period():
    repo = DataRepository()
    repo.ensure_period("2026_H2")
    assert repo.loaded_period_keys() == ["2026_H2"]
    assert len(repo.get_all_payments(period="2026_H2")) > 0
    assert repo.loaded_period_keys() == ["2026_H2"]


def test_period_resolution_does_not_parse_csvs():
    repo = DataRepository()
    assert repo.normalize_period_key("2024_H1") == "2024_H1"
    assert repo.loaded_period_keys() == []


def test_merchant_meta_does_not_hydrate_payments():
    repo = DataRepository()
    data = repo.get_merchant_data(period="2026_H2")
    assert data["merchant_name"] == "Zenzo Commerce"
    assert repo.loaded_period_keys() == []


def test_engine_first_status_does_not_load_all_periods():
    repo = DataRepository()
    engine = FinancialEngine(repo)
    status = engine.get_financial_status(period="2026_H2")
    assert status["money_affected_inr"] > 0
    assert repo.loaded_period_keys() == ["2026_H2"]
    catalog = engine.get_available_periods(eager=False)
    assert len(catalog) == 6
    current = next(item for item in catalog if item["key"] == "2026_H2")
    assert current["confirmed_loss_inr"] == status["money_affected_inr"]


def test_data_loader_loads_one_period_on_accessor():
    loader = DataLoader()
    payments, total = loader.get_payments(period="2024_H1", page=1, page_size=5)
    assert total > 0
    assert len(payments) == 5
    assert loader._loaded_periods == {"2024_H1"}


def test_health_stays_fast_before_financial_load():
    client = authenticated_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
