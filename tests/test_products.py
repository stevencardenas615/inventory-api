def make_manifest(client, auth_headers):
    r = client.post("/manifests", json={"purchase_date": "2026-10-01", "cost": "500.00"}, headers=auth_headers)
    return r.json()["manifest_id"]


def make_product(client, auth_headers, manifest_id, **overrides):
    body = {"manifest_id": manifest_id, "barcode": "111", "product_name": "Blender",
            "retail_price": "49.99", "list_price": "29.99"}
    body.update(overrides)
    return client.post("/products", json=body, headers=auth_headers)

def test_create_product_defaults_to_not_available(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    r = make_product(client, auth_headers, manifest_id)
    assert r.status_code == 200
    assert r.json()["status"] == "not_available"

def test_bad_manifest(client, auth_headers):
    r = make_product(client, auth_headers, 999)
    assert r.status_code == 400

def test_list_products_without_token_is_401(client):
    r = client.get("/products")
    assert r.status_code == 401

def test_get_product_by_id(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id).json()["product_id"]
    r = client.get(f"/products/{product_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["product_name"] == "Blender"

def test_get_missing_product_is_404(client, auth_headers):
    r = client.get("/products/999", headers=auth_headers)
    assert r.status_code == 404

def test_patch_list_price(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id).json()["product_id"]
    r = client.patch(f"/products/{product_id}", json={"list_price": "24.99"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["list_price"] == "24.99"

def test_patch_status_sold_is_422(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id).json()["product_id"]
    r = client.patch(f"/products/{product_id}", json={"status": "sold"}, headers=auth_headers)
    assert r.status_code == 422

def test_patch_empty_body_is_400(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id).json()["product_id"]
    r = client.patch(f"/products/{product_id}", json={}, headers=auth_headers)
    assert r.status_code == 400

def test_sell_available_product_is_200(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id, status="available").json()["product_id"]
    r = client.post(f"/products/{product_id}/sell", json={"sold_price": "35.00"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "sold"
    assert r.json()["sold_at"] is not None

def test_sell_product_twice_is_409(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id, status="available").json()["product_id"]
    client.post(f"/products/{product_id}/sell", json={"sold_price": "35.00"}, headers=auth_headers)   # first sale
    r = client.post(f"/products/{product_id}/sell", json={"sold_price": "35.00"}, headers=auth_headers)  # second
    assert r.status_code == 409

def test_delete_a_sold_product_is_409(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id, status="available").json()["product_id"]
    client.post(f"/products/{product_id}/sell", json={"sold_price": "35.00"}, headers=auth_headers)
    r = client.delete(f"/products/{product_id}", headers=auth_headers)
    assert r.status_code == 409

def test_delete_available_product_is_200(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id, status="available").json()["product_id"]
    r = client.delete(f"/products/{product_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "deleted"

def test_deleted_product_hidden_from_list(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id).json()["product_id"]
    client.delete(f"/products/{product_id}", headers=auth_headers)
    r = client.get("/products", headers=auth_headers)
    assert r.json() == []

def test_patch_sold_product_is_409(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id, status="available").json()["product_id"]
    client.post(f"/products/{product_id}/sell", json={"sold_price": "35.00"}, headers=auth_headers)
    r = client.patch(f"/products/{product_id}", json={"list_price": "1.00"}, headers=auth_headers)
    assert r.status_code == 409

def test_create_with_status_deleted_is_422(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    r = make_product(client, auth_headers, manifest_id, status="deleted")
    assert r.status_code == 422

def test_patch_status_deleted_is_422(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id).json()["product_id"]
    r = client.patch(f"/products/{product_id}", json={"status": "deleted"}, headers=auth_headers)
    assert r.status_code == 422

def test_patch_cannot_bring_back_a_deleted_product(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id).json()["product_id"]
    client.delete(f"/products/{product_id}", headers=auth_headers)
    r = client.patch(f"/products/{product_id}", json={"status": "available"}, headers=auth_headers)
    assert r.status_code == 409
    assert client.get(f"/products/{product_id}", headers=auth_headers).json()["status"] == "deleted"

def test_patch_missing_product_is_404(client, auth_headers):
    r = client.patch("/products/999", json={"list_price": "1.00"}, headers=auth_headers)
    assert r.status_code == 404

def test_delete_missing_product_is_404(client, auth_headers):
    r = client.delete("/products/999", headers=auth_headers)
    assert r.status_code == 404

def test_sell_missing_product_is_404(client, auth_headers):
    r = client.post("/products/999/sell", json={"sold_price": "35.00"}, headers=auth_headers)
    assert r.status_code == 404

def test_sell_product_that_is_not_available_is_409(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id).json()["product_id"]   # defaults to not_available
    r = client.post(f"/products/{product_id}/sell", json={"sold_price": "35.00"}, headers=auth_headers)
    assert r.status_code == 409

def test_status_filter_returns_only_that_status(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    make_product(client, auth_headers, manifest_id)                                  # not_available
    available_id = make_product(client, auth_headers, manifest_id, status="available").json()["product_id"]
    deleted_id = make_product(client, auth_headers, manifest_id).json()["product_id"]
    client.delete(f"/products/{deleted_id}", headers=auth_headers)

    r = client.get("/products", params={"status": "available"}, headers=auth_headers)
    assert [p["product_id"] for p in r.json()] == [available_id]
    # deleted rows are hidden from the plain list but can be asked for by name
    r = client.get("/products", params={"status": "deleted"}, headers=auth_headers)
    assert [p["product_id"] for p in r.json()] == [deleted_id]

def test_status_filter_with_unknown_status_is_422(client, auth_headers):
    r = client.get("/products", params={"status": "lost"}, headers=auth_headers)
    assert r.status_code == 422

def test_two_sales_at_the_same_moment_sell_the_product_once(client, auth_headers):
    """Two requests for the same product, released together from two threads. Each
    request gets its own database connection, so Postgres decides: the second
    UPDATE waits for the first, then finds the row no longer 'available'."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id, status="available").json()["product_id"]
    start = Barrier(2)

    def sell(price):
        start.wait(timeout=5)
        return client.post(f"/products/{product_id}/sell", json={"sold_price": price}, headers=auth_headers)

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(sell, ["35.00", "40.00"]))

    assert sorted(r.status_code for r in responses) == [200, 409]
    winner = next(r for r in responses if r.status_code == 200).json()
    assert client.get(f"/products/{product_id}", headers=auth_headers).json()["sold_price"] == winner["sold_price"]
