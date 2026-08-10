import os
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

from database import engine, get_db
import models
from auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    UserInDB,
    verify_password,
    SECRET_KEY,
    ALGORITHM,
    require_secrets,
    oauth2_scheme,
)
from schemas import UserCreate, UserResponse, Token, TrustInfo, TrustChoice, TrustStatus
from crud import create_user, get_user_by_login, get_users, get_trust, set_trust
from routers.printers import router as printers_router

# Fail fast if secrets missing (production)
_env = os.getenv("ENV", os.getenv("RENDER", "") and "production" or "development")
if _env == "production" or os.getenv("RENDER"):
    require_secrets()
elif not SECRET_KEY:
    # Local dev convenience only
    os.environ.setdefault("JWT_SECRET_KEY", "dev-only-change-me-use-32chars-min!!")
    import auth as auth_mod
    auth_mod.SECRET_KEY = os.environ["JWT_SECRET_KEY"]
    SECRET_KEY = auth_mod.SECRET_KEY

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="TonerTrack", version="1.0.0")

_cors = os.getenv(
    "CORS_ORIGINS",
    "https://tonertrack.onrender.com,http://localhost:3000,http://localhost:10000",
)
allow_origins = [o.strip() for o in _cors.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(printers_router)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception as e:
        return {"status": "degraded", "database": str(e)}


@app.get("/trust/info", response_model=TrustInfo)
def trust_info():
    """Shown before any network monitoring path. Clear and refusable."""
    return TrustInfo(
        title="How TonerTrack uses your network",
        what_we_access=[
            "Only printer IP addresses you explicitly add",
            "Only status signals those printers expose (toner, online/offline, page count when available)",
        ],
        what_we_never_access=[
            "The rest of your network (no subnet scan)",
            "File shares, email, or user PCs",
            "Active Directory or other directory services",
            "Any device you did not add as a printer",
        ],
        what_leaves_network=[
            "Account details you create in this app",
            "Printer names, locations, and toner/status metrics you enable",
            "Alert events (e.g. low toner)",
        ],
        kill_switch=(
            "Revoke the on-site agent token or uninstall the agent — probing stops. "
            "You can also stay on Manual only and never install an agent."
        ),
        modes=[
            {
                "id": "manual_only",
                "label": "Manual only",
                "description": "Staff update toner levels in the app. Nothing on your network is contacted.",
            },
            {
                "id": "agent_accepted",
                "label": "On-site agent (later)",
                "description": "A small agent inside your network talks only to printers you listed, then sends metrics to this app over HTTPS.",
            },
        ],
    )


@app.get("/trust/status", response_model=TrustStatus)
def trust_status(
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    row = get_trust(db, current_user.username)
    if not row:
        return TrustStatus(mode="manual_only", accepted_at=None)
    accepted = row.accepted_at.isoformat() if row.accepted_at else None
    return TrustStatus(mode=row.mode, accepted_at=accepted)


@app.post("/trust/choice", response_model=TrustStatus)
def trust_choice(
    body: TrustChoice,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    if body.mode not in {"manual_only", "agent_accepted"}:
        raise HTTPException(status_code=400, detail="mode must be manual_only or agent_accepted")
    # Agent install is not shipped in Step 1 — accepting only records preference
    row = set_trust(db, current_user.username, body.mode)
    accepted = row.accepted_at.isoformat() if row.accepted_at else None
    return TrustStatus(mode=row.mode, accepted_at=accepted)


@app.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_login(db, user.username) or get_user_by_login(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    created = create_user(db, user)
    access_token = create_access_token(
        data={"sub": created.username, "email": created.email, "role": created.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": created.username, "email": created.email, "role": created.role}
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_login(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect login or password")
    role = getattr(user, "role", None) or "operator"
    access_token = create_access_token(
        data={"sub": user.username, "email": user.email, "role": role}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "email": user.email, "role": role}
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@app.get("/me", response_model=UserResponse)
def me(current_user: UserInDB = Depends(get_current_user)):
    return current_user


@app.post("/logout")
def logout():
    return {"detail": "Logout successful"}


@app.post("/refresh", response_model=Token)
def refresh(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role") or "operator"
        if username is None or payload.get("type") != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    access_token = create_access_token(data={"sub": username, "email": email, "role": role})
    new_refresh = create_refresh_token(data={"sub": username, "email": email, "role": role})
    return {"access_token": access_token, "refresh_token": new_refresh, "token_type": "bearer"}


@app.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    users = get_users(db)
    return [{"username": u.username, "email": u.email, "role": getattr(u, "role", "operator")} for u in users]


# Serve React build when present (single-URL hosting on Render)
STATIC_DIR = Path(__file__).resolve().parent / "frontend" / "build"
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR / "static"), name="static")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        if full_path.startswith("api") or full_path in {
            "docs",
            "openapi.json",
            "redoc",
            "health",
            "login",
            "register",
            "me",
            "trust",
        }:
            raise HTTPException(status_code=404)
        index = STATIC_DIR / "index.html"
        if index.is_file():
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Frontend not built")
