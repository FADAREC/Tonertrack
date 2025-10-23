from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from schemas import ScanRequest, PrinterCreate, PrinterUpdate, PrinterResponse, PrinterList
from database import get_db
from auth import get_current_user
from utils import scan_network, is_printer_via_snmp, get_printer_status
from crud import create_printer, get_printers, get_printer, update_printer, delete_printer
import logging
import ipaddress

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/printers", tags=["printers"])

@router.post("/", response_model=PrinterResponse)
def add_printer(printer: PrinterCreate, db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    created = create_printer(db, printer)
    # Fetch initial status
    try:
        toner_levels, errors = get_printer_status(created.ip_address, created.connection_mode, created.snmp_community)
        updates = {
            "toner_level": toner_levels['black'] if toner_levels else 0,
            "status": "online" if toner_levels else "offline",
            "last_checked": datetime.now().isoformat(),
            "page_count": 0  # Stub
        }
        update_printer(db, created, updates)
    except:
        logger.warning(f"Initial status failed for {created.ip_address}")
    return created

@router.get("/", response_model=PrinterList)
def list_printers(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    printers = get_printers(db, skip=skip, limit=limit)
    return {"printers": printers}

@router.get("/{printer_id}", response_model=PrinterResponse)
def get_printer_details(printer_id: int, db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    printer = get_printer(db, printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    try:
        toner_levels, errors = get_printer_status(printer.ip_address, printer.connection_mode, printer.snmp_community)
        updates = {
            "toner_level": toner_levels['black'] if toner_levels else 0,
            "status": "online" if toner_levels else "offline",
            "last_checked": datetime.now().isoformat()
        }
        update_printer(db, printer, updates)
    except:
        pass
    return printer

@router.patch("/{printer_id}", response_model=PrinterResponse)
def update_printer_endpoint(printer_id: int, updates: PrinterUpdate, db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    printer = get_printer(db, printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    updated = update_printer(db, printer, updates.dict(exclude_unset=True))
    return updated

@router.delete("/{printer_id}")
def delete_printer_endpoint(printer_id: int, db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    deleted = delete_printer(db, printer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Printer not found")
    return {"detail": "Printer deleted"}

@router.post("/scan")
async def scan(subnet: ScanRequest, db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    try:
        devices = await scan_network(subnet.subnet)
        discovered = []
        for device in devices:
            existing = db.query(models.Printer).filter(models.Printer.ip_address == device['ip']).first()
            if existing:
                continue
            model = await is_printer_via_snmp(device['ip'])
            if model:
                printer = PrinterCreate(name=model, ip_address=device['ip'], connection_mode="snmp" if 161 in device['ports'] else "web")
                created = create_printer(db, printer)
                discovered.append(created)
        return {"discovered": len(discovered), "printers": discovered}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))