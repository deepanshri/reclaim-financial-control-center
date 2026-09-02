import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]

load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")


def _split_origins(raw: str) -> List[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    environment: str
    demo_merchant_id: str
    demo_merchant_name: str
    demo_password: str
    session_ttl_seconds: int
    cors_origins: List[str]
    cookie_secure: bool
    cookie_samesite: str
    rate_limit_per_minute: int
    login_rate_limit_per_minute: int
    enable_docs: bool
    sqlite_path: Path
    finance_email: str
    settlement_bank: str

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")


def get_settings() -> Settings:
    environment = os.getenv("RECLAIM_ENV", "development")
    default_origins = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3001,http://127.0.0.1:3001,"
        "http://localhost:3002,http://127.0.0.1:3002,"
        "http://localhost:5173,http://127.0.0.1:5173"
    )
    sqlite_raw = os.getenv("RECLAIM_SQLITE_PATH", str(BACKEND_DIR / "data" / "operational.sqlite"))
    return Settings(
        environment=environment,
        demo_merchant_id=os.getenv("RECLAIM_DEMO_MERCHANT_ID", "mid_demo_ZC771042"),
        demo_merchant_name=os.getenv("RECLAIM_DEMO_MERCHANT_NAME", "Zenzo Commerce"),
        demo_password=os.getenv("RECLAIM_DEMO_PASSWORD", "ReclaimDemo!2026"),
        session_ttl_seconds=int(os.getenv("RECLAIM_SESSION_TTL_SECONDS", "28800")),
        cors_origins=_split_origins(os.getenv("RECLAIM_CORS_ORIGINS", default_origins)),
        cookie_secure=os.getenv("RECLAIM_COOKIE_SECURE", "false").lower() == "true" or environment in ("production", "prod"),
        cookie_samesite=os.getenv("RECLAIM_COOKIE_SAMESITE", "lax"),
        rate_limit_per_minute=int(os.getenv("RECLAIM_RATE_LIMIT_PER_MINUTE", "180")),
        login_rate_limit_per_minute=int(os.getenv("RECLAIM_LOGIN_RATE_LIMIT_PER_MINUTE", "20")),
        enable_docs=os.getenv("RECLAIM_ENABLE_DOCS", "true").lower() == "true" and environment not in ("production", "prod"),
        sqlite_path=Path(sqlite_raw),
        finance_email=os.getenv("RECLAIM_FINANCE_EMAIL", "finance@zenzocommerce.in"),
        settlement_bank=os.getenv("RECLAIM_SETTLEMENT_BANK", "ICICI Bank Current Account •••• 4412"),
    )


settings = get_settings()
