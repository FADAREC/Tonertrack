from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
    login: str  #With this Users can login with Username or email
    password: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class UserResponse(BaseModel):
    username: str
    email: str

class ScanRequest(BaseModel):
    subnet: str

class PrinterCreate(BaseModel):
    name: str
    ip_address: str
    location: str = None
    connection_mode: str = "web"
    snmp_community: str = "public"
    department: str = None
    access_type: str = "public"
    allowed_users: list[str] = []

class PrinterUpdate(BaseModel):
    name: str = None
    location: str = None
    department: str = None
    access_type: str = None
    allowed_users: list[str] = None

class PrinterResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    location: str
    status: str
    toner_level: int
    page_count: int
    last_checked: str
    connection_mode: str
    department: str
    access_type: str
    allowed_users: list[str]

class PrinterList(BaseModel):
    printers: list[PrinterResponse]

class JobCreate(BaseModel):
    printer_id: int
    user: str
    document: str
    pages: int
    cost: float = 0.0
    status: str = "pending"

class JobUpdate(BaseModel):
    status: str = None

class JobResponse(BaseModel):
    id: int
    printer_id: int
    user: str
    document: str
    pages: int
    cost: float
    status: str
    timestamp: str

class JobList(BaseModel):
    jobs: list[JobResponse]

class AlertCreate(BaseModel):
    printer_id: int
    message: str

class AlertResponse(BaseModel):
    id: int
    printer_id: int
    message: str
    timestamp: str
    resolved: bool

class AlertList(BaseModel):
    alerts: list[AlertResponse]

class SettingUpdate(BaseModel):
    check_interval: int = None  # Seconds
    low_toner_threshold: int = 20