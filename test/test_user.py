from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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


def test_get_user(client: TestClient, db: Session, seed_user):
    response = client.get(f"/user/{seed_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == seed_user.username
    assert data["email"] == seed_user.email
    assert data["journal_entries"] == []