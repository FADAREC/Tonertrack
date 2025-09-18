from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from schemas import ScanRequest, PrinterCreate, PrinterStatus, PrinterList, PrinterResponse
from database import get_db
from auth import get_current_user
from utils import scan_network, is_printer_via_snmp, get_printer_status  # Now async
from crud import create_printer, get_printer_by_ip, get_printer, update_printer_status, get_printers, delete_printer
import logging
import ipaddress

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/printers", tags=["printers"])

@router.post("/scan")
async def scan(subnet: ScanRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Validate subnet format (CIDR)
    try:
        ipaddress.IPv4Network(subnet.subnet, strict=False)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subnet format (use CIDR like '192.168.1.0/24')")
    
    # Basic private IP check
    if not subnet.subnet.startswith("192.168.") and not subnet.subnet.startswith("10.") and not subnet.subnet.startswith("172."):
        raise HTTPException(status_code=400, detail="Only private subnets allowed")
    
    try:
        # Await async scan
        devices = await scan_network(subnet.subnet)
        discovered = []
        for device in devices:
            existing = get_printer_by_ip(db, device['ip'])
            if existing:
                continue  # Skip if already in DB
            
            # Await async SNMP check
            model = await is_printer_via_snmp(device['ip'])
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
    printer = get_printer(db, printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    try:
        toner_levels, errors = await get_printer_status(printer.ip, printer.connection_mode, printer.snmp_community)
        updated_printer = update_printer_status(db, printer, toner_levels, errors)
        return PrinterStatus(
            toner_levels=updated_printer.toner_levels,
            errors=updated_printer.errors,
            model=updated_printer.model,
            ip=updated_printer.ip
        )
    except ValueError as e:  # Catch status failures
        logger.error(f"Status fetch failed for printer {printer_id}: {e}")
        raise HTTPException(status_code=503, detail="Printer unreachable - check connection")  # 503 for service unavailable
    except Exception as e:
        logger.error(f"Unexpected error for printer {printer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch status")

@router.get("/", response_model=PrinterList)
def list_printers(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    printers = get_printers(db, skip=skip, limit=limit)
    return {"printers": printers}

@router.post("/add", response_model=PrinterResponse)
async def add_printer(printer: PrinterCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    existing = get_printer_by_ip(db, printer.ip)
    if existing:
        raise HTTPException(status_code=400, detail="Printer IP already exists")
    
    # Validate IP (basic)
    try:
        ipaddress.ip_address(printer.ip)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IP address")
    
    created = create_printer(db, printer)
    
    # Auto-query status on add
    try:
        toner_levels, errors = await get_printer_status(created.ip, created.connection_mode, created.snmp_community)
        update_printer_status(db, created, toner_levels, errors)
    except:
        logger.warning(f"Initial status query failed for {created.ip}; using defaults")
    
    return created

@router.delete("/{printer_id}")
def delete_printer_endpoint(printer_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    deleted = delete_printer(db, printer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Printer not found")
    return {"detail": "Printer deleted"}