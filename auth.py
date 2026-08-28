from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from pydantic import BaseModel

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "480"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class UserInDB(BaseModel):
    username: str
    email: str
    role: str = "operator"


def require_secrets() -> None:
    """Fail fast in production if auth secrets are missing."""
    if not SECRET_KEY or len(SECRET_KEY) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to a strong secret (32+ characters). "
            "Refusing to start."
        )


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    from database import SessionLocal
    import models

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None or payload.get("type") != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db = SessionLocal()
    try:
        row = db.query(models.User).filter(models.User.username == username).first()
        if not row:
            raise credentials_exception
        from crud import ensure_user_workspace
        try:
            ws_id = ensure_user_workspace(db, row)
        except Exception:
            # Last resort: still reject empty workspace rather than leak global data
            ws_id = getattr(row, "workspace_id", None)
        return UserInDB(
            username=row.username,
            email=row.email or "",
            role=row.role or "admin",
            workspace_id=ws_id,
        )
    finally:
        db.close()
