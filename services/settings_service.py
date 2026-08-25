"""Deployment-level settings (pilot: single tenant)."""
from __future__ import annotations

from sqlalchemy.orm import Session
import models

# Allowed poll intervals in seconds (2 min … 24 h)
ALLOWED_POLL_INTERVALS = {
    120,       # 2 minutes
    300,       # 5 minutes
    900,       # 15 minutes
    1800,      # 30 minutes
    3600,      # 1 hour
    21600,     # 6 hours
    86400,     # 24 hours
}
DEFAULT_POLL_INTERVAL = 900  # 15 minutes
KEY_POLL = "poll_interval_seconds"


def get_setting(db: Session, key: str, default: str | None = None) -> str | None:
    row = db.query(models.Setting).filter(models.Setting.key == key).first()
    if not row or row.value is None:
        return default
    return row.value


def set_setting(db: Session, key: str, value: str) -> models.Setting:
    row = db.query(models.Setting).filter(models.Setting.key == key).first()
    if not row:
        row = models.Setting(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    db.commit()
    db.refresh(row)
    return row


def get_poll_interval_seconds(db: Session) -> int:
    raw = get_setting(db, KEY_POLL, str(DEFAULT_POLL_INTERVAL))
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_POLL_INTERVAL
    if n not in ALLOWED_POLL_INTERVALS:
        return DEFAULT_POLL_INTERVAL
    return n


def set_poll_interval_seconds(db: Session, seconds: int) -> int:
    if seconds not in ALLOWED_POLL_INTERVALS:
        raise ValueError(
            "poll_interval_seconds must be one of: "
            + ", ".join(str(x) for x in sorted(ALLOWED_POLL_INTERVALS))
        )
    set_setting(db, KEY_POLL, str(seconds))
    return seconds
