import psycopg
from fastapi import FastAPI, Depends
from app.db import get_db
from app.routers import auth, manifests, products

REPO_URL = "https://github.com/stevencardenas615/inventory-api"

app = FastAPI(
    title="Inventory API",
    description="Tracks products bought in bulk through manifests, from intake through sale. "
                f"Every route except /health and /auth/token needs a token. Source and design notes: {REPO_URL}",
    version="0.2.0",
)
app.include_router(auth.router)
app.include_router(manifests.router)
app.include_router(products.router)

@app.get("/", include_in_schema=False)
def root():
    return {"service": "Inventory API", "version": app.version, "docs": "/docs", "health": "/health", "source": REPO_URL}

@app.get("/health")
def health(conn: psycopg.Connection[dict] = Depends(get_db)):
    conn.execute("SELECT 1")
    return {"status": "ok"}
