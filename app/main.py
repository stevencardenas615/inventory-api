import psycopg
from fastapi import FastAPI, Depends
from app.db import get_db

app = FastAPI()

@app.get("/health")
def health(conn: psycopg.Connection = Depends(get_db)):
    conn.execute("SELECT 1")
    return {"status": "ok"}
