from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime


class UserLogin(BaseModel):
    login: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserResponse(BaseModel):
    username: str
    email: str
    role: str = "operator"
    workspace_id: int | None = None

    class Config:
        from_attributes = True


class ScanRequest(BaseModel):
    subnet: str


class PrinterCreate(BaseModel):
    name: str
    ip_address: Optional[str] = None
    location: Optional[str] = ""
    connection_mode: str = "manual"  # snmp | web | ping | manual | local
    local_name: Optional[str] = None  # Windows printer name when mode=local
    snmp_community: str = "public"
    department: Optional[str] = ""
    access_type: str = "public"
    allowed_users: List[str] = Field(default_factory=list)
    toner_level: Optional[int] = None  # for manual mode
    notes: Optional[str] = ""


class PrinterUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    access_type: Optional[str] = None
    allowed_users: Optional[List[str]] = None
    toner_level: Optional[int] = None
    status: Optional[str] = None
    connection_mode: Optional[str] = None
    local_name: Optional[str] = None
    notes: Optional[str] = None
    ip_address: Optional[str] = None


class PrinterResponse(BaseModel):
    id: int
    name: str
    ip_address: Optional[str] = None
    location: Optional[str] = ""
    status: str = "unknown"
    status_raw: Optional[str] = None
    status_detail: Optional[str] = None
    status_note: Optional[str] = None
    toner_level: Optional[int] = None
    page_count: int = 0
    last_checked: Optional[str] = None
    last_verified_at: Optional[str] = None
    last_attempt_at: Optional[str] = None
    days_since_update: Optional[float] = None
    seconds_since_verified: Optional[int] = None
    stale: bool = False
    fail_streak: int = 0
    connection_mode: str = "manual"
    local_name: Optional[str] = None
    department: Optional[str] = ""
    access_type: str = "public"
    allowed_users: List[str] = Field(default_factory=list)
    notes: Optional[str] = ""

    class Config:
        from_attributes = True


class PrinterList(BaseModel):
    printers: List[PrinterResponse]


class TrustInfo(BaseModel):
    """What we access / never access - shown before any network path."""
    title: str
    what_we_access: List[str]
    what_we_never_access: List[str]
    what_leaves_network: List[str]
    kill_switch: str
    modes: List[dict]


class TrustChoice(BaseModel):
    mode: str  # manual_only | agent_accepted


class TrustStatus(BaseModel):
    mode: str
    accepted_at: Optional[str] = None


class JobCreate(BaseModel):
    printer_id: int
    user: str
    document: str
    pages: int
    cost: float = 0.0
    status: str = "pending"


class AlertCreate(BaseModel):
    printer_id: int
    message: str


class SettingUpdate(BaseModel):
    check_interval: Optional[int] = None
    low_toner_threshold: int = 20


StatusDetailValue = Literal[
    "unreachable",
    "device_reported",
    "probe_skipped_cloud_disabled",
]


class AgentReportRequest(BaseModel):
    """Narrow write surface for agent tokens - status verification only.

    Unknown status_detail values are rejected (422), not ignored.
    """
    printer_id: int
    ok: bool
    status: Optional[str] = None
    toner_level: Optional[int] = None
    status_detail: Optional[StatusDetailValue] = None


class AgentTokenCreate(BaseModel):
    name: str = "default"


class AgentTokenPublic(BaseModel):
    id: int
    name: str
    token_prefix: str
    created_by: str
    created_at: Optional[str] = None
    last_used_at: Optional[str] = None
    revoked_at: Optional[str] = None
    helper_download_enabled: bool = False

    class Config:
        from_attributes = True


class AgentTokenCreated(BaseModel):
    """Returned only at creation - includes raw token once."""
    token: AgentTokenPublic
    raw_token: str
    warning: str = "Store this token now. It will not be shown again."


class PollIntervalUpdate(BaseModel):
    poll_interval_seconds: int


class PollConfigResponse(BaseModel):
    poll_interval_seconds: int
    allowed_intervals_seconds: list[int]
    label: str


class AgentPrinterTarget(BaseModel):
    id: int
    name: str
    ip_address: Optional[str] = None
    connection_mode: str = "manual"
