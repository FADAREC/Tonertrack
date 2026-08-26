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

STALE_AFTER_DAYS = 7
FAIL_STREAK_THRESHOLD = 3
FAIL_WINDOW = timedelta(minutes=15)
LOW_TONER_THRESHOLD = 20

ALLOWED_STATUS_DETAILS = frozenset({
    "unreachable",
    "device_reported",
    "probe_skipped_cloud_disabled",
})


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


def normalize_toner_status(
    toner_level: Optional[int], status: Optional[str] = None
) -> tuple[Optional[int], Optional[str]]:
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


def record_status_check(
    db: Session,
    printer_id: int,
    *,
    source: str,
    ok: bool | None = None,
    status: str | None = None,
    toner_level: int | None = None,
    status_detail: str | None = None,
) -> None:
    """Best-effort append-only trail. Never fails the parent write."""
    try:
        db.add(
            models.StatusCheck(
                printer_id=printer_id,
                source=source,
                ok=ok,
                status=status,
                toner_level=toner_level,
                status_detail=status_detail,
                created_at=_utcnow(),
            )
        )
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


def apply_human_status(
    db: Session,
    printer: models.Printer,
    *,
    status: Optional[str] = None,
    toner_level: Optional[int] = ...,  # Ellipsis = omitted
) -> models.Printer:
    """
    Human verification write. Presence of status and/or toner_level counts
    as verification. Resets fail_streak. Clears status_detail.
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
    printer.last_checked = now
    printer.fail_streak = 0
    printer.status_detail = None

    db.add(printer)
    db.commit()
    db.refresh(printer)
    record_status_check(
        db,
        printer.id,
        source="human",
        ok=True,
        status=printer.status,
        toner_level=printer.toner_level,
        status_detail=None,
    )
    return printer


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
    - ok=True + status_detail=device_reported: immediate offline trust
    - ok=True otherwise: successful read
    - ok=False: unreachable; debounce before display flip
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
        record_status_check(
            db,
            printer.id,
            source="agent",
            ok=True,
            status=printer.status,
            toner_level=printer.toner_level,
            status_detail="device_reported",
        )
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
        record_status_check(
            db,
            printer.id,
            source="agent",
            ok=True,
            status=printer.status,
            toner_level=printer.toner_level,
            status_detail=status_detail,
        )
        return printer

    # Unreachable — atomic streak increment
    db.execute(
        update(models.Printer)
        .where(models.Printer.id == printer.id)
        .values(fail_streak=models.Printer.fail_streak + 1, last_attempt_at=now)
    )
    db.commit()
    db.refresh(printer)

    streak = int(printer.fail_streak or 0)
    verified = printer.last_verified_at
    in_window = False
    if verified is not None:
        try:
            v = verified.replace(tzinfo=None) if getattr(verified, "tzinfo", None) else verified
            in_window = (_utcnow() - v) <= FAIL_WINDOW
        except Exception:
            in_window = False

    if streak >= FAIL_STREAK_THRESHOLD or not in_window:
        printer.status = "unknown"
        printer.status_detail = status_detail or "unreachable"
        db.add(printer)
        db.commit()
        db.refresh(printer)

    record_status_check(
        db,
        printer.id,
        source="agent",
        ok=False,
        status=printer.status,
        toner_level=printer.toner_level,
        status_detail=status_detail or "unreachable",
    )
    return printer


def effective_status(printer: models.Printer) -> str:
    verified = getattr(printer, "last_verified_at", None) or printer.last_checked
    days = _days_since(verified)
    if days is not None and days > STALE_AFTER_DAYS:
        return "unknown"

    detail = getattr(printer, "status_detail", None) or ""
    raw = (printer.status or "unknown").lower()

    if detail == "unreachable" and (printer.fail_streak or 0) >= FAIL_STREAK_THRESHOLD:
        return "unknown"

    if printer.toner_level is not None and printer.toner_level <= LOW_TONER_THRESHOLD:
        if days is None or days <= STALE_AFTER_DAYS:
            return "low"

    if raw in {"low", "offline", "online", "unknown", "ok"}:
        return "online" if raw == "ok" else raw
    return "unknown"


def _human_age(dt) -> str | None:
    if dt is None:
        return None
    days = _days_since(dt)
    if days is None:
        return None
    secs = days * 86400
    if secs < 60:
        return f"{int(max(secs, 0))}s ago"
    if secs < 3600:
        return f"{int(secs // 60)} min ago"
    if secs < 86400:
        h = int(secs // 3600)
        return f"{h} hour{'s' if h != 1 else ''} ago"
    d = int(days)
    return f"{d} day{'s' if d != 1 else ''} ago"


def serialize_status_fields(printer: models.Printer) -> dict:
    verified = getattr(printer, "last_verified_at", None) or printer.last_checked
    attempt = getattr(printer, "last_attempt_at", None)
    days = _days_since(verified)
    stale = bool(days is not None and days > STALE_AFTER_DAYS)
    eff = effective_status(printer)

    detail = getattr(printer, "status_detail", None)
    verified_age = _human_age(verified)
    attempt_age = _human_age(attempt)

    age_note = None
    if verified is None and printer.toner_level is None and (printer.status or "unknown") == "unknown":
        age_note = "Not checked yet"
    elif stale and printer.toner_level is not None:
        age_note = f"Stale — last checked {printer.toner_level}% ({verified_age})"
    elif stale:
        age_note = f"Stale — last checked {verified_age}"
    elif verified_age:
        age_note = f"Checked {verified_age}"
        if attempt_age and attempt != verified:
            age_note += f" · last try {attempt_age}"

    return {
        "status": eff,
        "status_raw": printer.status or "unknown",
        "status_detail": detail,
        "toner_level": printer.toner_level,
        "last_checked": verified.isoformat() if verified is not None and hasattr(verified, "isoformat") else None,
        "last_verified_at": verified.isoformat() if verified is not None and hasattr(verified, "isoformat") else None,
        "last_attempt_at": attempt.isoformat() if attempt is not None and hasattr(attempt, "isoformat") else None,
        "days_since_update": None if days is None else round(days, 1),
        "seconds_since_verified": None if days is None else int(days * 86400),
        "stale": stale,
        "fail_streak": int(getattr(printer, "fail_streak", 0) or 0),
        "status_note": age_note,
    }
