from pydantic import BaseModel

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ScanRequest(BaseModel):
    subnet: str  # e.g., "192.168.1.0/24"

class PrinterCreate(BaseModel):
    ip: str
    model: str = None
    connection_mode: str = "web"  # Default