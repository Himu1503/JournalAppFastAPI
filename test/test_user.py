from fastapi.testclient import TestClient

def test_create_user(client: TestClient):
    payload = {
        "username": "test",
        "email": "test@gmail.com",
        "password": "12345",
    }
    response = client.post("/user", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert data["journal_entries"] == []


def test_login_user(client: TestClient, seed_user):
    payload = {"email": seed_user.email, "password": "secret"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_user(client: TestClient, seed_user, auth_headers):
    response = client.get(f"/user/{seed_user.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == seed_user.username
    assert data["email"] == seed_user.email
    assert data["journal_entries"] == []