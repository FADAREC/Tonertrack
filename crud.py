from sqlalchemy.orm import Session
from datetime import datetime, timezone
import models
from schemas import PrinterCreate, UserCreate, JobCreate, AlertCreate
from auth import get_password_hash


def create_user(db: Session, user: UserCreate, role: str | None = None):
    hashed_password = get_password_hash(user.password)
    # First user becomes admin
    if role is None:
        count = db.query(models.User).count()
        role = "admin" if count == 0 else "operator"
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_login(db: Session, login: str):
    return (
        db.query(models.User)
        .filter((models.User.username == login) | (models.User.email == login))
        .first()
    )


def get_users(db: Session):
    return db.query(models.User).all()


def create_printer(db: Session, printer: PrinterCreate):
    data = printer.model_dump() if hasattr(printer, "model_dump") else printer.dict()
    # Manual mode: no probe; status unknown unless toner provided
    if data.get("connection_mode") == "manual":
        if data.get("toner_level") is not None:
            data["status"] = "low" if data["toner_level"] <= 20 else "online"
        else:
            data["status"] = "unknown"
            data["toner_level"] = None
    db_printer = models.Printer(**{k: v for k, v in data.items() if hasattr(models.Printer, k)})
    db.add(db_printer)
    db.commit()
    db.refresh(db_printer)
    return db_printer


def get_printers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Printer).offset(skip).limit(limit).all()


def get_printer(db: Session, printer_id: int):
    return db.query(models.Printer).filter(models.Printer.id == printer_id).first()


def update_printer(db: Session, printer: models.Printer, updates: dict):
    for key, value in updates.items():
        if value is not None and hasattr(printer, key):
            setattr(printer, key, value)
    if "toner_level" in updates and updates["toner_level"] is not None:
        level = updates["toner_level"]
        printer.status = "low" if level <= 20 else "online"
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


def get_trust(db: Session, username: str):
    return (
        db.query(models.TrustPreference)
        .filter(models.TrustPreference.username == username)
        .first()
    )


def set_trust(db: Session, username: str, mode: str):
    row = get_trust(db, username)
    now = datetime.now(timezone.utc)
    if not row:
        row = models.TrustPreference(username=username, mode=mode, accepted_at=now if mode == "agent_accepted" else None)
        db.add(row)
    else:
        row.mode = mode
        row.accepted_at = now if mode == "agent_accepted" else None
    db.commit()
    db.refresh(row)
    return row


def create_job(db: Session, job: JobCreate):
    db_job = models.Job(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def get_jobs(db: Session):
    return db.query(models.Job).all()


def create_alert(db: Session, alert: AlertCreate):
    db_alert = models.Alert(**alert.dict())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def get_alerts(db: Session):
    return db.query(models.Alert).all()


def get_setting(db: Session, key: str):
    return db.query(models.Setting).filter(models.Setting.key == key).first()


def update_setting(db: Session, key: str, value: str):
    setting = get_setting(db, key)
    if not setting:
        setting = models.Setting(key=key, value=value)
        db.add(setting)
    else:
        setting.value = value
    db.commit()
    db.refresh(setting)
    return setting
