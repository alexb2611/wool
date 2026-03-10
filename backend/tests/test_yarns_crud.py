import pytest


def test_create_yarn(client):
    payload = {
        "name": "Drops Alpaca",
        "weight": "4 Ply",
        "colour": "Light Sea Green",
        "fibre": "Alpaca",
        "metres_per_ball": 167,
        "full_balls": 1,
        "part_balls": 0,
        "extra_metres": None,
        "intended_project": None,
        "notes": None,
    }
    response = client.post("/api/yarns/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Drops Alpaca"
    assert data["weight"] == "4 Ply"
    assert data["colour"] == "Light Sea Green"
    assert data["fibre"] == "Alpaca"
    assert data["metres_per_ball"] == 167
    assert data["full_balls"] == 1
    assert data["part_balls"] == 0
    assert data["extra_metres"] is None
    assert data["estimated_total_metres"] == 167  # 1*167 = 167
    assert data["intended_project"] is None
    assert data["notes"] is None
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_yarn_minimal(client):
    payload = {
        "name": "Mystery Yarn",
        "weight": "DK",
        "colour": "Blue",
        "fibre": "Wool",
    }
    response = client.post("/api/yarns/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["full_balls"] == 0
    assert data["part_balls"] == 0
    assert data["metres_per_ball"] is None
    assert data["estimated_total_metres"] is None


def test_create_yarn_with_extra_metres(client):
    payload = {
        "name": "Test Yarn",
        "weight": "Aran",
        "colour": "Green",
        "fibre": "Cotton",
        "metres_per_ball": 100,
        "full_balls": 2,
        "part_balls": 3,
        "extra_metres": 30,
    }
    response = client.post("/api/yarns/", json=payload)
    assert response.status_code == 201
    data = response.json()
    # 2*100 + 3*100*0.5 + 30 = 200 + 150 + 30 = 380
    assert data["estimated_total_metres"] == 380


# --- helpers and tests for Task 7 ---

def _create_yarn(client, **overrides):
    payload = {
        "name": "Test Yarn",
        "weight": "DK",
        "colour": "Blue",
        "fibre": "Wool",
        "metres_per_ball": 100,
        "full_balls": 2,
        "part_balls": 0,
        **overrides,
    }
    response = client.post("/api/yarns/", json=payload)
    assert response.status_code == 201
    return response.json()


def test_get_yarn(client):
    created = _create_yarn(client)
    yarn_id = created["id"]
    response = client.get(f"/api/yarns/{yarn_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == yarn_id
    assert data["name"] == "Test Yarn"


def test_get_yarn_not_found(client):
    response = client.get("/api/yarns/99999")
    assert response.status_code == 404


def test_update_yarn(client):
    created = _create_yarn(client, full_balls=2, metres_per_ball=100)
    yarn_id = created["id"]
    update_payload = {"name": "Updated Yarn", "full_balls": 5}
    response = client.put(f"/api/yarns/{yarn_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Yarn"
    assert data["full_balls"] == 5
    # unchanged fields
    assert data["colour"] == "Blue"
    assert data["fibre"] == "Wool"
    # recomputed: 5*100 + 0*100*0.5 = 500
    assert data["estimated_total_metres"] == 500


def test_update_yarn_not_found(client):
    response = client.put("/api/yarns/99999", json={"name": "Nope"})
    assert response.status_code == 404


def test_delete_yarn(client):
    created = _create_yarn(client)
    yarn_id = created["id"]
    response = client.delete(f"/api/yarns/{yarn_id}")
    assert response.status_code == 204
    # verify gone
    response = client.get(f"/api/yarns/{yarn_id}")
    assert response.status_code == 404


def test_delete_yarn_not_found(client):
    response = client.delete("/api/yarns/99999")
    assert response.status_code == 404
