from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import models
from schemas import PrinterCreate, UserCreate, JobCreate, AlertCreate, SettingUpdate
from auth import get_password_hash

def create_printer(db: Session, printer: PrinterCreate):
    db_printer = models.Printer(**printer.dict())
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

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_login(db: Session, login: str):
    return db.query(models.User).filter((models.User.username == login) | (models.User.email == login)).first()

def get_users(db: Session):
    return db.query(models.User).all()

def create_job(db: Session, job: JobCreate):
    db_job = models.Job(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def get_jobs(db: Session):
    return db.query(models.Job).all()

def get_job(db: Session, job_id: int):
    return db.query(models.Job).filter(models.Job.id == job_id).first()

def update_job(db: Session, job: models.Job, updates: dict):
    for key, value in updates.items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job

def delete_job(db: Session, job_id: int):
    job = get_job(db, job_id)
    if job:
        db.delete(job)
        db.commit()
        return True
    return False

def create_alert(db: Session, alert: AlertCreate):
    db_alert = models.Alert(**alert.dict())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

def get_alerts(db: Session):
    return db.query(models.Alert).all()

def delete_alert(db: Session, alert_id: int):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if alert:
        db.delete(alert)
        db.commit()
        return True
    return False

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