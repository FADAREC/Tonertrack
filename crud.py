from sqlalchemy.orm import Session
import models
from schemas import PrinterCreate

def create_printer(db: Session, printer: PrinterCreate):
    db_printer = models.Printer(
        ip=printer.ip,
        model=printer.model,
        connection_mode=printer.connection_mode,
        toner_levels={},  # Empty initially
        errors=[]
    )
    db.add(db_printer)
    db.commit()
    db.refresh(db_printer)
    return db_printer

def get_printers(db: Session):
    return db.query(models.Printer).all()

def get_printer_by_ip(db: Session, ip: str):
    return db.query(models.Printer).filter(models.Printer.ip == ip).first()