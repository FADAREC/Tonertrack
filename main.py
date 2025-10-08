from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, get_db
import models
from auth import create_access_token, get_current_user # Import auth
from routers.printers import router as printers_router
# For real user management
from schemas import UserCreate
from crud import create_user, get_user_by_username
from auth import verify_password  # For real password check

# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tonertrack.onrender.com", "http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly allow OPTIONS
    allow_headers=["*"],  # Allow all headers (Authorization, Content-Type, etc.)
)

app.include_router(printers_router)

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    created_user = create_user(db, user)
    return {"detail": "User registered", "username": created_user.username}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # # For fake:
    # user = fake_users_db.get(form_data.username)
    # if not user or user["hashed_password"] != form_data.password:  # Fake check
    #     raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # For real (comment out fake above and uncomment):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/health")
def health_check(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"status": "healthy", "user": current_user.username}