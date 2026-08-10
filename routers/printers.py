from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from schemas import PrinterCreate, PrinterUpdate, PrinterResponse, PrinterList, ScanRequest
from database import get_db
from auth import get_current_user, UserInDB
from crud import create_printer, get_printers, get_printer, update_printer, delete_printer
import models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/printers", tags=["printers"])


# Pilot policy: free tier hard cap (no invites / single-user product rule is enforced in product policy)
FREE_PRINTER_CAP = 5
# After this many days without a status/toner update, effective status decays to unknown
STALE_AFTER_DAYS = 7


def _days_since(dt) -> float | None:
    if dt is None:
        return None
    try:
        if getattr(dt, "tzinfo", None) is not None:
            dt = dt.replace(tzinfo=None)
        return (datetime.utcnow() - dt).total_seconds() / 86400.0
    except Exception:
        return None


def _effective_status(p: models.Printer) -> str:
    """Apply toner + staleness so the board never shows a lying 'OK'."""
    raw = (p.status or "unknown").lower()
    toner = p.toner_level
    days = _days_since(p.last_checked)

    if days is not None and days > STALE_AFTER_DAYS:
        return "unknown"

    if toner is not None and toner <= 20:
        return "low"
    if raw in {"low", "offline", "online", "unknown", "ok"}:
        if raw == "ok":
            return "online"
        return raw
    return "unknown"


def _serialize(p: models.Printer) -> dict:
    last = p.last_checked
    days = _days_since(last)
    last_iso = last.isoformat() if last is not None and hasattr(last, "isoformat") else None
    return {
        "id": p.id,
        "name": p.name,
        "ip_address": p.ip_address,
        "location": p.location or "",
        "status": _effective_status(p),
        "status_raw": (p.status or "unknown"),
        "toner_level": p.toner_level,
        "page_count": p.page_count or 0,
        "last_checked": last_iso,
        "days_since_update": None if days is None else round(days, 1),
        "stale": bool(days is not None and days > STALE_AFTER_DAYS),
        "connection_mode": p.connection_mode or "manual",
        "department": p.department or "",
        "access_type": p.access_type or "public",
        "allowed_users": p.allowed_users or [],
        "notes": getattr(p, "notes", None) or "",
    }


@router.get("/", response_model=PrinterList)
def list_printers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    rows = get_printers(db, skip=skip, limit=limit)
    return {"printers": [_serialize(p) for p in rows]}


@router.post("/", response_model=PrinterResponse)
def add_printer(
    printer: PrinterCreate,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """Add a printer. connection_mode=manual never probes the network."""
    mode = (printer.connection_mode or "manual").lower()
    if mode not in {"manual", "snmp", "web", "ping"}:
        raise HTTPException(status_code=400, detail="connection_mode must be manual, snmp, web, or ping")

    # Free-tier hard cap (pilot). Pro flag can raise this later without changing the path.
    existing = get_printers(db, skip=0, limit=1000)
    if len(existing) >= FREE_PRINTER_CAP:
        raise HTTPException(
            status_code=403,
            detail=f"Free plan allows up to {FREE_PRINTER_CAP} printers. Upgrade to Pro for a full office fleet.",
        )

    created = create_printer(db, printer)

    # Only probe when not manual — and only the IP the user typed
    if mode != "manual" and created.ip_address:
        try:
            from utils import get_printer_status
            import asyncio

            result = asyncio.get_event_loop().run_until_complete(
                get_printer_status(created.ip_address, mode, created.snmp_community or "public")
            )
            # Best-effort parse; keep unknown on failure
            status = "online"
            toner = created.toner_level
            if isinstance(result, dict):
                status = result.get("status", "online")
                details = result.get("details") or {}
                if isinstance(details, dict) and "black" in details:
                    toner = details.get("black")
            update_printer(
                db,
                created,
                {
                    "status": status,
                    "toner_level": toner,
                    "last_checked": datetime.utcnow(),
                },
            )
        except Exception as e:
            logger.warning("Initial status failed for %s: %s", created.ip_address, e)
            update_printer(db, created, {"status": "unknown", "last_checked": datetime.utcnow()})

    db.refresh(created)
    return _serialize(created)


@router.get("/{printer_id}", response_model=PrinterResponse)
def get_printer_details(
    printer_id: int,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    printer = get_printer(db, printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return _serialize(printer)


@router.patch("/{printer_id}", response_model=PrinterResponse)
def update_printer_endpoint(
    printer_id: int,
    updates: PrinterUpdate,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    printer = get_printer(db, printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    data = updates.model_dump(exclude_unset=True) if hasattr(updates, "model_dump") else updates.dict(exclude_unset=True)
    # Any human status/toner edit is a verification event — refresh last_checked for decay logic
    if any(k in data for k in ("toner_level", "status", "name", "location", "notes", "ip_address")):
        data["last_checked"] = datetime.utcnow()
    if "toner_level" in data and data["toner_level"] is not None:
        try:
            lvl = int(data["toner_level"])
            if lvl < 0 or lvl > 100:
                raise HTTPException(status_code=400, detail="Toner level must be between 0 and 100.")
            data["toner_level"] = lvl
            if lvl <= 20:
                data["status"] = "low"
            elif data.get("status") in (None, "unknown", "low"):
                data["status"] = "online"
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Toner level must be a number from 0 to 100.")
    updated = update_printer(db, printer, data)
    return _serialize(updated)


@router.delete("/{printer_id}")
def delete_printer_endpoint(
    printer_id: int,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    if not delete_printer(db, printer_id):
        raise HTTPException(status_code=404, detail="Printer not found")
    return {"detail": "Printer deleted"}


@router.post("/scan")
async def scan(
    subnet: ScanRequest,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """Subnet scan is disabled in Step 1 trust model — refuse by default."""
    raise HTTPException(
        status_code=403,
        detail=(
            "Network-wide scan is disabled. Add printers one by one "
            "(manual, SNMP, web, or ping). An optional on-site agent "
            "will only contact IPs you list — never your whole subnet."
        ),
    )
