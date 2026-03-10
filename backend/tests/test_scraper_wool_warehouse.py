from pathlib import Path

from backend.scrapers.wool_warehouse import parse_wool_warehouse

FIXTURE = Path(__file__).parent / "fixtures" / "wool_warehouse.html"
URL = "https://www.woolwarehouse.co.uk/yarn/drops-air-all-colours"


def test_parse_name():
    result = parse_wool_warehouse(FIXTURE.read_text(), URL)
    assert "Drops" in result.name
    assert "Air" in result.name
    assert "All Colours" not in result.name


def test_parse_weight():
    result = parse_wool_warehouse(FIXTURE.read_text(), URL)
    assert result.weight == "Aran"


def test_parse_fibre():
    result = parse_wool_warehouse(FIXTURE.read_text(), URL)
    assert result.fibre is not None
    assert "Alpaca" in result.fibre


def test_parse_metres():
    result = parse_wool_warehouse(FIXTURE.read_text(), URL)
    assert result.metres_per_ball == 150


def test_parse_ball_weight():
    result = parse_wool_warehouse(FIXTURE.read_text(), URL)
    assert result.ball_weight_grams == 50


def test_parse_needle_size():
    result = parse_wool_warehouse(FIXTURE.read_text(), URL)
    assert result.needle_size_mm == 5.0


def test_parse_tension():
    result = parse_wool_warehouse(FIXTURE.read_text(), URL)
    assert result.tension is not None
    assert "17" in result.tension


def test_parse_colourways():
    result = parse_wool_warehouse(FIXTURE.read_text(), URL)
    assert len(result.colourways) > 0
    names = [c.name for c in result.colourways]
    assert any("Pearl Grey" in n for n in names)


def test_parse_image():
    result = parse_wool_warehouse(FIXTURE.read_text(), URL)
    assert result.image_url is not None
    assert result.image_url.startswith("http")


def test_source_url():
    result = parse_wool_warehouse(FIXTURE.read_text(), URL)
    assert result.source_url == URL
