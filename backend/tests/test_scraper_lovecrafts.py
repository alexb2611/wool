from pathlib import Path

from backend.scrapers.lovecrafts import parse_lovecrafts

FIXTURE = Path(__file__).parent / "fixtures" / "lovecrafts.html"
URL = "https://www.lovecrafts.com/en-gb/p/rowan-four-seasons"


def test_parse_name():
    result = parse_lovecrafts(FIXTURE.read_text(), URL)
    assert "Rowan" in result.name
    assert "Four Seasons" in result.name


def test_parse_fibre():
    result = parse_lovecrafts(FIXTURE.read_text(), URL)
    assert result.fibre is not None
    assert "Cotton" in result.fibre


def test_parse_metres():
    result = parse_lovecrafts(FIXTURE.read_text(), URL)
    assert result.metres_per_ball == 75


def test_parse_ball_weight():
    result = parse_lovecrafts(FIXTURE.read_text(), URL)
    assert result.ball_weight_grams == 50


def test_parse_needle_size():
    result = parse_lovecrafts(FIXTURE.read_text(), URL)
    assert result.needle_size_mm is not None
    assert result.needle_size_mm == 4.5


def test_parse_tension():
    result = parse_lovecrafts(FIXTURE.read_text(), URL)
    assert result.tension is not None
    assert "16" in result.tension


def test_parse_colourways():
    result = parse_lovecrafts(FIXTURE.read_text(), URL)
    assert len(result.colourways) > 0
    names = [c.name for c in result.colourways]
    assert any("Beach" in n for n in names)


def test_parse_image():
    result = parse_lovecrafts(FIXTURE.read_text(), URL)
    assert result.image_url is not None
    assert result.image_url.startswith("http")


def test_source_url():
    result = parse_lovecrafts(FIXTURE.read_text(), URL)
    assert result.source_url == URL
