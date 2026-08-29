"""Opaque agent API tokens - hashed at rest, shown once, checked on every report."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

import models

TOKEN_BYTES = 32
PREFIX_LEN = 8


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_raw_token() -> str:
    # tt_ prefix makes the secret recognizable if leaked into logs by mistake
    return "tt_" + secrets.token_urlsafe(TOKEN_BYTES)


def create_agent_token(
    db: Session,
    *,
    created_by: str,
    name: str = "default",
    workspace_id: int | None = None,
) -> Tuple[models.AgentToken, str]:
    """Returns (row, raw_token). Raw is only available at this moment."""
    if workspace_id is None:
        raise ValueError("workspace_id is required to create an access key")
    raw = generate_raw_token()
    row = models.AgentToken(
        name=name or "default",
        token_hash=_hash_token(raw),
        token_prefix=raw[: PREFIX_LEN + 3],  # include tt_
        created_by=created_by,
        created_at=datetime.utcnow(),
        workspace_id=workspace_id,
    )
    db.add(row)
    db.add(
        models.AuditEvent(
            action="agent_token_created",
            actor=created_by,
            detail=f"name={row.name} prefix={row.token_prefix}",
            created_at=datetime.utcnow(),
            workspace_id=workspace_id,
        )
    )
    db.commit()
    db.refresh(row)
    return row, raw


def revoke_agent_token(
    db: Session,
    token_id: int,
    *,
    revoked_by: str,
    workspace_id: int | None = None,
) -> Optional[models.AgentToken]:
    if workspace_id is None:
        return None
    row = (
        db.query(models.AgentToken)
        .filter(models.AgentToken.id == token_id)
        .filter(models.AgentToken.workspace_id == workspace_id)
        .first()
    )
    if not row:
        return None
    if row.revoked_at is not None:
        return row
    row.revoked_at = datetime.utcnow()
    row.revoked_by = revoked_by
    db.add(row)
    db.add(
        models.AuditEvent(
            action="agent_token_revoked",
            actor=revoked_by,
            detail=f"id={row.id} prefix={row.token_prefix}",
            created_at=datetime.utcnow(),
            workspace_id=row.workspace_id,
        )
    )
    db.commit()
    db.refresh(row)
    return row


def verify_agent_token(db: Session, raw: str) -> Optional[models.AgentToken]:
    """
    Lookup by hash. Returns None if missing or revoked.
    Auth is evaluated on every call - never cache across requests/connections.
    """
    if not raw or not raw.startswith("tt_"):
        return None
    h = _hash_token(raw)
    row = db.query(models.AgentToken).filter(models.AgentToken.token_hash == h).first()
    if not row or row.revoked_at is not None:
        return None
    return row


def touch_last_used(db: Session, token: models.AgentToken) -> None:
    token.last_used_at = datetime.utcnow()
    db.add(token)
    db.commit()


def list_agent_tokens(db: Session, workspace_id: int | None = None):
    # Fail closed: no workspace => no keys (never list the whole table)
    if workspace_id is None:
        return []
    return (
        db.query(models.AgentToken)
        .filter(models.AgentToken.workspace_id == workspace_id)
        .order_by(models.AgentToken.created_at.desc())
        .all()
    )
