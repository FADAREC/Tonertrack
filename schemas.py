from pydantic import BaseModel, constr

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: constr(min_length=3, strip_whitespace=True)  # At least 3 chars, no leading/trailing spaces
    password: constr(min_length=8, strip_whitespace=True)  # At least 8 chars

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

class PrinterStatus(BaseModel):
    toner_levels: dict
    errors: list[str]
    model: str
    ip: str

class PrinterResponse(BaseModel):
    id: int
    ip: str
    model: str | None
    toner_levels: dict
    errors: list[str]
    connection_mode: str

class PrinterList(BaseModel):
    printers: list[PrinterResponse]