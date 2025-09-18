import models
from sqlalchemy.orm import Session
from database import engine, get_db
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt  # pyjwt is alias 'jose' in FastAPI docs, but we use pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
# For real hashing, uncomment and install passlib[bcrypt]
from passlib.context import CryptContext

load_dotenv()

# db = SessionLocal()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # Real hashing context

# Fake user DB for demo (replace with real DB later)
# fake_users_db = {
#     "testuser": {
#         "username": "testuser",
#         "hashed_password": "fakehashedpassword",  # In real: use bcrypt
#     }
# }

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # fake test:
    # user = fake_users_db.get(username)
    
    # For real: Query from DB (uncomment in main.py and crud.py)
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_password_hash(password: str):  # Real hashing function
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):  # Real verification
    return pwd_context.verify(plain_password, hashed_password)