from pathlib import Path
from backend.scrapers.ravelry import parse_ravelry

FIXTURE = Path(__file__).parent / "fixtures" / "ravelry_pattern.html"
URL = "https://www.ravelry.com/patterns/library/skyler-5"


def test_parse_name():
    result = parse_ravelry(FIXTURE.read_text(), URL)
    assert result.name == "Skyler"


def test_parse_author():
    result = parse_ravelry(FIXTURE.read_text(), URL)
    assert result.author == "Quail Studio"


def test_parse_suggested_yarn():
    result = parse_ravelry(FIXTURE.read_text(), URL)
    assert result.suggested_yarn is not None
    assert "Summerlite" in result.suggested_yarn


def test_parse_yarn_weight():
    result = parse_ravelry(FIXTURE.read_text(), URL)
    assert result.yarn_weight is not None
    assert "DK" in result.yarn_weight


def test_parse_image_url():
    result = parse_ravelry(FIXTURE.read_text(), URL)
    assert result.image_url is not None
    assert result.image_url.startswith("http")


def test_source_url():
    result = parse_ravelry(FIXTURE.read_text(), URL)
    assert result.source_url == URL
