from fastapi.testclient import TestClient
def test_create_journal_entry(client : TestClient, seed_user, auth_headers):
    payload = {"title": "Test Title", "content": "Test Content"}
    res = client.post(f"/journal/{seed_user.id}", json=payload, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["title"] == "Test Title"
    assert res.json()["content"] == "Test Content"
    assert res.json()["user_id"] == seed_user.id


def test_get_journal_entries(client : TestClient, seed_user, auth_headers):
    payload = {"title": "Test Title", "content": "Test Content"}
    create_res = client.post(f"/journal/{seed_user.id}", json=payload, headers=auth_headers)
    assert create_res.status_code == 200

    get_res = client.get(f"/journal?user_id={seed_user.id}", headers=auth_headers)
    assert get_res.status_code == 200
    entries = get_res.json()
    assert len(entries) >= 1
    assert any(
        entry["title"] == "Test Title"
        and entry["content"] == "Test Content"
        and entry["user_id"] == seed_user.id
        for entry in entries
    )