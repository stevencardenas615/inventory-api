import psycopg
from fastapi import FastAPI, Depends, HTTPException
from app.db import get_db
from app.models import ManifestCreate, Manifest

app = FastAPI()

@app.get("/health")
def health(conn: psycopg.Connection = Depends(get_db)):
    conn.execute("SELECT 1")
    return {"status": "ok"}

@app.post("/manifests", response_model=Manifest)
def create_manifest(manifest: ManifestCreate, conn: psycopg.Connection = Depends(get_db)):
    row = conn.execute(
        "INSERT INTO manifests (purchase_date, cost, entered_by) "
        "VALUES (%s, %s, %s) RETURNING *",
        (manifest.purchase_date, manifest.cost, 1),  # TODO: entered_by from JWT user
    ).fetchone()
    return row

@app.get("/manifests", response_model=list[Manifest])
def list_manifests(conn: psycopg.Connection = Depends(get_db)):
    results = conn.execute("SELECT * FROM manifests ORDER BY purchase_date DESC").fetchall()
    return results

@app.get("/manifests/{manifest_id}", response_model=Manifest)
def get_manifest(manifest_id: int, conn: psycopg.Connection = Depends(get_db)):
    row = conn.execute(
        "SELECT * FROM manifests WHERE manifest_id = %s", (manifest_id,)
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Manifest not found")
    return row