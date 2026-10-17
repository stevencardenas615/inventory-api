import psycopg
from fastapi import FastAPI, Depends, HTTPException
from psycopg import sql
from app.db import get_db
from app.models import ProductCreate, Product, ProductUpdate, ProductSell, Status
from app.deps import get_current_user
from app.routers import auth, manifests

app = FastAPI()
app.include_router(auth.router)
app.include_router(manifests.router)

@app.get("/health")
def health(conn: psycopg.Connection = Depends(get_db)):
    conn.execute("SELECT 1")
    return {"status": "ok"}

@app.post("/products", response_model=Product,  dependencies=[Depends(get_current_user)])
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

@app.get("/products/{product_id}", response_model=Product, dependencies=[Depends(get_current_user)])
def get_product(product_id: int, conn: psycopg.Connection = Depends(get_db)):
    row = conn.execute(
        "SELECT * FROM products WHERE product_id = %s", (product_id,)
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return row

@app.get("/products", response_model=list[Product], dependencies=[Depends(get_current_user)])
def list_products(status: Status | None = None, conn: psycopg.Connection[dict] = Depends(get_db)):
    if status is None:
        results = conn.execute("SELECT * FROM products WHERE status <> 'deleted' ORDER BY product_id DESC").fetchall()
    else:
        results = conn.execute("SELECT * FROM products WHERE status = %s ORDER BY product_id DESC", (status.value,)).fetchall()
    return results

@app.patch("/products/{product_id}", response_model=Product, dependencies=[Depends(get_current_user)])
def update_product(product_id: int, product: ProductUpdate, conn: psycopg.Connection = Depends(get_db)):
    updates = product.model_dump(exclude_unset=True)

    if not updates:       
        raise HTTPException(status_code=400, detail="No fields to update")
    
    set_clause = sql.SQL(", ").join(sql.SQL("{} = %s").format(sql.Identifier(col)) for col in updates)
    query = sql.SQL("UPDATE products SET {} WHERE product_id = %s AND status <> 'sold' RETURNING *").format(set_clause)

    row = conn.execute(query, (*updates.values(), product_id)).fetchone()

    if row is None:
        existing = conn.execute("SELECT status FROM products WHERE product_id = %s", (product_id,)).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Product not found")
        raise HTTPException(status_code=409, detail="Sold products cannot be edited")
    return row

@app.post("/products/{product_id}/sell", response_model=Product, dependencies=[Depends(get_current_user)])
def sell_product(product_id: int, sale: ProductSell, conn: psycopg.Connection[dict] = Depends(get_db)):
    row = conn.execute("UPDATE products SET status ='sold', sold_price = %s, sold_at = now()"
                       " WHERE product_id = %s AND status = 'available' RETURNING *",
                       (sale.sold_price, product_id,)).fetchone()

    if row is None:
        existing = conn.execute("SELECT status FROM products WHERE product_id = %s", (product_id,)).fetchone()

        if existing is None:
            raise HTTPException(status_code=404, detail="Product not found")

        raise HTTPException(status_code=409, detail=f"Product is {existing['status']}, only available products can be sold",)

    return row

@app.delete("/products/{product_id}", response_model=Product, dependencies=[Depends(get_current_user)])

def delete_product(product_id: int, conn: psycopg.Connection[dict] = Depends(get_db)):
    row = conn.execute("UPDATE products SET status ='deleted' "
                       " WHERE product_id = %s AND status <> 'sold' RETURNING *",
                       (product_id,)).fetchone()

    if row is None:
        existing = conn.execute("SELECT status FROM products WHERE product_id = %s", (product_id,)).fetchone()

        if existing is None:
            raise HTTPException(status_code=404, detail="Product not found")

        raise HTTPException(status_code=409, detail="Sold products cannot be deleted",)

    return row
