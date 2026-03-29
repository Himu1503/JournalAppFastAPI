from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_create_journal_entry(client : TestClient, db: Session, seed_user ):
    payload = {"title": "Test Title", "content": "Test Content", "user_id": seed_user.id}
    res =client.post("/journal", json=payload)
    assert res.status_code == 200
    assert res.json()["title"] == "Test Title"
    assert res.json()["content"] == "Test Content"
    assert res.json()["user_id"] == seed_user.id


def test_get_journal_entries(client : TestClient, db: Session, seed_user):
    payload = {"title": "Test Title", "content": "Test Content", "user_id": seed_user.id}
    create_res = client.post("/journal", json=payload)
    assert create_res.status_code == 200

    get_res = client.get(f"/journal?user_id={seed_user.id}")
    assert get_res.status_code == 200
    entries = get_res.json()
    assert len(entries) >= 1
    assert any(
        entry["title"] == "Test Title"
        and entry["content"] == "Test Content"
        and entry["user_id"] == seed_user.id
        for entry in entries
    )