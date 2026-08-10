from sqlalchemy import Column, Integer, String, JSON, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.sql import func
from database import Base


class Printer(Base):
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ip_address = Column(String, index=True)
    location = Column(String, default="")
    status = Column(String, default="unknown")
    toner_level = Column(Integer, nullable=True)
    page_count = Column(Integer, default=0)
    last_checked = Column(DateTime, default=func.now())
    connection_mode = Column(String, default="manual")
    snmp_community = Column(String, default="public")
    department = Column(String, default="")
    access_type = Column(String, default="public")
    allowed_users = Column(JSON, default=list)
    notes = Column(String, default="")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="operator")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    printer_id = Column(Integer, ForeignKey("printers.id"))
    user = Column(String)
    document = Column(String)
    pages = Column(Integer)
    cost = Column(Float, default=0.0)
    status = Column(String, default="pending")
    timestamp = Column(DateTime, default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    printer_id = Column(Integer, ForeignKey("printers.id"))
    message = Column(String)
    timestamp = Column(DateTime, default=func.now())
    resolved = Column(Boolean, default=False)


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True)
    value = Column(String)


class TrustPreference(Base):
    __tablename__ = "trust_preferences"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    mode = Column(String, default="manual_only")
    accepted_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
