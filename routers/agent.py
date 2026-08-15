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
)
from services.printer_status import apply_agent_result
from services.agent_tokens import (
    create_agent_token,
    revoke_agent_token,
    verify_agent_token,
    touch_last_used,
    list_agent_tokens,
)
from routers.printers import _serialize
import models

router = APIRouter(prefix="/agent", tags=["agent"])


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
    }


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


@router.post("/tokens", response_model=AgentTokenCreated)
def issue_token(
    body: AgentTokenCreate,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    _require_admin(current_user)
    row, raw = create_agent_token(db, created_by=current_user.username, name=body.name)
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
    return [_public_token(r) for r in list_agent_tokens(db)]


@router.post("/tokens/{token_id}/revoke", response_model=AgentTokenPublic)
def revoke_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    _require_admin(current_user)
    row = revoke_agent_token(db, token_id, revoked_by=current_user.username)
    if not row:
        raise HTTPException(status_code=404, detail="Token not found")
    return _public_token(row)


@router.post("/report")
def agent_report(
    body: AgentReportRequest,
    db: Session = Depends(get_db),
    agent: models.AgentToken = Depends(get_agent_from_header),
):
    """
    Local agent/one-shot posts status. Auth checked on this request only.
    Narrow body — no fleet metadata writes.
    """
    printer = get_printer(db, body.printer_id)
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
        device_reported_offline=body.device_reported_offline,
    )
    touch_last_used(db, agent)
    return _serialize(updated)
