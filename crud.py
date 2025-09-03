from sqlalchemy.orm import Session
import model
from schemas import PrinterCreate

def create_printer(db: Session, printer: PrinterCreate):
    db_printer = model.Printer(
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
    return db.query(model.Printer).all()

def get_printer_by_ip(db: Session, ip: str):
    return db.query(model.Printer).filter(model.Printer.ip == ip).first()

def update_printer_status(db: Session, printer: model.Printer, toner_levels: dict, errors: list):
    printer.toner_levels = toner_levels
    printer.errors = errors
    db.commit()
    db.refresh(printer)
    return printer

def get_printer(db: Session, printer_id: int):
    return db.query(model.Printer).filter(model.Printer.id == printer_id).first()

def delete_printer(db: Session, printer: model.Printer):
    db.delete(printer)
    db.commit()