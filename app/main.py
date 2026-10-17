import psycopg
from fastapi import FastAPI, Depends
from app.db import get_db
from app.routers import auth, manifests, products

app = FastAPI()
app.include_router(auth.router)
app.include_router(manifests.router)
app.include_router(products.router)

@app.get("/health")
def health(conn: psycopg.Connection[dict] = Depends(get_db)):
    conn.execute("SELECT 1")
    return {"status": "ok"}
