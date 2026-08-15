"""Read/write the small key/value settings table (GitHub/LeetCode usernames)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Setting


def read_settings(db: Session) -> dict:
    rows = db.execute(select(Setting)).scalars().all()
    values = {s.key: s.value for s in rows}
    return {
        "github_username": values.get("github_username") or None,
        "leetcode_username": values.get("leetcode_username") or None,
    }


def write_settings(db: Session, fields: dict) -> dict:
    """Upsert non-empty values; delete keys whose value is blank."""
    for key, value in fields.items():
        value = (value or "").strip()
        existing = db.get(Setting, key)
        if value:
            if existing:
                existing.value = value
            else:
                db.add(Setting(key=key, value=value))
        elif existing:
            db.delete(existing)
    db.flush()
    return read_settings(db)
