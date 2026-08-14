
"""Agent report API — narrow write surface (token auth to be wired with agent tokens)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, UserInDB
from crud import get_printer
from schemas import AgentReportRequest
from services.printer_status import apply_agent_result
from routers.printers import _serialize

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/report")
def agent_report(
    body: AgentReportRequest,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Temporary: uses user JWT so we can test apply_agent_result before agent tokens exist.
    Replace with agent-token auth; never accept PrinterUpdate here.
    """
    printer = get_printer(db, body.printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    if not printer.ip_address:
        raise HTTPException(status_code=400, detail="Printer has no IP — agent cannot probe it")

    updated = apply_agent_result(
        db,
        printer,
        ok=body.ok,
        status=body.status,
        toner_level=body.toner_level,
        status_detail=body.status_detail,
        device_reported_offline=body.device_reported_offline,
    )
    return _serialize(updated)
