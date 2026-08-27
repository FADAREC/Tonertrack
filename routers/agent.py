"""Agent report API — opaque token auth checked on every request."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, UserInDB
from crud import get_printer
from schemas import (
    AgentReportRequest,
    AgentTokenCreate,
    AgentTokenPublic,
    AgentTokenCreated,
    PollIntervalUpdate,
    PollConfigResponse,
)
from services.printer_status import apply_agent_result
from services.agent_tokens import (
    create_agent_token,
    revoke_agent_token,
    verify_agent_token,
    touch_last_used,
    list_agent_tokens,
)
from services.settings_service import (
    get_poll_interval_seconds,
    set_poll_interval_seconds,
    ALLOWED_POLL_INTERVALS,
)
from crud import get_printers
from fastapi.responses import FileResponse, PlainTextResponse, Response, PlainTextResponse, Response
import os
from pathlib import Path as FsPath
from routers.printers import _serialize
import models

router = APIRouter(prefix="/agent", tags=["agent"])  # Office helper


def _require_admin(user: UserInDB) -> None:
    if getattr(user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin only")


def _iso(dt) -> Optional[str]:
    if dt is None:
        return None
    return dt.isoformat() if hasattr(dt, "isoformat") else str(dt)


def _public_token(row: models.AgentToken) -> dict:
    return {
        "id": row.id,
        "name": row.name or "default",
        "token_prefix": row.token_prefix,
        "created_by": row.created_by,
        "created_at": _iso(row.created_at),
        "last_used_at": _iso(row.last_used_at),
        "revoked_at": _iso(row.revoked_at),
        "helper_download_enabled": bool(getattr(row, "helper_download_enabled", False)),
    }


def _interval_label(seconds: int) -> str:
    if seconds < 3600:
        return f"{seconds // 60} minutes"
    if seconds < 86400:
        return f"{seconds // 3600} hour(s)"
    return f"{seconds // 86400} day(s)"


def get_agent_from_header(
    authorization: Optional[str] = Header(None),
    x_agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
    db: Session = Depends(get_db),
) -> models.AgentToken:
    """
    Auth on every report. Prefer Authorization: Bearer <token> or X-Agent-Token.
    Never caches across requests.
    """
    raw = None
    if x_agent_token:
        raw = x_agent_token.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        raw = authorization[7:].strip()
    if not raw:
        raise HTTPException(status_code=401, detail="Agent token required")
    row = verify_agent_token(db, raw)
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or revoked agent token")
    return row


@router.post("/tokens", response_model=AgentTokenCreated, summary="Create an office helper access key")
def issue_token(
    body: AgentTokenCreate,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    _require_admin(current_user)
    ws = getattr(current_user, "workspace_id", None)
    if ws is None:
        raise HTTPException(status_code=400, detail="Account is not linked to an office yet.")
    try:
        row, raw = create_agent_token(
            db,
            created_by=current_user.username,
            name=body.name,
            workspace_id=ws,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "token": _public_token(row),
        "raw_token": raw,
        "warning": "Store this token now. It will not be shown again.",
    }


@router.get("/tokens", response_model=list[AgentTokenPublic])
def list_tokens(
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    _require_admin(current_user)
    return [
        _public_token(r)
        for r in list_agent_tokens(db, workspace_id=getattr(current_user, "workspace_id", None))
    ]


@router.post("/tokens/{token_id}/revoke", response_model=AgentTokenPublic)
def revoke_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    _require_admin(current_user)
    row = revoke_agent_token(
        db,
        token_id,
        revoked_by=current_user.username,
        workspace_id=getattr(current_user, "workspace_id", None),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Token not found")
    return _public_token(row)


@router.post("/report", summary="Send a printer status update from the office helper")
def agent_report(
    body: AgentReportRequest,
    db: Session = Depends(get_db),
    agent: models.AgentToken = Depends(get_agent_from_header),
):
    """
    Local agent/one-shot posts status. Auth checked on this request only.
    Narrow body — no fleet metadata writes.
    """
    printer = get_printer(db, body.printer_id, workspace_id=getattr(agent, "workspace_id", None))
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    if not printer.ip_address:
        raise HTTPException(status_code=400, detail="Printer has no IP on allow-list")

    updated = apply_agent_result(
        db,
        printer,
        ok=body.ok,
        status=body.status,
        toner_level=body.toner_level,
        status_detail=body.status_detail,
    )
    touch_last_used(db, agent)
    return _serialize(updated)


@router.get("/config", summary="How often the office helper should check printers")
def agent_config(
    db: Session = Depends(get_db),
    agent: models.AgentToken = Depends(get_agent_from_header),
):
    """Poll frequency the local helper should use."""
    seconds = get_poll_interval_seconds(db)
    touch_last_used(db, agent)
    return {
        "poll_interval_seconds": seconds,
        "allowed_intervals_seconds": sorted(ALLOWED_POLL_INTERVALS),
        "label": _interval_label(seconds),
    }


@router.get("/fleet", summary="List of printers the office helper may check")
def agent_fleet(
    db: Session = Depends(get_db),
    agent: models.AgentToken = Depends(get_agent_from_header),
):
    """Printers the helper may poll (listed devices with an IP)."""
    ws = getattr(agent, "workspace_id", None)
    rows = get_printers(db, skip=0, limit=500, workspace_id=ws)
    targets = []
    for p in rows:
        if not p.ip_address:
            continue
        targets.append({
            "id": p.id,
            "name": p.name,
            "ip_address": p.ip_address,
            "connection_mode": p.connection_mode or "manual",
        })
    touch_last_used(db, agent)
    return {"printers": targets, "count": len(targets)}


@router.get("/poll-config", response_model=PollConfigResponse, summary="See check frequency (website)")
def get_poll_config_admin(
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """Admin/operator: read poll interval for the dashboard UI."""
    seconds = get_poll_interval_seconds(db)
    return {
        "poll_interval_seconds": seconds,
        "allowed_intervals_seconds": sorted(ALLOWED_POLL_INTERVALS),
        "label": _interval_label(seconds),
    }


@router.put("/poll-config", response_model=PollConfigResponse, summary="Change how often the helper checks")
def set_poll_config_admin(
    body: PollIntervalUpdate,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """Admin: set how often the office helper should poll."""
    _require_admin(current_user)
    try:
        seconds = set_poll_interval_seconds(db, body.poll_interval_seconds)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    db.add(models.AuditEvent(
        action="poll_interval_set",
        actor=current_user.username,
        detail=f"poll_interval_seconds={seconds}",
        created_at=datetime.utcnow(),
    ))
    db.commit()
    return {
        "poll_interval_seconds": seconds,
        "allowed_intervals_seconds": sorted(ALLOWED_POLL_INTERVALS),
        "label": _interval_label(seconds),
    }


@router.post("/tokens/{token_id}/enable-helper-download", summary="Allow download of the office helper")
def enable_helper_download(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """Admin grants helper download for this token."""
    _require_admin(current_user)
    ws = getattr(current_user, "workspace_id", None)
    if ws is None:
        raise HTTPException(status_code=400, detail="Account is not linked to an office yet.")
    row = (
        db.query(models.AgentToken)
        .filter(models.AgentToken.id == token_id)
        .filter(models.AgentToken.workspace_id == ws)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Token not found")
    if row.revoked_at is not None:
        raise HTTPException(status_code=400, detail="Token is revoked")
    row.helper_download_enabled = True
    db.add(row)
    db.add(models.AuditEvent(
        action="helper_download_enabled",
        actor=current_user.username,
        detail=f"token_id={token_id} prefix={row.token_prefix}",
        created_at=datetime.utcnow(),
    ))
    db.commit()
    db.refresh(row)
    return _public_token(row)


@router.get("/helper/download", summary="Download the office helper program")
def download_helper(
    db: Session = Depends(get_db),
    agent: models.AgentToken = Depends(get_agent_from_header),
):
    """
    Locked helper download. Requires a valid agent token with
    helper_download_enabled=True. Every attempt is logged.
    """
    log = models.HelperDownloadLog(
        token_id=agent.id,
        token_prefix=agent.token_prefix,
        actor="agent_token",
        success=False,
        detail="",
        created_at=datetime.utcnow(),
    )
    if not getattr(agent, "helper_download_enabled", False):
        log.detail = "download_not_enabled"
        db.add(log)
        db.commit()
        raise HTTPException(
            status_code=403,
            detail="Helper download not enabled for this token. Ask your TonerTrack admin to grant access.",
        )
    if agent.revoked_at is not None:
        log.detail = "token_revoked"
        db.add(log)
        db.commit()
        raise HTTPException(status_code=401, detail="Token revoked")

    helper_path = FsPath(__file__).resolve().parent.parent / "scripts" / "tonertrack_helper.py"
    if not helper_path.is_file():
        log.detail = "helper_missing"
        db.add(log)
        db.commit()
        raise HTTPException(status_code=503, detail="Helper package not available on server")

    log.success = True
    log.detail = "ok"
    db.add(log)
    db.commit()
    touch_last_used(db, agent)
    return FileResponse(
        path=str(helper_path),
        filename="tonertrack_helper.py",
        media_type="text/x-python",
    )



@router.post("/quick-setup", summary="One-step office helper setup for admin")
def quick_setup_helper(
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """Create access key, enable download, return raw key once."""
    _require_admin(current_user)
    ws = getattr(current_user, "workspace_id", None)
    if ws is None:
        raise HTTPException(status_code=400, detail="Account is not linked to an office yet.")
    try:
        row, raw = create_agent_token(
            db,
            created_by=current_user.username,
            name="office-checker",
            workspace_id=ws,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    row.helper_download_enabled = True
    db.add(row)
    db.add(
        models.AuditEvent(
            action="helper_quick_setup",
            actor=current_user.username,
            detail=f"token_id={row.id} prefix={row.token_prefix}",
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    db.refresh(row)
    return {
        "token": _public_token(row),
        "raw_token": raw,
        "warning": "Save this access key. It will not be shown again.",
        "next": "Download the Windows starter, copy it to an office PC, and double-click it.",
    }


@router.get("/helper/starter.bat", summary="Windows starter that runs the office helper")
def download_windows_starter(
    db: Session = Depends(get_db),
    x_agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
    authorization: Optional[str] = Header(None),
):
    """Returns a .bat that embeds the access key and runs the helper."""
    import os

    raw = None
    if x_agent_token:
        raw = x_agent_token.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        raw = authorization[7:].strip()
    if not raw:
        raise HTTPException(status_code=401, detail="Access key required")

    agent = verify_agent_token(db, raw)
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid or revoked access key")

    log = models.HelperDownloadLog(
        token_id=agent.id,
        token_prefix=agent.token_prefix,
        actor="agent_token",
        success=False,
        detail="starter_bat",
        created_at=datetime.utcnow(),
    )
    if not getattr(agent, "helper_download_enabled", False):
        log.detail = "download_not_enabled"
        db.add(log)
        db.commit()
        raise HTTPException(status_code=403, detail="Helper download not enabled for this key.")
    if agent.revoked_at is not None:
        log.detail = "token_revoked"
        db.add(log)
        db.commit()
        raise HTTPException(status_code=401, detail="Access key revoked")

    base = (
        os.environ.get("PUBLIC_BASE_URL")
        or os.environ.get("RENDER_EXTERNAL_URL")
        or "https://tonertrack.onrender.com"
    ).rstrip("/")

    safe_raw = raw.replace("%", "%%")

    bat = (
        "@echo off\r\n"
        "setlocal\r\n"
        "title TonerTrack office checker\r\n"
        "echo.\r\n"
        "echo TonerTrack office checker\r\n"
        "echo Checks only printers on your board. Does not scan the network.\r\n"
        "echo.\r\n"
        f"set TONERTRACK_URL={base}\r\n"
        f"set TONERTRACK_AGENT_TOKEN={safe_raw}\r\n"
        "\r\n"
        "where python >nul 2>nul\r\n"
        "if errorlevel 1 (\r\n"
        "  echo Python was not found. Install Python 3 and enable Add Python to PATH.\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "\r\n"
        "echo Downloading helper...\r\n"
        "curl -sS -H \"X-Agent-Token: %TONERTRACK_AGENT_TOKEN%\" -o \"%~dp0tonertrack_helper.py\" \"%TONERTRACK_URL%/agent/helper/download\"\r\n"
        "if errorlevel 1 (\r\n"
        "  echo Download failed. Check internet and access key.\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "\r\n"
        "echo Starting checker. Leave this window open.\r\n"
        "echo.\r\n"
        "python \"%~dp0tonertrack_helper.py\"\r\n"
        "pause\r\n"
    )
    log.success = True
    log.detail = "starter_bat_ok"
    db.add(log)
    db.commit()
    touch_last_used(db, agent)
    return Response(
        content=bat,
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=Run-TonerTrack-Checker.bat"},
    )
