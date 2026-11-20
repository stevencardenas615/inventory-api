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

def test_summary_of_a_manifest_with_no_products(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)            # cost 500.00
    r = client.get(f"/manifests/{manifest_id}/summary", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"manifest_id": manifest_id, "cost": "500.00", "items": 0, "sold": 0,
                        "available": 0, "not_available": 0, "revenue": "0.00", "profit": "-500.00"}

def test_summary_counts_by_status_and_adds_up_the_sales(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)            # cost 500.00
    for price in ("300.00", "250.50"):
        product_id = make_product(client, auth_headers, manifest_id, status="available").json()["product_id"]
        client.post(f"/products/{product_id}/sell", json={"sold_price": price}, headers=auth_headers)
    make_product(client, auth_headers, manifest_id, status="available")
    make_product(client, auth_headers, manifest_id)              # not_available
    deleted_id = make_product(client, auth_headers, manifest_id).json()["product_id"]
    client.delete(f"/products/{deleted_id}", headers=auth_headers)

    body = client.get(f"/manifests/{manifest_id}/summary", headers=auth_headers).json()
    assert (body["items"], body["sold"], body["available"], body["not_available"]) == (4, 2, 1, 1)
    assert body["revenue"] == "550.50"
    assert body["profit"] == "50.50"

def test_summary_keeps_other_manifests_out(client, auth_headers):
    first = make_manifest(client, auth_headers)
    second = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, second, status="available").json()["product_id"]
    client.post(f"/products/{product_id}/sell", json={"sold_price": "80.00"}, headers=auth_headers)
    assert client.get(f"/manifests/{first}/summary", headers=auth_headers).json()["revenue"] == "0.00"

def test_summary_of_missing_manifest_is_404(client, auth_headers):
    r = client.get("/manifests/999/summary", headers=auth_headers)
    assert r.status_code == 404
