"""Workspace-scoped settings (poll interval, etc.)."""
from __future__ import annotations

from sqlalchemy.orm import Session

import models
from crud import get_setting, set_setting

ALLOWED_POLL_INTERVALS = frozenset(
    {
        120,  # 2 min
        300,
        900,
        1800,
        3600,
        21600,
        86400,
    }
)
DEFAULT_POLL_SECONDS = 900
POLL_KEY = "poll_interval_seconds"


def get_poll_interval_seconds(db: Session, workspace_id: int | None = None) -> int:
    if workspace_id is None:
        return DEFAULT_POLL_SECONDS
    row = get_setting(db, POLL_KEY, workspace_id=workspace_id)
    if not row or not row.value:
        return DEFAULT_POLL_SECONDS
    try:
        n = int(row.value)
        if n in ALLOWED_POLL_INTERVALS:
            return n
    except ValueError:
        pass
    return DEFAULT_POLL_SECONDS


def set_poll_interval_seconds(db: Session, seconds: int, workspace_id: int | None = None) -> int:
    if workspace_id is None:
        raise ValueError("workspace_id is required")
    seconds = int(seconds)
    if seconds not in ALLOWED_POLL_INTERVALS:
        raise ValueError(
            f"poll_interval_seconds must be one of {sorted(ALLOWED_POLL_INTERVALS)}"
        )
    set_setting(db, POLL_KEY, str(seconds), workspace_id=workspace_id)
    return seconds
