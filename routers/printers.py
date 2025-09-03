from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import ScanRequest, PrinterCreate, PrinterStatus
from database import get_db
from auth import get_current_user
from utils import scan_network, is_printer_via_snmp, get_printer_status
from crud import create_printer, get_printer_by_ip, update_printer_status, get_printer, delete_printer
from .. import model
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/printers", tags=["printers"])

@router.post("/scan")
def scan(subnet: ScanRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not subnet.subnet.startswith("192.168.") and not subnet.subnet.startswith("10.") and not subnet.subnet.startswith("172."):  # Basic private IP validation
        raise HTTPException(status_code=400, detail="Only private subnets allowed")
    
    try:
        devices = scan_network(subnet.subnet)
        discovered = []
        for device in devices:
            existing = get_printer_by_ip(db, device['ip'])
            if existing:
                continue  # Skip if already in DB
            
            # Confirm it's a printer (SNMP fallback; web check in status endpoint later)
            model = is_printer_via_snmp(device['ip'])
            if model:
                printer = PrinterCreate(ip=device['ip'], model=model, connection_mode="snmp" if 161 in device['ports'] else "web")
                created = create_printer(db, printer)
                discovered.append(created)
        
        return {"discovered": len(discovered), "printers": discovered}
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail="Scan failed")
    
@router.get("/{printer_id}/status", response_model=PrinterStatus)
async def get_status(printer_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    printer = db.query(model.Printer).filter(model.Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    try:
        toner_levels, errors = await get_printer_status(printer.ip, printer.connection_mode)
        updated_printer = update_printer_status(db, printer, toner_levels, errors)
        return PrinterStatus(
            toner_levels=updated_printer.toner_levels,
            errors=updated_printer.errors,
            model=updated_printer.model,
            ip=updated_printer.ip
        )
    except Exception as e:
        logger.error(f"Status fetch failed for printer {printer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch status")