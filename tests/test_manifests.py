from tests.test_products import make_manifest, make_product


def test_create_manifest_records_who_entered_it(client, auth_headers):
    r = client.post("/manifests", json={"purchase_date": "2026-10-01", "cost": "500.00"}, headers=auth_headers)
    assert r.status_code == 200
    me = client.get("/auth/me", headers=auth_headers).json()
    assert r.json()["entered_by"] == me["user_id"]      # from the token, not the request body
    assert r.json()["cost"] == "500.00"

def test_manifests_without_token_is_401(client):
    r = client.get("/manifests")
    assert r.status_code == 401

def test_list_manifests_newest_purchase_first(client, auth_headers):
    for day in ("2026-09-01", "2026-10-15", "2026-10-01"):
        client.post("/manifests", json={"purchase_date": day, "cost": "100.00"}, headers=auth_headers)
    r = client.get("/manifests", headers=auth_headers)
    assert [m["purchase_date"] for m in r.json()] == ["2026-10-15", "2026-10-01", "2026-09-01"]

def test_get_manifest_by_id(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    r = client.get(f"/manifests/{manifest_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["purchase_date"] == "2026-10-01"

def test_get_missing_manifest_is_404(client, auth_headers):
    r = client.get("/manifests/999", headers=auth_headers)
    assert r.status_code == 404

def test_manifest_products_hides_deleted_ones(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    kept_id = make_product(client, auth_headers, manifest_id).json()["product_id"]
    deleted_id = make_product(client, auth_headers, manifest_id).json()["product_id"]
    client.delete(f"/products/{deleted_id}", headers=auth_headers)
    r = client.get(f"/manifests/{manifest_id}/products", headers=auth_headers)
    assert [p["product_id"] for p in r.json()] == [kept_id]

def test_manifest_with_no_products_is_an_empty_list(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    r = client.get(f"/manifests/{manifest_id}/products", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []

def test_products_of_missing_manifest_is_404(client, auth_headers):
    r = client.get("/manifests/999/products", headers=auth_headers)
    assert r.status_code == 404
