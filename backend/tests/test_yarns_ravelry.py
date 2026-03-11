from unittest.mock import patch

from backend.scrapers.schemas import ScrapedPattern


MOCK_PATTERN = ScrapedPattern(
    name="Skyler", author="Quail Studio",
    suggested_yarn="Rowan Summerlite DK",
    yarn_weight="DK / 8 ply",
    image_url="https://example.com/image.jpg",
    source_url="https://www.ravelry.com/patterns/library/skyler-5",
)

MOCK_PATTERN_2 = ScrapedPattern(
    name="Another Pattern", author="Other Designer",
    suggested_yarn="Some Yarn",
    yarn_weight="Aran",
    image_url="https://example.com/image2.jpg",
    source_url="https://www.ravelry.com/patterns/library/another-pattern",
)


def _create_yarn(client, **overrides):
    payload = {
        "name": "Test Yarn",
        "weight": "DK",
        "colour": "Blue",
        "fibre": "Wool",
        **overrides,
    }
    return client.post("/api/yarns/", json=payload)


def test_create_yarn_rejects_non_ravelry_url(client):
    response = _create_yarn(client, ravelry_url="https://example.com/pattern")
    assert response.status_code == 422
    assert "Ravelry" in response.json()["detail"]


def test_create_yarn_accepts_valid_ravelry_url(client):
    with patch("backend.routers.yarns.scrape_ravelry", return_value=MOCK_PATTERN), \
         patch("backend.routers.yarns._download_image", return_value="abc123.jpg"):
        response = _create_yarn(
            client,
            ravelry_url="https://www.ravelry.com/patterns/library/skyler-5",
        )
    assert response.status_code == 201
    data = response.json()
    assert data["ravelry_url"] == "https://www.ravelry.com/patterns/library/skyler-5"
    assert data["pattern_name"] == "Skyler"
    assert data["pattern_author"] == "Quail Studio"
    assert data["pattern_suggested_yarn"] == "Rowan Summerlite DK"
    assert data["pattern_yarn_weight"] == "DK / 8 ply"
    assert data["pattern_image_filename"] == "abc123.jpg"
    assert data["pattern_image_url"] == "/api/pattern-images/abc123.jpg"


def test_create_yarn_survives_scrape_failure(client):
    with patch("backend.routers.yarns.scrape_ravelry", side_effect=Exception("Network error")):
        response = _create_yarn(
            client,
            ravelry_url="https://www.ravelry.com/patterns/library/skyler-5",
        )
    assert response.status_code == 201
    data = response.json()
    assert data["ravelry_url"] == "https://www.ravelry.com/patterns/library/skyler-5"
    assert data["pattern_name"] is None
    assert data["pattern_image_url"] is None


def test_update_yarn_clears_pattern_fields(client):
    with patch("backend.routers.yarns.scrape_ravelry", return_value=MOCK_PATTERN), \
         patch("backend.routers.yarns._download_image", return_value="cleanup_test.jpg"):
        resp = _create_yarn(
            client,
            ravelry_url="https://www.ravelry.com/patterns/library/skyler-5",
        )
    yarn_id = resp.json()["id"]

    with patch("backend.routers.yarns._delete_pattern_image") as mock_delete:
        resp = client.put(f"/api/yarns/{yarn_id}", json={"ravelry_url": None})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ravelry_url"] is None
    assert data["pattern_name"] is None
    assert data["pattern_author"] is None
    assert data["pattern_image_url"] is None
    mock_delete.assert_called_once_with("cleanup_test.jpg")


def test_update_yarn_changes_pattern(client):
    with patch("backend.routers.yarns.scrape_ravelry", return_value=MOCK_PATTERN), \
         patch("backend.routers.yarns._download_image", return_value="old_image.jpg"):
        resp = _create_yarn(
            client,
            ravelry_url="https://www.ravelry.com/patterns/library/skyler-5",
        )
    yarn_id = resp.json()["id"]

    with patch("backend.routers.yarns.scrape_ravelry", return_value=MOCK_PATTERN_2), \
         patch("backend.routers.yarns._download_image", return_value="new_image.jpg"), \
         patch("backend.routers.yarns._delete_pattern_image") as mock_delete:
        resp = client.put(f"/api/yarns/{yarn_id}", json={
            "ravelry_url": "https://www.ravelry.com/patterns/library/another-pattern",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["pattern_name"] == "Another Pattern"
    assert data["pattern_author"] == "Other Designer"
    assert data["pattern_image_filename"] == "new_image.jpg"
    mock_delete.assert_called_once_with("old_image.jpg")


def test_delete_yarn_cleans_up_pattern_image(client):
    with patch("backend.routers.yarns.scrape_ravelry", return_value=MOCK_PATTERN), \
         patch("backend.routers.yarns._download_image", return_value="to_delete.jpg"):
        resp = _create_yarn(
            client,
            ravelry_url="https://www.ravelry.com/patterns/library/skyler-5",
        )
    yarn_id = resp.json()["id"]

    with patch("backend.routers.yarns._delete_pattern_image") as mock_delete:
        resp = client.delete(f"/api/yarns/{yarn_id}")
    assert resp.status_code == 204
    mock_delete.assert_called_once_with("to_delete.jpg")
