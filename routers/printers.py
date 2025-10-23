from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from schemas import ScanRequest, PrinterCreate, PrinterUpdate, PrinterResponse, PrinterList
from database import get_db
from auth import get_current_user, UserInDB
from utils import scan_network, is_printer_via_snmp, get_printer_status
from crud import create_printer, get_printers, get_printer, update_printer, delete_printer
import logging
import ipaddress
from datetime import datetime
import models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/printers", tags=["printers"])

@router.post("/", response_model=PrinterResponse)
def add_printer(
    printer: PrinterCreate,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    created = create_printer(db, printer)
    # Fetch initial status
    try:
        toner_levels, errors = get_printer_status(
            created.ip_address,
            created.connection_mode,
            created.snmp_community
        )
        updates = {
            "toner_level": toner_levels.get("black", 0) if toner_levels else 0,
            "status": "online" if toner_levels else "offline",
            "last_checked": datetime.now().isoformat(),
            "page_count": 0  # Placeholder
        }
        update_printer(db, created, updates)
    except Exception as e:
        logger.warning(f"Initial status failed for {created.ip_address}: {e}")
    return created

@router.get("/{printer_id}", response_model=PrinterResponse)
def get_printer_details(
    printer_id: int,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    printer = get_printer(db, printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    try:
        toner_levels, errors = get_printer_status(
            printer.ip_address,
            printer.connection_mode,
            printer.snmp_community
        )
        updates = {
            "toner_level": toner_levels.get("black", 0) if toner_levels else 0,
            "status": "online" if toner_levels else "offline",
            "last_checked": datetime.now().isoformat()
        }
        update_printer(db, printer, updates)
    except Exception as e:
        logger.warning(f"Status check failed for {printer.ip_address}: {e}")
    return printer

@router.patch("/{printer_id}", response_model=PrinterResponse)
def update_printer_endpoint(
    printer_id: int,
    updates: PrinterUpdate,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    printer = get_printer(db, printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    updated = update_printer(db, printer, updates.dict(exclude_unset=True))
    return updated

@router.delete("/{printer_id}")
def delete_printer_endpoint(
    printer_id: int,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    deleted = delete_printer(db, printer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Printer not found")
    return {"detail": "Printer deleted"}

@router.post("/scan")
async def scan(
    subnet: ScanRequest,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    try:
        # Validate subnet
        ipaddress.IPv4Network(subnet.subnet, strict=False)
        devices = await scan_network(subnet.subnet)
        discovered = []

        for device in devices:
            existing = db.query(models.Printer).filter(models.Printer.ip_address == device["ip"]).first()
            if existing:
                continue

            model = await is_printer_via_snmp(device["ip"])
            if model:
                printer = PrinterCreate(
                    name=model,
                    ip_address=device["ip"],
                    connection_mode="snmp" if 161 in device["ports"] else "web"
                )
                created = create_printer(db, printer)
                discovered.append(created)

        return {"discovered": len(discovered), "printers": discovered}

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))