from sqlalchemy import Column, Integer, String, JSON
from database import Base

class Printer(Base):
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String, unique=True, index=True)
    model = Column(String)
    toner_levels = Column(JSON)  # e.g., {"black": 80, "cyan": 50}
    errors = Column(JSON)  # e.g., ["Paper Jam"]
    connection_mode = Column(String)  # "web" or "snmp"