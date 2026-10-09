import os

import psycopg
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from app.db import get_db
from app.main import app

load_dotenv()
TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]


@pytest.fixture
def client():
    def override_get_db():
        with psycopg.connect(TEST_DATABASE_URL, row_factory=dict_row, connect_timeout=5) as conn:
            yield conn

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

    with psycopg.connect(TEST_DATABASE_URL, connect_timeout=5) as conn:
        conn.execute("TRUNCATE products, manifests, users RESTART IDENTITY CASCADE")

@pytest.fixture
def auth_headers(client):
    client.post("/auth/register", json={
        "username": "tester", "password": "pw12345",
        "first_name": "Test", "last_name": "User",
    })
    r = client.post("/auth/token", data={"username": "tester", "password": "pw12345"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
