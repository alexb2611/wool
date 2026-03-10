import pytest
from backend.seed_data import SEED_YARNS


def test_seed_yarns(client):
    response = client.post("/api/yarns/seed")
    assert response.status_code == 200
    data = response.json()
    assert data["created"] == len(SEED_YARNS)
    assert data["skipped"] == 0

    list_response = client.get(f"/api/yarns/?limit={len(SEED_YARNS) + 10}")
    assert list_response.status_code == 200
    assert len(list_response.json()) == len(SEED_YARNS)


def test_seed_yarns_idempotent(client):
    # First seed
    client.post("/api/yarns/seed")
    # Second seed - all should be skipped
    response = client.post("/api/yarns/seed")
    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 0
    assert data["skipped"] == len(SEED_YARNS)
