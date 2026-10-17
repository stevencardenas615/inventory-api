import psycopg
from fastapi import APIRouter, Depends, HTTPException

from app.db import get_db
from app.deps import get_current_user
from app.models import Manifest, ManifestCreate, Product

router = APIRouter(prefix="/manifests", tags=["manifests"], dependencies=[Depends(get_current_user)])

@router.post("", response_model=Manifest)
def create_manifest(manifest: ManifestCreate, current_user: dict = Depends(get_current_user), conn: psycopg.Connection[dict]= Depends(get_db)):
    row = conn.execute(
        "INSERT INTO manifests (purchase_date, cost, entered_by) "
        "VALUES (%s, %s, %s) RETURNING *",
        (manifest.purchase_date, manifest.cost, current_user["user_id"])).fetchone()
    return row

@router.get("", response_model=list[Manifest])
def list_manifests(conn: psycopg.Connection[dict]= Depends(get_db)):
    results = conn.execute("SELECT * FROM manifests ORDER BY purchase_date DESC").fetchall()
    return results

@router.get("/{manifest_id}", response_model=Manifest)
def get_manifest(manifest_id: int, conn: psycopg.Connection[dict]= Depends(get_db)):
    row = conn.execute(
        "SELECT * FROM manifests WHERE manifest_id = %s", (manifest_id,)
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Manifest not found")
    return row

@router.get("/{manifest_id}/products", response_model=list[Product])
def list_manifest_products(manifest_id: int, conn: psycopg.Connection[dict] = Depends(get_db)):
    results = conn.execute("SELECT * FROM products WHERE manifest_id = %s AND status <> 'deleted' ORDER BY product_id DESC ", (manifest_id, )).fetchall()

    if not results:
        manifest = conn.execute("SELECT manifest_id FROM manifests WHERE manifest_id = %s", (manifest_id,)).fetchone()

        if manifest is None:
            raise HTTPException(status_code=404, detail="Manifest not found")

    return results
