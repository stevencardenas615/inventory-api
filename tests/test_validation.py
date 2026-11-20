import pytest

from tests.test_products import make_manifest, make_product


@pytest.mark.parametrize("field, value", [
    ("retail_price", "-1.00"),            # negative money
    ("list_price", "123456789.00"),       # more digits than NUMERIC(10, 2) holds
    ("list_price", "9.999"),              # three decimals would be rounded without notice
    ("product_name", ""),
    ("barcode", ""),
    ("manifest_id", 0),
    ("manifest_id", 99999999999),         # past a Postgres int
])
def test_create_product_rejects_bad_input(client, auth_headers, field, value):
    overrides = {field: value}
    manifest_id = overrides.pop("manifest_id", make_manifest(client, auth_headers))
    r = make_product(client, auth_headers, manifest_id, **overrides)
    assert r.status_code == 422

def test_manifest_cost_cannot_be_negative(client, auth_headers):
    r = client.post("/manifests", json={"purchase_date": "2026-10-01", "cost": "-5.00"}, headers=auth_headers)
    assert r.status_code == 422

def test_sold_price_cannot_be_negative(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id, status="available").json()["product_id"]
    r = client.post(f"/products/{product_id}/sell", json={"sold_price": "-35.00"}, headers=auth_headers)
    assert r.status_code == 422
    assert client.get(f"/products/{product_id}", headers=auth_headers).json()["status"] == "available"

def test_patch_null_is_400_not_a_server_error(client, auth_headers):
    manifest_id = make_manifest(client, auth_headers)
    product_id = make_product(client, auth_headers, manifest_id).json()["product_id"]
    r = client.patch(f"/products/{product_id}", json={"list_price": None}, headers=auth_headers)
    assert r.status_code == 400

@pytest.mark.parametrize("field, value", [
    ("password", "short"),
    ("username", "ab"),
    ("first_name", ""),
])
def test_register_rejects_bad_input(client, field, value):
    body = {"username": "ana", "password": "pw123456", "first_name": "Ana", "last_name": "Lopez"}
    body[field] = value
    r = client.post("/auth/register", json=body)
    assert r.status_code == 422
