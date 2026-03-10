import pytest
from backend.tests.test_yarns_list import _create_yarn


def test_stats_empty(client):
    response = client.get("/api/yarns/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_yarns"] == 0
    assert data["total_estimated_metres"] == 0
    assert data["by_weight"] == {}
    assert data["by_fibre"] == {}


def test_stats_with_data(client):
    # 2 DK yarns, 1 Aran yarn
    # DK yarn 1: metres_per_ball=100, full_balls=2, part_balls=0 -> 200m
    _create_yarn(client, name="DK Yarn 1", weight="DK", fibre="Wool", metres_per_ball=100, full_balls=2, part_balls=0)
    # DK yarn 2: metres_per_ball=100, full_balls=1, part_balls=0 -> 100m
    _create_yarn(client, name="DK Yarn 2", weight="DK", fibre="Cotton", metres_per_ball=100, full_balls=1, part_balls=0)
    # Aran yarn: metres_per_ball=100, full_balls=2, part_balls=0 -> 200m
    _create_yarn(client, name="Aran Yarn", weight="Aran", fibre="Wool", metres_per_ball=100, full_balls=2, part_balls=0)
    # total = 200 + 100 + 200 = 500

    response = client.get("/api/yarns/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_yarns"] == 3
    assert data["total_estimated_metres"] == 500
    assert data["by_weight"] == {"DK": 2, "Aran": 1}
    assert data["by_fibre"] == {"Wool": 2, "Cotton": 1}
