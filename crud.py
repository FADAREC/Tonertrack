from sqlalchemy.orm import Session
import models
from schemas import PrinterCreate, UserCreate
# For real hashing, uncomment
from auth import get_password_hash

def create_printer(db: Session, printer: PrinterCreate):
    db_printer = models.Printer(
        ip=printer.ip,
        model=printer.model,
        connection_mode=printer.connection_mode,
        snmp_community=printer.snmp_community,  # New
        toner_levels={},
        errors=[]
    )
    db.add(db_printer)
    db.commit()
    db.refresh(db_printer)
    return db_printer

def get_printers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Printer).offset(skip).limit(limit).all()

def get_printer_by_ip(db: Session, ip: str):
    return db.query(models.Printer).filter(models.Printer.ip == ip).first()

def get_printer(db: Session, printer_id: int):
    return db.query(models.Printer).filter(models.Printer.id == printer_id).first()

def update_printer_status(db: Session, printer: models.Printer, toner_levels: dict, errors: list):
    printer.toner_levels = toner_levels
    printer.errors = errors
    db.commit()
    db.refresh(printer)
    return printer

def delete_printer(db: Session, printer_id: int):
    printer = get_printer(db, printer_id)
    if printer:
        db.delete(printer)
        db.commit()
        return True
    return False

# User CRUD for real implementation
def create_user(db: Session, user: UserCreate):
    # Fake: hashed_password = user.password  # Uncomment for fake
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()