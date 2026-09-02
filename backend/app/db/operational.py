"""SQLite store for sessions, recovery overlays, settings, tickets, and audit runs."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.security import hash_password, hash_token, verify_password
from app.models.domain import RecoveryRequest

_lock = threading.Lock()
_initialized = False

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    merchant_id TEXT PRIMARY KEY,
    merchant_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (merchant_id) REFERENCES users(merchant_id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_merchant ON sessions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

CREATE TABLE IF NOT EXISTS recovery_requests (
    request_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    period_key TEXT NOT NULL,
    finding_id TEXT NOT NULL,
    created_date TEXT NOT NULL,
    resolved_date TEXT,
    status TEXT NOT NULL,
    amount_requested_paise INTEGER NOT NULL,
    amount_recovered_paise INTEGER NOT NULL DEFAULT 0,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    summary TEXT NOT NULL,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    idempotency_key TEXT,
    UNIQUE (merchant_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_recovery_merchant_period ON recovery_requests(merchant_id, period_key);

CREATE TABLE IF NOT EXISTS merchant_settings (
    merchant_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_runs (
    run_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    period_key TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    finding_count INTEGER NOT NULL
);
"""


def _raw_connect() -> sqlite3.Connection:
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(settings.sqlite_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _connect() -> sqlite3.Connection:
    if not _initialized:
        initialize()
    return _raw_connect()


def initialize() -> None:
    global _initialized
    with _lock:
        if _initialized:
            return
        conn = _raw_connect()
        try:
            conn.executescript(SCHEMA)
            now = datetime.now(timezone.utc).isoformat()
            row = conn.execute(
                "SELECT merchant_id FROM users WHERE merchant_id = ?",
                (settings.demo_merchant_id,),
            ).fetchone()
            if not row:
                conn.execute(
                    "INSERT INTO users (merchant_id, merchant_name, password_hash, created_at) VALUES (?, ?, ?, ?)",
                    (
                        settings.demo_merchant_id,
                        settings.demo_merchant_name,
                        hash_password(settings.demo_password),
                        now,
                    ),
                )
            else:
                # Keep the demo password in sync with env for local/demo deployments.
                conn.execute(
                    "UPDATE users SET password_hash = ?, merchant_name = ? WHERE merchant_id = ?",
                    (hash_password(settings.demo_password), settings.demo_merchant_name, settings.demo_merchant_id),
                )
            conn.commit()
        finally:
            conn.close()
        _initialized = True


def authenticate(merchant_id: str, password: str) -> Optional[Dict[str, str]]:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT merchant_id, merchant_name, password_hash FROM users WHERE merchant_id = ?",
            (merchant_id,),
        ).fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            return None
        return {"merchant_id": row["merchant_id"], "merchant_name": row["merchant_name"]}
    finally:
        conn.close()


def create_session(merchant_id: str, token: str, expires_at: datetime) -> None:
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO sessions (token_hash, merchant_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (hash_token(token), merchant_id, datetime.now(timezone.utc).isoformat(), expires_at.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_session(token: str) -> Optional[Dict[str, str]]:
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT s.merchant_id, u.merchant_name, s.expires_at
            FROM sessions s
            JOIN users u ON u.merchant_id = s.merchant_id
            WHERE s.token_hash = ?
            """,
            (hash_token(token),),
        ).fetchone()
        if not row:
            return None
        expires = datetime.fromisoformat(row["expires_at"])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= datetime.now(timezone.utc):
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (hash_token(token),))
            conn.commit()
            return None
        return {"merchant_id": row["merchant_id"], "merchant_name": row["merchant_name"]}
    finally:
        conn.close()


def delete_session(token: str) -> None:
    conn = _connect()
    try:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (hash_token(token),))
        conn.commit()
    finally:
        conn.close()


def get_recovery_by_idempotency(merchant_id: str, idempotency_key: str) -> Optional[sqlite3.Row]:
    conn = _connect()
    try:
        return conn.execute(
            "SELECT * FROM recovery_requests WHERE merchant_id = ? AND idempotency_key = ?",
            (merchant_id, idempotency_key),
        ).fetchone()
    finally:
        conn.close()


def insert_recovery_request(payload: Dict[str, Any]) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO recovery_requests (
                request_id, merchant_id, period_key, finding_id, created_date, resolved_date,
                status, amount_requested_paise, amount_recovered_paise, recipient, subject,
                summary, evidence_count, idempotency_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["request_id"],
                payload["merchant_id"],
                payload["period_key"],
                payload["finding_id"],
                payload["created_date"],
                payload.get("resolved_date"),
                payload["status"],
                payload["amount_requested_paise"],
                payload.get("amount_recovered_paise", 0),
                payload["recipient"],
                payload["subject"],
                payload["summary"],
                payload.get("evidence_count", 0),
                payload.get("idempotency_key"),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise ValueError("duplicate recovery request") from exc
    finally:
        conn.close()


def list_recovery_requests(merchant_id: str, period_key: str) -> List[RecoveryRequest]:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT * FROM recovery_requests
            WHERE merchant_id = ? AND period_key = ?
            ORDER BY created_date DESC, request_id DESC
            """,
            (merchant_id, period_key),
        ).fetchall()
        results: List[RecoveryRequest] = []
        for row in rows:
            results.append(
                RecoveryRequest(
                    request_id=row["request_id"],
                    finding_id=row["finding_id"],
                    created_date=row["created_date"],
                    resolved_date=row["resolved_date"],
                    status=row["status"],
                    amount_requested_paise=int(row["amount_requested_paise"]),
                    amount_recovered_paise=int(row["amount_recovered_paise"]),
                    recipient=row["recipient"],
                    subject=row["subject"],
                    summary=row["summary"],
                    evidence_count=int(row["evidence_count"] or 0),
                )
            )
        return results
    finally:
        conn.close()


def get_settings_payload(merchant_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT payload FROM merchant_settings WHERE merchant_id = ?",
            (merchant_id,),
        ).fetchone()
        if not row:
            return None
        return json.loads(row["payload"])
    finally:
        conn.close()


def save_settings_payload(merchant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    conn = _connect()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO merchant_settings (merchant_id, payload, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(merchant_id) DO UPDATE SET payload = excluded.payload, updated_at = excluded.updated_at
            """,
            (merchant_id, json.dumps(payload), now),
        )
        conn.commit()
        return payload
    finally:
        conn.close()


def insert_support_ticket(ticket_id: str, merchant_id: str, subject: str, description: str) -> Dict[str, str]:
    conn = _connect()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO support_tickets (ticket_id, merchant_id, subject, description, created_at, status)
            VALUES (?, ?, ?, ?, ?, 'open')
            """,
            (ticket_id, merchant_id, subject, description, now),
        )
        conn.commit()
        return {"ticket_id": ticket_id, "status": "open", "created_at": now}
    finally:
        conn.close()


def insert_audit_run(run_id: str, merchant_id: str, period_key: str, finding_count: int) -> Dict[str, Any]:
    conn = _connect()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO audit_runs (run_id, merchant_id, period_key, started_at, completed_at, finding_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, merchant_id, period_key, now, now, finding_count),
        )
        conn.commit()
        return {"run_id": run_id, "period": period_key, "completed_at": now, "finding_count": finding_count}
    finally:
        conn.close()
