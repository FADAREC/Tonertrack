"""Postgres workspace RLS context for defense in depth.

Application code still filters by workspace_id. Session settings drive
FORCE ROW LEVEL SECURITY policies so cross-tenant rows stay hidden even
if a query forgets a filter.
"""
from __future__ import annotations

from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text


def set_workspace_context(db: Session, workspace_id: int | None) -> None:
    """Bind this DB session to one workspace for RLS policies."""
    if workspace_id is None:
        db.execute(text("SELECT set_config('app.workspace_id', '', true)"))
        return
    db.execute(
        text("SELECT set_config('app.workspace_id', :ws, true)"),
        {"ws": str(int(workspace_id))},
    )


def clear_workspace_context(db: Session) -> None:
    db.execute(text("SELECT set_config('app.workspace_id', '', true)"))


@contextmanager
def rls_bypass(db: Session):
    """Temporarily allow cross-workspace reads/writes (auth lookup, signup)."""
    db.execute(text("SELECT set_config('app.rls_bypass', '1', true)"))
    try:
        yield
    finally:
        db.execute(text("SELECT set_config('app.rls_bypass', '', true)"))
