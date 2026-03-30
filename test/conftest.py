import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import SessionLocal
from main import app
from models.user import Users
from security import hash_password


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seed_user(db):
    suffix = uuid4().hex[:8]
    user = Users(
        username=f"testuser_{suffix}",
        email=f"testuser_{suffix}@example.com",
        password=hash_password("secret"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient, seed_user):
    login_response = client.post(
        "/auth/login",
        json={"email": seed_user.email, "password": "secret"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
