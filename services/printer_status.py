"""
Printer status verification rules (single place for human + agent writes).

Clocks:
  last_verified_at — successful human status/toner write, or successful agent read
  last_attempt_at  — every agent attempt (success or fail)
  last_checked     — legacy mirror of last_verified_at for older clients

Fail streak:
  Unreachable failures debounce (N consecutive) before effective status flips.
  Device-reported offline is trusted immediately.
  Any human status/toner verification resets fail_streak to 0.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import update

import models

# Pilot knobs
STALE_AFTER_DAYS = 7
FAIL_STREAK_THRESHOLD = 3
FAIL_WINDOW = timedelta(minutes=15)
LOW_TONER_THRESHOLD = 20


def _utcnow() -> datetime:
    return datetime.utcnow()


def _days_since(dt: Optional[datetime]) -> Optional[float]:
    if dt is None:
        return None
    try:
        if getattr(dt, "tzinfo", None) is not None:
            dt = dt.replace(tzinfo=None)
        return (_utcnow() - dt).total_seconds() / 86400.0
    except Exception:
        return None


def normalize_toner_status(toner_level: Optional[int], status: Optional[str] = None) -> tuple[Optional[int], Optional[str]]:
    if toner_level is not None:
        toner_level = int(toner_level)
        if toner_level < 0 or toner_level > 100:
            raise ValueError("Toner level must be between 0 and 100.")
        if toner_level <= LOW_TONER_THRESHOLD:
            return toner_level, "low"
        if status in (None, "unknown", "low"):
            return toner_level, "online"
        return toner_level, status
    return None, status


def apply_human_status(
    db: Session,
    printer: models.Printer,
    *,
    status: Optional[str] = None,
    toner_level: Optional[int] = ...,  # Ellipsis = omitted
) -> models.Printer:
    """
    Human verification write. Presence of status and/or toner_level (including
    same values) counts as verification — not value-diff.
    Resets fail_streak so agent noise cannot immediately undo a human check.
    Does not run for metadata-only updates (caller must not invoke this).
    """
    if status is None and toner_level is ...:
        return printer

    now = _utcnow()
    if toner_level is not ...:
        tl, st = normalize_toner_status(
            toner_level if toner_level is not None else None,
            status if status is not None else printer.status,
        )
        if toner_level is not None:
            printer.toner_level = tl
            printer.status = st or printer.status
        elif status is not None:
            printer.status = status
    elif status is not None:
        printer.status = status

    printer.last_verified_at = now
    printer.last_checked = now  # legacy mirror
    printer.fail_streak = 0
    # Human verification fully supersedes agent-side detail (e.g. leftover unreachable)
    printer.status_detail = None

    db.add(printer)
    db.commit()
    db.refresh(printer)
    return printer


ALLOWED_STATUS_DETAILS = frozenset({
    "unreachable",
    "device_reported",
    "probe_skipped_cloud_disabled",
})


def apply_agent_result(
    db: Session,
    printer: models.Printer,
    *,
    ok: bool,
    status: Optional[str] = None,
    toner_level: Optional[int] = None,
    status_detail: Optional[str] = None,
) -> models.Printer:
    """
    Agent probe result.

    - ok=True + status_detail=device_reported: reachable, device says offline (immediate)
    - ok=True otherwise: successful read; clear streak; touch both clocks
    - ok=False: unreachable path; atomic streak++; flip display after N or fail-window

    status_detail must be one of ALLOWED_STATUS_DETAILS or None (validated at API boundary).
    """
    now = _utcnow()
    printer.last_attempt_at = now

    if ok and status_detail == "device_reported":
        printer.status = status or "offline"
        printer.status_detail = "device_reported"
        printer.fail_streak = 0
        printer.last_verified_at = now
        printer.last_checked = now
        db.add(printer)
        db.commit()
        db.refresh(printer)
        return printer

    if ok:
        if toner_level is not None or status is not None:
            tl, st = normalize_toner_status(toner_level, status)
            if toner_level is not None:
                printer.toner_level = tl
            if st:
                printer.status = st
            elif status:
                printer.status = status
        printer.status_detail = status_detail
        printer.fail_streak = 0
        printer.last_verified_at = now
        printer.last_checked = now
        db.add(printer)
        db.commit()
        db.refresh(printer)
        return printer

    # Unreachable / transport failure — debounce
    # Atomic increment to avoid lost updates under concurrent agent posts
    db.execute(
        update(models.Printer)
        .where(models.Printer.id == printer.id)
        .values(fail_streak=models.Printer.fail_streak + 1, last_attempt_at=now)
    )
    db.commit()
    db.refresh(printer)

    streak = int(printer.fail_streak or 0)
    verified = printer.last_verified_at
    window_exceeded = False
    if verified is not None:
        v = verified.replace(tzinfo=None) if getattr(verified, "tzinfo", None) else verified
        window_exceeded = (now - v) > FAIL_WINDOW
    else:
        # Never verified: still require N failures before calling it unreachable on board
        window_exceeded = False

    if streak >= FAIL_STREAK_THRESHOLD or window_exceeded:
        printer.status = "unknown"
        printer.status_detail = status_detail or "unreachable"
        # Do NOT touch last_verified_at — reading is not verified
        db.add(printer)
        db.commit()
        db.refresh(printer)

    return printer


def effective_status(printer: models.Printer) -> str:
    """Fail-closed display status: stale wins over old low/ok."""
    days = _days_since(getattr(printer, "last_verified_at", None) or printer.last_checked)
    if days is not None and days > STALE_AFTER_DAYS:
        return "unknown"

    detail = getattr(printer, "status_detail", None) or ""
    raw = (printer.status or "unknown").lower()

    if detail == "unreachable" and (printer.fail_streak or 0) >= FAIL_STREAK_THRESHOLD:
        return "unknown"

    toner = printer.toner_level
    if toner is not None and toner <= LOW_TONER_THRESHOLD and days is not None and days <= STALE_AFTER_DAYS:
        return "low"

    if raw in {"low", "offline", "online", "unknown", "ok"}:
        return "online" if raw == "ok" else raw
    return "unknown"


def serialize_status_fields(printer: models.Printer) -> dict:
    verified = getattr(printer, "last_verified_at", None) or printer.last_checked
    attempt = getattr(printer, "last_attempt_at", None)
    days = _days_since(verified)
    stale = bool(days is not None and days > STALE_AFTER_DAYS)
    eff = effective_status(printer)

    detail = getattr(printer, "status_detail", None)
    age_note = None
    if verified is None and printer.toner_level is None and (printer.status or "unknown") == "unknown":
        age_note = "Never verified"
    elif stale and printer.toner_level is not None:
        age_note = f"Unknown — last reported {printer.toner_level}%, {int(days)} days ago"
    elif stale:
        age_note = f"Unknown — last verified {int(days)} days ago"

    return {
        "status": eff,
        "status_raw": printer.status or "unknown",
        "status_detail": detail,
        "toner_level": printer.toner_level,
        "last_checked": verified.isoformat() if verified is not None and hasattr(verified, "isoformat") else None,
        "last_verified_at": verified.isoformat() if verified is not None and hasattr(verified, "isoformat") else None,
        "last_attempt_at": attempt.isoformat() if attempt is not None and hasattr(attempt, "isoformat") else None,
        "days_since_update": None if days is None else round(days, 1),
        "stale": stale,
        "fail_streak": int(getattr(printer, "fail_streak", 0) or 0),
        "status_note": age_note,
    }
