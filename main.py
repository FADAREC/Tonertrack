from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from routers.printers import router as printers_router
from sqlalchemy.orm import Session
from database import engine, get_db
import model
from auth import create_access_token, get_current_user, fake_users_db  # Import auth

model.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(printers_router)

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    
    print(f"Received username: {form_data.username}")
    print(f"User found: {user}")

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    print(f"Stored hashed password: {user['hashed_password']}")
    print(f"Entered password: {form_data.password}")

    if user["hashed_password"] != form_data.password:  # Fake check
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/health")
def health_check(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"status": "healthy", "user": current_user["username"]}