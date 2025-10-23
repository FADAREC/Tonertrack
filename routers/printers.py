<<<<<<< HEAD
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from schemas import ScanRequest, PrinterCreate, PrinterUpdate, PrinterResponse, PrinterList
from database import get_db
from auth import get_current_user
from utils import scan_network, is_printer_via_snmp, get_printer_status
from crud import create_printer, get_printers, get_printer, update_printer, delete_printer
import logging
import ipaddress
=======
# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.orm import Session
# from schemas import ScanRequest, PrinterCreate, PrinterStatus, PrinterList, PrinterResponse
# from database import get_db
# from auth import get_current_user, UserInDB
# from utils import scan_network, is_printer_via_snmp, get_printer_status, get_print_jobs
# from crud import create_printer, get_printers, get_printer, update_printer, delete_printer, create_job, get_jobs, get_job, update_job, delete_job, create_alert, get_alerts, delete_alert, update_setting, get_setting
# import logging
# import ipaddress
# from datetime import datetime
>>>>>>> aecf2eb4ddcc28bc448e05fa9bec3ce966a4d970

# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/printers", tags=["printers"])

<<<<<<< HEAD
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
=======
# @router.post("/scan")
# async def scan(subnet: ScanRequest, db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
#     if current_user.role != "admin":
#         raise HTTPException(status_code=403, detail="Admin only")
#     try:
#         ipaddress.IPv4Network(subnet.subnet, strict=False)
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid subnet format")
#     if not subnet.subnet.startswith("192.168.") and not subnet.subnet.startswith("10.") and not subnet.subnet.startswith("172."):
#         raise HTTPException(status_code=400, detail="Only private subnets allowed")
    
#     try:
#         devices = await scan_network(subnet.subnet)
#         discovered = []
#         for device in devices:
#             existing = get_printer_by_ip(db, device['ip'])
#             if existing:
#                 continue
#             model = await is_printer_via_snmp(device['ip'])
#             if model:
#                 printer = PrinterCreate(ip=device['ip'], model=model, connection_mode="snmp" if 161 in device['ports'] else "web")
#                 created = create_printer(db, printer)
#                 discovered.append(created)
#         return {"discovered": len(discovered), "printers": discovered}
#     except Exception as e:
#         logger.error(f"Scan failed: {e}")
#         raise HTTPException(status_code=500, detail="Scan failed")

# @router.get("/{printer_id}/status", response_model=PrinterResponse)
# async def get_status(printer_id: int, db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
#     printer = get_printer(db, printer_id)
#     if not printer:
#         raise HTTPException(status_code=404, detail="Printer not found")
#     try:
#         toner_levels, errors = await get_printer_status(printer.ip_address, printer.connection_mode, printer.snmp_community)
#         updates = {
#             "toner_level": list(toner_levels.values())[0] if toner_levels else 0,  # Simplified
#             "status": "online" if toner_levels else "offline",
#             "last_checked": datetime.now()
#         }
#         updated_printer = update_printer(db, printer, updates)
#         return updated_printer
#     except:
#         updates = {"status": "offline", "last_checked": datetime.now()}
#         updated_printer = update_printer(db, printer, updates)
#         return updated_printer
>>>>>>> aecf2eb4ddcc28bc448e05fa9bec3ce966a4d970

# @router.get("/", response_model=PrinterList)
# def list_printers(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
#     printers = get_printers(db, skip=skip, limit=limit)
#     return {"printers": printers}

<<<<<<< HEAD
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
=======
# @router.post("/add", response_model=PrinterResponse)
# async def add_printer(printer: PrinterCreate, db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
#     if current_user.role != "admin":
#         raise HTTPException(status_code=403, detail="Admin only")
#     existing = get_printer_by_ip(db, printer.ip)
#     if existing:
#         raise HTTPException(status_code=400, detail="Printer IP already exists")
#     try:
#         ipaddress.ip_address(printer.ip)
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid IP address")
#     created = create_printer(db, printer)
#     try:
#         toner_levels, errors = await get_printer_status(created.ip, created.connection_mode, created.snmp_community)
#         update_printer_status(db, created, toner_levels, errors)
#     except:
#         logger.warning(f"Initial status query failed for {created.ip}; using defaults")
#     return created

# @router.patch("/{printer_id}", response_model=PrinterResponse)
# async def update_printer_endpoint(printer_id: int, updates: PrinterUpdate, db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
#     if current_user.role != "admin":
#         raise HTTPException(status_code=403, detail="Admin only")
#     printer = get_printer(db, printer_id)
#     if not printer:
#         raise HTTPException(status_code=404, detail="Printer not found")
#     updated = update_printer(db, printer, updates.dict(exclude_unset=True))
#     return updated

# @router.delete("/{printer_id}")
# def delete_printer_endpoint(printer_id: int, db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
#     if current_user.role != "admin":
#         raise HTTPException(status_code=403, detail="Admin only")
#     deleted = delete_printer(db, printer_id)
#     if not deleted:
#         raise HTTPException(status_code=404, detail="Printer not found")
#     return {"detail": "Printer deleted"}
>>>>>>> aecf2eb4ddcc28bc448e05fa9bec3ce966a4d970
