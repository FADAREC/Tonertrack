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
    # Creation is not verification — clocks stay null until first status/toner write
    data["last_checked"] = None
    data["last_verified_at"] = None
    data["last_attempt_at"] = None
    data["fail_streak"] = 0
    data["status_detail"] = None

    if data.get("connection_mode") == "manual":
        if data.get("toner_level") is not None:
            # Explicit toner on create counts as first verification
            from services.printer_status import normalize_toner_status
            from datetime import datetime
            tl, st = normalize_toner_status(data["toner_level"], data.get("status"))
            data["toner_level"] = tl
            data["status"] = st or "online"
            now = datetime.utcnow()
            data["last_verified_at"] = now
            data["last_checked"] = now
        else:
            data["status"] = "unknown"
            data["toner_level"] = None

    allowed = {c.name for c in models.Printer.__table__.columns}
    payload = {k: v for k, v in data.items() if k in allowed}
    db_printer = models.Printer(**payload)
    db.add(db_printer)
    db.commit()
    db.refresh(db_printer)
    return db_printer


def get_printers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Printer).offset(skip).limit(limit).all()


def get_printer(db: Session, printer_id: int):
    return db.query(models.Printer).filter(models.Printer.id == printer_id).first()


def update_printer(db: Session, printer: models.Printer, updates: dict):
    """Metadata or raw field updates. Status/toner verification must use services.printer_status."""
    for key, value in updates.items():
        if key in {"last_checked", "last_verified_at", "last_attempt_at", "fail_streak"}:
            # Only domain helpers should set clocks / streak
            if key in updates and key != "fail_streak":
                setattr(printer, key, value)
            continue
        if hasattr(printer, key):
            setattr(printer, key, value)
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
