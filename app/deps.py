import jwt
import psycopg
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.db import get_db
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_current_user(token: str = Depends(oauth2_scheme), conn: psycopg.Connection[dict] = Depends(get_db),):
    credentials_error = HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        user_id = decode_access_token(token)
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise credentials_error

    row = conn.execute("SELECT user_id, username, first_name, last_name, created_at FROM users WHERE user_id = %s", (user_id,)).fetchone()
    if row is None:
        raise credentials_error
    return row
