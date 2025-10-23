from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from database import engine, get_db
import models
from auth import create_access_token, create_refresh_token, get_current_user, UserInDB, verify_password, SECRET_KEY, ALGORITHM
from schemas import UserCreate, UserResponse, Token
from crud import create_user, get_user_by_login, get_users
from routers.printers import router as printers_router

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tonertrack.onrender.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(printers_router)


@app.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_login(db, user.username) or get_user_by_login(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    created_user = create_user(db, user)
    access_token = create_access_token(data={"sub": created_user.username, "email": created_user.email})
    refresh_token = create_refresh_token(data={"sub": created_user.username, "email": created_user.email})
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_login(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect login or password")
    
    access_token = create_access_token(data={"sub": user.username, "email": user.email})
    refresh_token = create_refresh_token(data={"sub": user.username, "email": user.email})
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@app.get("/me", response_model=UserResponse)
def me(current_user: UserInDB = Depends(get_current_user)):
    return current_user


@app.post("/logout")
def logout():
    return {"detail": "Logout successful"}


@app.post("/refresh", response_model=Token)
def refresh(refresh_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        email: str = payload.get("email")
        if username is None or payload.get("type") != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    access_token = create_access_token(data={"sub": username, "email": email})
    new_refresh_token = create_refresh_token(data={"sub": username, "email": email})
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


@app.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return get_users(db)


@app.post("/users", response_model=UserResponse)
def add_user(user: UserCreate, db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return create_user(db, user)

# @app.delete("/users/{user_id}")
# def delete_user_endpoint(user_id: int, db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
#     if current_user.role != "admin":
#         raise HTTPException(status_code=403, detail="Admin only")
#     deleted = delete_user(db, user_id)
#     if not deleted:
#         raise HTTPException(status_code=404, detail="User not found")
#     return {"detail": "User deleted"}
