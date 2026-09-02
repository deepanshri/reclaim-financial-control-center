import os
import tempfile
import uuid
from pathlib import Path

os.environ.setdefault("RECLAIM_ENV", "test")
os.environ.setdefault("RECLAIM_DEMO_PASSWORD", "ReclaimDemo!2026")
os.environ.setdefault("RECLAIM_RATE_LIMIT_PER_MINUTE", "10000")
os.environ.setdefault("RECLAIM_LOGIN_RATE_LIMIT_PER_MINUTE", "10000")
os.environ.setdefault("RECLAIM_ENABLE_DOCS", "true")
os.environ.setdefault("RECLAIM_COOKIE_SECURE", "false")
os.environ["RECLAIM_SQLITE_PATH"] = str(
    Path(tempfile.gettempdir()) / f"reclaim-test-{uuid.uuid4().hex}.sqlite"
)
