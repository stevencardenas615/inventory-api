import os

import psycopg
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from app.db import get_db
from app.main import app

load_dotenv()
TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]

# The client fixture empties every table before and after each test, so refuse
# to run against anything that is not clearly a test database.
if not str(conninfo_to_dict(TEST_DATABASE_URL).get("dbname", "")).endswith("_test"):
    raise RuntimeError("TEST_DATABASE_URL must point at a database whose name ends in _test")


def empty_tables():
    with psycopg.connect(TEST_DATABASE_URL, connect_timeout=5) as conn:
        conn.execute("TRUNCATE products, manifests, users RESTART IDENTITY CASCADE")


@pytest.fixture
def client(monkeypatch):
    # Registration is closed by default. The tests need it open and say so here,
    # instead of depending on whatever the machine's environment happens to set.
    monkeypatch.setenv("ALLOW_REGISTRATION", "true")
    empty_tables()  # rows left behind by a run that crashed must not leak into this test

    def override_get_db():
        with psycopg.connect(TEST_DATABASE_URL, row_factory=dict_row, connect_timeout=5) as conn: # type: ignore
            yield conn

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    empty_tables()


@pytest.fixture
def auth_headers(client):
    r = client.post("/auth/register", json={
        "username": "tester", "password": "pw123456",
        "first_name": "Test", "last_name": "User",
    })
    assert r.status_code == 200, f"could not register the test user: {r.text}"
    r = client.post("/auth/token", data={"username": "tester", "password": "pw123456"})
    assert r.status_code == 200, f"could not log in as the test user: {r.text}"
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
