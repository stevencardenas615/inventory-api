def register(client, username="ana", password="pw12345"):
    return client.post("/auth/register", json={
        "username": username, "password": password,
        "first_name": "Ana", "last_name": "Lopez",
    })

def test_register_returns_user_without_password(client):
    r = register(client)                        # ACT (no arrange needed, empty db)
    assert r.status_code == 200                 # ASSERT
    body = r.json()
    assert body["username"] == "ana"            # ASSERT
    assert "password_hash" not in body          # ASSERT

def test_duplicate_username_is_409(client):
    register(client)
    r = register(client)
    assert r.status_code == 409

def test_login_works(client):
    register(client)
    r = client.post("/auth/token", data={"username": "ana", "password": "pw12345",})
    assert r.status_code == 200
    assert "access_token" in r.json()
    
def test_wrong_password(client):
    register(client)
    r = client.post("/auth/token", data={"username": "ana", "password": "nope",})
    assert r.status_code == 401
    
def test_me_without_token_is_401(client):
    r = client.get("/auth/me")
    assert r.status_code == 401

def test_me_with_token_returns_user(client, auth_headers):
    r = client.get("/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["username"] == "tester"

def test_me_with_invalid_token_is_401(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401

def test_login_unknown_user_is_401(client):
    r = client.post("/auth/token", data={"username": "ghost", "password": "whatever"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Incorrect username or password"

def test_register_with_missing_field(client):
    r = client.post("/auth/register", json={"username": "sbc", "password": "pwd12345","first_name": "steven",})
    assert r.status_code == 422