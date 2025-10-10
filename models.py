from sqlalchemy import Column, Integer, String, JSON
from database import Base

class Printer(Base):
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String, unique=True, index=True)
    model = Column(String)
    toner_levels = Column(JSON)
    errors = Column(JSON)
    connection_mode = Column(String)
    snmp_community = Column(String, default="public")
    department = Column(String, default=None)
    location = Column(String, default=None)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="staff")