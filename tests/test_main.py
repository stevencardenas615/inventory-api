def test_root_points_to_docs_and_source(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["docs"] == "/docs"
    assert body["health"] == "/health"
    assert "github.com" in body["source"]

def test_health_is_open_and_checks_the_database(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_docs_carry_the_project_name(client):
    r = client.get("/openapi.json")
    assert r.json()["info"]["title"] == "Inventory API"
