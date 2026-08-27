from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from schemas import PrinterCreate, PrinterUpdate, PrinterResponse, PrinterList, ScanRequest
from database import get_db
from auth import get_current_user, UserInDB
from crud import create_printer, get_printers, get_printer, update_printer, delete_printer
from services.printer_status import (
    apply_human_status,
    serialize_status_fields,
    STALE_AFTER_DAYS,
)
import models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/printers", tags=["printers"])


# Pilot policy: free tier hard cap
FREE_PRINTER_CAP = 40  # one office floor; Goal 1 coverage


def _serialize(p: models.Printer) -> dict:
    base = {
        "id": p.id,
        "name": p.name,
        "ip_address": p.ip_address,
        "location": p.location or "",
        "page_count": p.page_count or 0,
        "connection_mode": p.connection_mode or "manual",
        "department": p.department or "",
        "access_type": p.access_type or "public",
        "allowed_users": p.allowed_users or [],
        "notes": getattr(p, "notes", None) or "",
    }
    base.update(serialize_status_fields(p))
    return base


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

    # Cloud must never dial customer printer IPs (private LAN is unreachable from
    # Render; public/port-forward would still violate the trust model).
    # Probing belongs on a local agent/one-shot inside the customer network.
    # Hard off — not an RFC1918 conditional.
    if mode != "manual" and created.ip_address:
        logger.warning(
            "Cloud probe disabled: skipped outbound check to %s (mode=%s). "
            "Use a local agent or one-shot reporter on the office LAN.",
            created.ip_address,
            mode,
        )
        created.status_detail = "probe_skipped_cloud_disabled"
        # Do not touch last_verified_at / fail_streak — nothing was verified or attempted on-LAN
        db.add(created)
        db.commit()
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

    status_keys = set(data.keys()) & {"status", "toner_level"}
    meta_keys = set(data.keys()) - {"status", "toner_level"}

    # Metadata only — never touches verification clocks
    if meta_keys:
        meta = {k: data[k] for k in meta_keys}
        printer = update_printer(db, printer, meta)

    # Status / toner verification — shared domain path (resets fail_streak)
    if status_keys:
        try:
            printer = apply_human_status(
                db,
                printer,
                status=data.get("status") if "status" in data else None,
                toner_level=data["toner_level"] if "toner_level" in data else ...,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return _serialize(printer)


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


@router.get("/{printer_id}/checks")
def list_status_checks(
    printer_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """Recent status checks for evidence trail (Goal 1 / Goal 2)."""
    printer = get_printer(db, printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    limit = max(1, min(limit, 100))
    rows = (
        db.query(models.StatusCheck)
        .filter(models.StatusCheck.printer_id == printer_id)
        .order_by(models.StatusCheck.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "checks": [
            {
                "id": r.id,
                "source": r.source,
                "ok": r.ok,
                "status": r.status,
                "toner_level": r.toner_level,
                "status_detail": r.status_detail,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }
