import psycopg
from fastapi import FastAPI, Depends, HTTPException
from app.db import get_db
from app.models import ManifestCreate, Manifest, ProductCreate, Product

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

@app.post("/products", response_model=Product)
def create_product(product: ProductCreate, conn: psycopg.Connection = Depends(get_db)):
    try:
        row = conn.execute(
            "INSERT INTO products (manifest_id, barcode, product_name, retail_price, list_price, status) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING *",
            (product.manifest_id, product.barcode, product.product_name,
             product.retail_price, product.list_price, product.status),
        ).fetchone()
    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(status_code=400, detail="Manifest not found")
    return row

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int, conn: psycopg.Connection = Depends(get_db)):
    row = conn.execute(
        "SELECT * FROM products WHERE product_id = %s", (product_id,)
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return row

@app.get("/products", response_model=list[Product])
def list_products(conn: psycopg.Connection = Depends(get_db)):
    results = conn.execute("SELECT * FROM products ORDER BY product_id DESC").fetchall()
    return results