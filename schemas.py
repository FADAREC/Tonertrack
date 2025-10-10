from pydantic import BaseModel

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "staff"

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ScanRequest(BaseModel):
    subnet: str

class PrinterCreate(BaseModel):
    ip: str
    model: str = None
    connection_mode: str = "web"
    snmp_community: str = "public"
    department: str = None
    location: str = None

class PrinterStatus(BaseModel):
    toner_levels: dict
    errors: list[str]
    model: str
    ip: str
    department: str = None
    location: str = None

class PrinterResponse(BaseModel):
    id: int
    ip: str
    model: str | None
    toner_levels: dict
    errors: list[str]
    connection_mode: str
    department: str | None
    location: str | None

class PrinterList(BaseModel):
    printers: list[PrinterResponse]