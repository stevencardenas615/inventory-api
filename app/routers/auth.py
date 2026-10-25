import psycopg
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.db import get_db
from app.deps import get_current_user
from app.models import User, UserCreate
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=User)
def register(user: UserCreate, conn: psycopg.Connection[dict]= Depends(get_db)):
    if os.environ.get("ALLOW_REGISTRATION", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="Registration is closed")
    try:
        row = conn.execute(
            "INSERT INTO users (username, password_hash, first_name, last_name) "
            "VALUES (%s, %s, %s, %s) "
            "RETURNING user_id, username, first_name, last_name, created_at",
            (user.username, hash_password(user.password), user.first_name, user.last_name),
        ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Username already taken")
    return row

@router.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends(), conn: psycopg.Connection[dict] = Depends(get_db)):
    row = conn.execute("SELECT user_id, password_hash FROM users WHERE username = %s", (form.username,)).fetchone()
    if row is None or not verify_password(form.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": create_access_token(row["user_id"]), "token_type": "bearer"}

@router.get("/me", response_model=User)
def read_me(current_user = Depends(get_current_user)):
    return current_user
