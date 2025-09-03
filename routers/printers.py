from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import ScanRequest, PrinterCreate
from database import get_db
from auth import get_current_user
from utils import scan_network, is_printer_via_snmp
from crud import create_printer, get_printer_by_ip
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