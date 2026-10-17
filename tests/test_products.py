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