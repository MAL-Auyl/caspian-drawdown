"""Единственные записываемые данные проекта — гражданские заявки. SQLite."""
import hashlib
import sqlite3
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = REPO_ROOT / "backend" / "storage" / "reports.db"

CATEGORIES = {"shoreline_change", "pollution", "dust_storm", "infrastructure", "other"}
RATE_LIMIT_PER_HOUR = 5


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS citizen_reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            contact TEXT,
            nearest_transect_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            ip_hash TEXT,
            status TEXT NOT NULL DEFAULT 'pending'
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_created ON citizen_reports(created_at DESC)")
    conn.commit()
    conn.close()


def ip_hash(ip: str) -> str:
    salt = "caspian-pulse-2026"
    return hashlib.sha256((salt + ip).encode()).hexdigest()[:16]


def rate_limited(ip: str) -> bool:
    conn = _connect()
    h = ip_hash(ip)
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM citizen_reports "
        "WHERE ip_hash = ? AND created_at >= datetime('now', '-1 hour')",
        (h,),
    ).fetchone()
    conn.close()
    return row["n"] >= RATE_LIMIT_PER_HOUR


def insert_report(latitude, longitude, category, description, contact, nearest_transect_id, ip):
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO citizen_reports "
        "(latitude, longitude, category, description, contact, nearest_transect_id, ip_hash) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (latitude, longitude, category, description, contact, nearest_transect_id, ip_hash(ip)),
    )
    conn.commit()
    report_id = cur.lastrowid
    row = conn.execute("SELECT created_at FROM citizen_reports WHERE report_id = ?", (report_id,)).fetchone()
    conn.close()
    return report_id, row["created_at"]


def list_reports(limit: int = 100):
    conn = _connect()
    rows = conn.execute(
        "SELECT report_id, latitude, longitude, category, description, "
        "nearest_transect_id, created_at, status FROM citizen_reports "
        "ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
