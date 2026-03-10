from unittest.mock import patch

from backend.scrapers.schemas import ScrapedColourway, ScrapedYarn


def test_scrape_unsupported_url(client):
    response = client.post("/api/yarns/scrape", json={
        "url": "https://www.amazon.co.uk/some-yarn"
    })
    assert response.status_code == 400
    assert "supported" in response.json()["detail"].lower()


def test_scrape_supported_url(client):
    mock_result = ScrapedYarn(
        name="Test Yarn",
        weight="DK",
        fibre="Wool",
        metres_per_ball=100,
        ball_weight_grams=50,
        needle_size_mm=4.0,
        tension="22 sts × 30 rows / 10cm",
        image_url="https://example.com/img.jpg",
        colourways=[
            ScrapedColourway(name="Red", shade_number="01", image_url=None),
        ],
        source_url="https://www.woolwarehouse.co.uk/yarn/test",
    )
    with patch("backend.routers.yarns.get_scraper") as mock_get:
        mock_get.return_value = lambda url: mock_result
        response = client.post("/api/yarns/scrape", json={
            "url": "https://www.woolwarehouse.co.uk/yarn/test"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Yarn"
    assert data["metres_per_ball"] == 100
    assert len(data["colourways"]) == 1
    assert data["colourways"][0]["name"] == "Red"


def test_scrape_site_error(client):
    with patch("backend.routers.yarns.get_scraper") as mock_get:
        mock_get.return_value = lambda url: (_ for _ in ()).throw(Exception("Connection failed"))
        response = client.post("/api/yarns/scrape", json={
            "url": "https://www.woolwarehouse.co.uk/yarn/test"
        })
    assert response.status_code == 502
