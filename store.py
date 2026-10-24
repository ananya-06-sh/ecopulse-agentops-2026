"""Local SQLite decision and audit store for the synthetic demo."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "ecopulse.sqlite3"


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect(path=DB_PATH):
    db = sqlite3.connect(path, timeout=10)
    try:
        db.execute("CREATE TABLE IF NOT EXISTS decisions (id TEXT PRIMARY KEY, report TEXT NOT NULL, created_at TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, event TEXT NOT NULL, detail TEXT NOT NULL)")
        db.commit()
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save(report, order, path=DB_PATH):
    saved = {**report, "input_order": order, "created_at": now()}
    # The model's unverified prose is never part of the auditable decision record.
    saved.pop("model_draft_note", None)
    with connect(path) as db:
        db.execute("INSERT INTO decisions VALUES (?, ?, ?)", (saved["decision_id"], json.dumps(saved, ensure_ascii=False), saved["created_at"]))
        db.execute("INSERT INTO audit (at, event, detail) VALUES (?, ?, ?)",
                   (now(), "evaluation", json.dumps({"decision_id": saved["decision_id"], "order_id": order["id"], "mode": saved["mode"]})))
    return saved


def get(decision_id, path=DB_PATH):
    with connect(path) as db:
        row = db.execute("SELECT report FROM decisions WHERE id=?", (decision_id,)).fetchone()
    return json.loads(row[0]) if row else None


def decide(decision_id, approval, path=DB_PATH):
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT report FROM decisions WHERE id=?", (decision_id,)).fetchone()
        if not row:
            raise LookupError("Evaluate the current order first")
        report = json.loads(row[0])
        if report.get("approval"):
            raise ValueError("Decision already recorded")
        if approval["action"] == "approve" and not report.get("draft_po"):
            raise ValueError("No eligible draft to approve")
        report["approval"] = approval
        db.execute("UPDATE decisions SET report=? WHERE id=?", (json.dumps(report, ensure_ascii=False), decision_id))
        db.execute("INSERT INTO audit (at, event, detail) VALUES (?, ?, ?)",
                   (now(), "human_decision", json.dumps({"decision_id": decision_id, **approval}, ensure_ascii=False)))
    return approval


def audit(limit=100, path=DB_PATH):
    with connect(path) as db:
        rows = db.execute("SELECT at, event, detail FROM audit ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{"at": at, "event": event, "detail": json.loads(detail)} for at, event, detail in rows]
