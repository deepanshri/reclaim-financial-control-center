import csv
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.exceptions import InvalidPeriodError

logger = logging.getLogger("reclaim.data_loader")

PERIOD_KEYS = ["2024_H1", "2024_H2", "2025_H1", "2025_H2", "2026_H1", "2026_H2"]
DEFAULT_PERIOD = "2026_H2"

REQUIRED_PERIOD_FILES = [
    "dataset_meta.json",
    "payments.csv",
    "refunds.csv",
    "settlements.csv",
    "settlement_recon.csv",
    "bank_credits.csv",
    "fee_contracts.csv",
    "anomalies.csv",
    "anomaly_evidence.csv",
    "recovery_requests.csv",
    "summary.csv",
]


class DatasetValidationError(RuntimeError):
    """Raised when one or more required dataset files are missing or corrupted."""
    pass


class PeriodData:
    """Holds loaded in-memory records for a single half-year period."""

    def __init__(self, key: str, period_dir: Path):
        self.key = key
        self.period_dir = period_dir
        self.meta: Dict[str, Any] = {}
        self.payments: List[Dict[str, Any]] = []
        self.refunds: List[Dict[str, Any]] = []
        self.settlements: List[Dict[str, Any]] = []
        self.settlement_recon: List[Dict[str, Any]] = []
        self.bank_credits: List[Dict[str, Any]] = []
        self.fee_contracts: List[Dict[str, Any]] = []
        self.anomalies: List[Dict[str, Any]] = []
        self.anomaly_evidence: List[Dict[str, Any]] = []
        self.recovery_requests: List[Dict[str, Any]] = []
        self.summary: List[Dict[str, Any]] = []


class DataLoader:
    """
    Centralized, thread-safe data access layer for the Reclaim Six Half-Year Datasets.
    Loads and caches financial records in memory per period (2024_H1 to 2026_H2).
    """

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.data_dir = base_dir / "data" / "reclaim_six_half_year_datasets"
        else:
            self.data_dir = Path(data_dir)

        self._periods: Dict[str, PeriodData] = {}
        self._selection_meta: Dict[str, Any] = {}
        self._is_loaded: bool = False
        self._load_lock = threading.Lock()

    def normalize_period_key(self, period: Optional[str] = None, year: Optional[int] = None) -> str:
        """Resolves period string or year to a valid period key. Explicit unknown keys are never substituted."""
        self.load_dataset()
        known = list(self._periods.keys()) or list(PERIOD_KEYS)

        if period:
            cleaned = period.strip().replace("-", "_").replace(" ", "_").upper()
            if cleaned in self._periods:
                return cleaned
            for key in PERIOD_KEYS:
                if (key == cleaned or key.replace("_", "") == cleaned) and key in self._periods:
                    return key
            raise InvalidPeriodError(period, known)

        if year is not None:
            yr_str = str(year)
            for key in (f"{yr_str}_H2", f"{yr_str}_H1"):
                if key in self._periods:
                    return key
            raise InvalidPeriodError(str(year), known)

        if DEFAULT_PERIOD in self._periods:
            return DEFAULT_PERIOD
        if known:
            return known[-1]
        return DEFAULT_PERIOD

    def verify_files_exist(self) -> None:
        """Validates dataset root and all period folders."""
        if not self.data_dir.exists() or not self.data_dir.is_dir():
            raise DatasetValidationError(
                f"Dataset root directory does not exist: {self.data_dir.resolve()}"
            )

        for p_key in PERIOD_KEYS:
            p_dir = self.data_dir / p_key
            if not p_dir.exists() or not p_dir.is_dir():
                raise DatasetValidationError(f"Period folder missing: {p_dir.resolve()}")
            missing = [f for f in REQUIRED_PERIOD_FILES if not (p_dir / f).is_file()]
            if missing:
                raise DatasetValidationError(f"Period {p_key} missing files: {', '.join(missing)}")

    def load_dataset(self, force_reload: bool = False) -> None:
        with self._load_lock:
            self._load_unlocked(force_reload=force_reload)

    def _load_unlocked(self, force_reload: bool = False) -> None:
        if self._is_loaded and not force_reload:
            return

        self.verify_files_exist()
        logger.info(f"Loading Reclaim six half-year datasets from {self.data_dir.resolve()}")

        # Load selection metadata if present
        selection_file = self.data_dir / "selection.json"
        if selection_file.is_file():
            with selection_file.open("r", encoding="utf-8") as f:
                self._selection_meta = json.load(f)

        self._periods = {}
        for p_key in PERIOD_KEYS:
            p_dir = self.data_dir / p_key
            p_data = PeriodData(p_key, p_dir)

            # 1. dataset_meta.json
            with (p_dir / "dataset_meta.json").open("r", encoding="utf-8") as f:
                p_data.meta = json.load(f)

            # 2. payments.csv
            p_data.payments = self._load_csv(p_dir / "payments.csv")
            for p in p_data.payments:
                if "created_at" in p and p["created_at"]:
                    try:
                        ts = int(p["created_at"])
                        p["created_at_dt"] = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                        p["created_date"] = p["created_at_dt"][:10]
                        p["created_year"] = int(p["created_date"][:4])
                    except (ValueError, TypeError):
                        p["created_at_dt"] = str(p.get("created_at", ""))
                        p["created_date"] = str(p.get("created_date", ""))
                        p["created_year"] = int(p_key[:4])

            # 3. refunds.csv
            p_data.refunds = self._load_csv(p_dir / "refunds.csv")
            for r in p_data.refunds:
                if "created_at" in r and r["created_at"]:
                    try:
                        ts = int(r["created_at"])
                        r["created_at_dt"] = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                        r["created_date"] = r["created_at_dt"][:10]
                        r["created_year"] = int(r["created_date"][:4])
                    except (ValueError, TypeError):
                        r["created_at_dt"] = str(r.get("created_at", ""))
                        r["created_date"] = str(r.get("created_date", ""))
                        r["created_year"] = int(p_key[:4])

            # 4. settlements.csv
            p_data.settlements = self._load_csv(p_dir / "settlements.csv")
            for s in p_data.settlements:
                if "created_at" in s and s["created_at"]:
                    try:
                        ts = int(s["created_at"])
                        s["created_at_dt"] = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    except (ValueError, TypeError):
                        s["created_at_dt"] = str(s.get("created_at", ""))

            # 5. settlement_recon.csv
            p_data.settlement_recon = self._load_csv(p_dir / "settlement_recon.csv")

            # 6. bank_credits.csv
            p_data.bank_credits = self._load_csv(p_dir / "bank_credits.csv")

            # 7. fee_contracts.csv
            p_data.fee_contracts = self._load_csv(p_dir / "fee_contracts.csv")

            # 8. anomalies.csv
            p_data.anomalies = self._load_csv(p_dir / "anomalies.csv")
            for a in p_data.anomalies:
                if "affected_transactions" in a:
                    try:
                        a["affected_transactions"] = int(a["affected_transactions"])
                    except (ValueError, TypeError):
                        pass
                if "financial_impact" in a:
                    try:
                        a["financial_impact"] = float(a["financial_impact"])
                    except (ValueError, TypeError):
                        pass

            # 9. anomaly_evidence.csv
            p_data.anomaly_evidence = self._load_csv(p_dir / "anomaly_evidence.csv")
            for ev in p_data.anomaly_evidence:
                for float_field in ["gross_amount", "expected_value", "actual_value", "difference"]:
                    if float_field in ev:
                        try:
                            ev[float_field] = float(ev[float_field])
                        except (ValueError, TypeError):
                            pass

            # 10. recovery_requests.csv
            p_data.recovery_requests = self._load_csv(p_dir / "recovery_requests.csv")
            for req in p_data.recovery_requests:
                for float_field in ["amount_requested", "amount_recovered"]:
                    if float_field in req:
                        try:
                            req[float_field] = float(req[float_field])
                        except (ValueError, TypeError):
                            pass

            # 11. summary.csv
            p_data.summary = self._load_csv(p_dir / "summary.csv")

            self._periods[p_key] = p_data

        self._is_loaded = True
        logger.info(
            f"Successfully loaded all {len(self._periods)} half-year periods: {', '.join(self._periods.keys())}"
        )

    def _load_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        with file_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------

    def get_period_data(self, period: Optional[str] = None, year: Optional[int] = None) -> PeriodData:
        self.load_dataset()
        key = self.normalize_period_key(period, year)
        return self._periods[key]

    def get_all_period_keys(self) -> List[str]:
        self.load_dataset()
        return PERIOD_KEYS

    def get_merchant_info(self, period: Optional[str] = None) -> Dict[str, Any]:
        p = self.get_period_data(period)
        meta = p.meta
        fee_rate = 0.018
        if p.fee_contracts:
            try:
                fee_rate = float(p.fee_contracts[0].get("contracted_rate", 0.018))
            except (ValueError, TypeError):
                fee_rate = 0.018

        return {
            "merchant_name": meta.get("merchant_name", "Zenzo Commerce"),
            "merchant_id": meta.get("merchant_id", "mid_demo_ZC771042"),
            "currency": meta.get("currency", "INR"),
            "payment_provider": meta.get("payment_provider", "Razorpay"),
            "dataset_period": {
                "start": meta.get("period_start", "2024-01-01"),
                "end": meta.get("period_end", "2026-12-31"),
                "years": [2024, 2025, 2026],
            },
            "contract": {
                "fee_rate": fee_rate,
                "effective_from": meta.get("period_start", "2024-01-01"),
                "effective_to": meta.get("period_end", "2026-12-31"),
            },
            "demo_status": "Synthetic demo dataset" if meta.get("dataset_type") == "synthetic_demo" else "Connected",
            "notes": meta.get("note", ""),
        }

    def get_dataset_status(self, period: Optional[str] = None) -> Dict[str, Any]:
        p = self.get_period_data(period)
        confirmed_count = sum(1 for a in p.anomalies if a.get("status") == "confirmed")
        under_review_count = sum(1 for a in p.anomalies if a.get("status") == "under_review")

        return {
            "merchant_name": p.meta.get("merchant_name", "Zenzo Commerce"),
            "payment_provider": p.meta.get("payment_provider", "Razorpay"),
            "dataset_start_date": p.meta.get("period_start", "2024-01-01"),
            "dataset_end_date": p.meta.get("period_end", "2026-12-31"),
            "payment_record_count": len(p.payments),
            "refund_record_count": len(p.refunds),
            "settlement_record_count": len(p.settlements),
            "reconciliation_record_count": len(p.settlement_recon),
            "confirmed_anomaly_count": confirmed_count,
            "under_review_anomaly_count": under_review_count,
            "recovery_request_count": len(p.recovery_requests),
        }

    def get_payments(
        self,
        period: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        year: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        anomaly_type: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        p = self.get_period_data(period, year)
        filtered = p.payments

        if year is not None:
            filtered = [item for item in filtered if item.get("created_year") == year]
        if start_date is not None:
            filtered = [item for item in filtered if (item.get("created_date") or "") >= start_date]
        if end_date is not None:
            filtered = [item for item in filtered if (item.get("created_date") or "") <= end_date]
        if anomaly_type is not None:
            filtered = [item for item in filtered if item.get("anomaly_type") == anomaly_type]

        total = len(filtered)
        start_idx = max(0, (page - 1) * page_size)
        end_idx = start_idx + page_size
        return filtered[start_idx:end_idx], total

    def get_refunds(
        self,
        period: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        year: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        anomaly_type: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        p = self.get_period_data(period, year)
        filtered = p.refunds

        if year is not None:
            filtered = [item for item in filtered if item.get("created_year") == year]
        if start_date is not None:
            filtered = [item for item in filtered if (item.get("created_date") or "") >= start_date]
        if end_date is not None:
            filtered = [item for item in filtered if (item.get("created_date") or "") <= end_date]
        if anomaly_type is not None:
            filtered = [item for item in filtered if item.get("anomaly_type") == anomaly_type]

        total = len(filtered)
        start_idx = max(0, (page - 1) * page_size)
        end_idx = start_idx + page_size
        return filtered[start_idx:end_idx], total

    def get_settlements(
        self,
        period: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        year: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        p = self.get_period_data(period, year)
        filtered = p.settlements

        if year is not None:
            filtered = [s for s in filtered if (s.get("settlement_date") or "")[:4] == str(year)]

        total = len(filtered)
        start_idx = max(0, (page - 1) * page_size)
        end_idx = start_idx + page_size
        return filtered[start_idx:end_idx], total

    def get_anomalies(
        self,
        period: Optional[str] = None,
        status: Optional[str] = None,
        include_evidence: bool = True,
    ) -> List[Dict[str, Any]]:
        p = self.get_period_data(period)
        result = []
        for anom in p.anomalies:
            if status is not None and anom.get("status") != status:
                continue
            item = dict(anom)
            if include_evidence:
                anom_id = anom.get("anomaly_id")
                item["evidence_logs"] = [
                    ev for ev in p.anomaly_evidence if ev.get("anomaly_id") == anom_id
                ]
            result.append(item)
        return result

    def get_anomaly_by_id(self, anomaly_id: str, period: Optional[str] = None) -> Optional[Dict[str, Any]]:
        self.load_dataset()
        # Search in given period or across all periods if not found
        periods_to_search = [self.get_period_data(period)] if period else list(self._periods.values())
        for p in periods_to_search:
            for anom in p.anomalies:
                if anom.get("anomaly_id") == anomaly_id:
                    item = dict(anom)
                    item["evidence_logs"] = [
                        ev for ev in p.anomaly_evidence if ev.get("anomaly_id") == anomaly_id
                    ]
                    return item
        return None

    def get_recovery_requests(
        self,
        period: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        p = self.get_period_data(period)
        if status is not None:
            return [r for r in p.recovery_requests if r.get("status") == status]
        return p.recovery_requests

    def get_monthly_summary(self, period: Optional[str] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
        p = self.get_period_data(period, year)
        return p.summary

    def get_fee_contracts(self, period: Optional[str] = None) -> List[Dict[str, Any]]:
        p = self.get_period_data(period)
        return p.fee_contracts


# Singleton instance
data_loader = DataLoader()
