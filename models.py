from sqlalchemy import Column, Integer, String, JSON, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.sql import func
from database import Base


class Printer(Base):
    """Fleet device row.

    PILOT: single-tenant — there is no workspace_id. All printers on this
    deployment share one global table. A second office on the same app would
    see the same fleet. Multi-tenancy is a future migration, not a missing filter.
    """
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ip_address = Column(String, index=True)
    location = Column(String, default="")
    status = Column(String, default="unknown")
    status_detail = Column(String, nullable=True)  # unreachable | device_reported | None
    toner_level = Column(Integer, nullable=True)
    page_count = Column(Integer, default=0)
    # Legacy mirror of last successful verification (kept for older rows/clients)
    last_checked = Column(DateTime, nullable=True)
    # Two-clock model
    last_verified_at = Column(DateTime, nullable=True)
    last_attempt_at = Column(DateTime, nullable=True)
    fail_streak = Column(Integer, default=0, nullable=False)
    connection_mode = Column(String, default="manual")
    snmp_community = Column(String, default="public")
    department = Column(String, default="")
    access_type = Column(String, default="public")
    allowed_users = Column(JSON, default=list)
    notes = Column(String, default="")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="operator")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    printer_id = Column(Integer, ForeignKey("printers.id"))
    user = Column(String)
    document = Column(String)
    pages = Column(Integer)
    cost = Column(Float, default=0.0)
    status = Column(String, default="pending")
    timestamp = Column(DateTime, default=func.now())


class StatusCheck(Base):
    """Append-only check trail for support evidence (Goal 1 freshness / Goal 2 bills)."""
    __tablename__ = "status_checks"

    id = Column(Integer, primary_key=True, index=True)
    printer_id = Column(Integer, ForeignKey("printers.id"), nullable=False, index=True)
    source = Column(String, default="agent")  # agent | human
    ok = Column(Boolean, nullable=True)
    status = Column(String, nullable=True)
    toner_level = Column(Integer, nullable=True)
    status_detail = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    printer_id = Column(Integer, ForeignKey("printers.id"))
    message = Column(String)
    alert_type = Column(String, default="low_toner", index=True)
    timestamp = Column(DateTime, default=func.now())
    resolved = Column(Boolean, default=False)


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True)
    value = Column(String)


class TrustPreference(Base):
    __tablename__ = "trust_preferences"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    mode = Column(String, default="manual_only")
    accepted_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AgentToken(Base):
    """Opaque API key for local agents/one-shot reporters. Hashed at rest; shown once.

    PILOT: single-tenant — token is deployment-scoped, not workspace-scoped.
    Any valid token can report against any printer_id on this instance.
    """
    __tablename__ = "agent_tokens"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="default")
    token_hash = Column(String, nullable=False, unique=True, index=True)
    token_prefix = Column(String, nullable=False)  # first 8 chars for admin UI identification
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String, nullable=True)
    # Admin must enable before helper package can be downloaded with this token
    helper_download_enabled = Column(Boolean, default=False, nullable=False)


class HelperDownloadLog(Base):
    """Track every helper download attempt (success or denied)."""
    __tablename__ = "helper_download_logs"

    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, ForeignKey("agent_tokens.id"), nullable=True)
    token_prefix = Column(String, default="")
    actor = Column(String, default="")  # username if admin-triggered, or "agent_token"
    success = Column(Boolean, default=False)
    detail = Column(String, default="")
    created_at = Column(DateTime, default=func.now())


class AuditEvent(Base):
    """Simple audit trail (token issue/revoke, trust, admin transfer, etc.)."""
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False, index=True)
    actor = Column(String, nullable=False)
    detail = Column(String, default="")
    created_at = Column(DateTime, default=func.now())


class SiteVisit(Base):
    """Lightweight page-view log for pilot traffic (not /health uptime pings)."""
    __tablename__ = "site_visits"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, default="/", index=True)
    created_at = Column(DateTime, default=func.now(), index=True)

