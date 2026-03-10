import pytest


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


def test_list_yarns_empty(client):
    response = client.get("/api/yarns/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_yarns(client):
    _create_yarn(client, name="Yarn A")
    _create_yarn(client, name="Yarn B")
    response = client.get("/api/yarns/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_yarns_search(client):
    _create_yarn(client, name="Alpaca Delight")
    _create_yarn(client, name="Cotton Candy")
    response = client.get("/api/yarns/?q=alpaca")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Alpaca Delight"


def test_list_yarns_search_colour(client):
    _create_yarn(client, name="Yarn A", colour="Turquoise")
    _create_yarn(client, name="Yarn B", colour="Red")
    response = client.get("/api/yarns/?q=turquoise")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["colour"] == "Turquoise"


def test_list_yarns_search_notes(client):
    _create_yarn(client, name="Yarn A", notes="Left over from baby blanket")
    _create_yarn(client, name="Yarn B", notes="From a shop in France")
    response = client.get("/api/yarns/?q=baby")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["notes"] == "Left over from baby blanket"


def test_list_yarns_search_intended_project(client):
    _create_yarn(client, name="Yarn A", intended_project="Summer top")
    _create_yarn(client, name="Yarn B", intended_project="Winter scarf")
    response = client.get("/api/yarns/?q=summer")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["intended_project"] == "Summer top"


def test_list_yarns_filter_weight(client):
    _create_yarn(client, name="DK Yarn", weight="DK")
    _create_yarn(client, name="Aran Yarn", weight="Aran")
    response = client.get("/api/yarns/?weight=DK")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["weight"] == "DK"


def test_list_yarns_filter_fibre(client):
    _create_yarn(client, name="Wool Yarn", fibre="Merino Wool")
    _create_yarn(client, name="Cotton Yarn", fibre="Cotton")
    response = client.get("/api/yarns/?fibre=merino")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["fibre"] == "Merino Wool"


def test_list_yarns_filter_has_project(client):
    _create_yarn(client, name="With Project", intended_project="A nice top")
    _create_yarn(client, name="Without Project")
    response_true = client.get("/api/yarns/?has_project=true")
    assert response_true.status_code == 200
    true_data = response_true.json()
    assert len(true_data) == 1
    assert true_data[0]["name"] == "With Project"

    response_false = client.get("/api/yarns/?has_project=false")
    assert response_false.status_code == 200
    false_data = response_false.json()
    assert len(false_data) == 1
    assert false_data[0]["name"] == "Without Project"


def test_list_yarns_sort(client):
    _create_yarn(client, name="Zebra Yarn")
    _create_yarn(client, name="Apple Yarn")
    _create_yarn(client, name="Mango Yarn")

    response_asc = client.get("/api/yarns/?sort_by=name&sort_dir=asc")
    assert response_asc.status_code == 200
    names_asc = [y["name"] for y in response_asc.json()]
    assert names_asc == sorted(names_asc)

    response_desc = client.get("/api/yarns/?sort_by=name&sort_dir=desc")
    assert response_desc.status_code == 200
    names_desc = [y["name"] for y in response_desc.json()]
    assert names_desc == sorted(names_desc, reverse=True)


def test_list_yarns_pagination(client):
    for i in range(5):
        _create_yarn(client, name=f"Yarn {i:02d}")

    response = client.get("/api/yarns/?limit=2&offset=0&sort_by=name&sort_dir=asc")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Yarn 00"
    assert data[1]["name"] == "Yarn 01"

    response2 = client.get("/api/yarns/?limit=2&offset=2&sort_by=name&sort_dir=asc")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 2
    assert data2[0]["name"] == "Yarn 02"
    assert data2[1]["name"] == "Yarn 03"
