import re

import httpx
from bs4 import BeautifulSoup

from backend.scrapers.schemas import ScrapedColourway, ScrapedYarn


def _get_property(soup, testid: str) -> str | None:
    """Extract a value from a LoveCrafts data-testid property container."""
    container = soup.find("div", attrs={"data-testid": testid})
    if not container:
        return None
    dd = container.find("dd")
    if dd:
        return dd.get_text(strip=True)
    return None


def parse_lovecrafts(html: str, url: str) -> ScrapedYarn:
    """Parse a LoveCrafts product page HTML into ScrapedYarn."""
    soup = BeautifulSoup(html, "html.parser")

    # Product name from h1
    name = ""
    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(strip=True)

    # Brand from data-testid="Brand"
    brand = None
    brand_container = soup.find("div", attrs={"data-testid": "Brand"})
    if brand_container:
        dd = brand_container.find("dd")
        if dd:
            a = dd.find("a")
            brand = a.get_text(strip=True) if a else dd.get_text(strip=True)

    # Prepend brand to name if not already included
    if brand and not name.lower().startswith(brand.lower()):
        name = f"{brand} {name}"

    # Fibre composition
    fibre = None
    blend_text = _get_property(soup, "Blend")
    if blend_text:
        fibre = blend_text

    # Metres per ball
    metres_per_ball = None
    length_text = _get_property(soup, "Length")
    if length_text:
        m = re.search(r"(\d+)\s*m", length_text)
        if m:
            metres_per_ball = int(m.group(1))

    # Ball weight
    ball_weight_grams = None
    weight_text = _get_property(soup, "Net Weight")
    if weight_text:
        m = re.search(r"(\d+)\s*g", weight_text)
        if m:
            ball_weight_grams = int(m.group(1))

    # Needle size - take the first (smallest) value
    needle_size_mm = None
    needle_text = _get_property(soup, "Needles")
    if needle_text:
        m = re.search(r"([\d.]+)\s*mm", needle_text)
        if m:
            needle_size_mm = float(m.group(1))

    # Tension
    tension = None
    tension_text = _get_property(soup, "Tension")
    if tension_text:
        sts_match = re.search(r"(\d+)\s*stitch", tension_text, re.IGNORECASE)
        rows_match = re.search(r"(\d+)\s*row", tension_text, re.IGNORECASE)
        if sts_match and rows_match:
            tension = f"{sts_match.group(1)} sts × {rows_match.group(1)} rows / 10cm"
        elif sts_match:
            tension = f"{sts_match.group(1)} sts / 10cm"

    # Colourways from variant grid images
    colourways: list[ScrapedColourway] = []
    variant_labels = soup.find_all("label", class_=re.compile(r"grid-variants__variant"))
    for label in variant_labels:
        img = label.find("img")
        if not img or not img.get("alt"):
            continue
        alt = img.get("alt", "")
        img_src = img.get("src")
        # Parse "Beach (00002)" → name="Beach", shade_number="00002"
        code_match = re.match(r"^(.+?)\s*\((\d+)\)$", alt)
        if code_match:
            colourways.append(ScrapedColourway(
                name=code_match.group(1).strip(),
                shade_number=code_match.group(2),
                image_url=img_src,
            ))
        else:
            colourways.append(ScrapedColourway(
                name=alt.strip(), shade_number=None, image_url=img_src,
            ))

    # Main product image from og:image meta tag
    image_url = None
    og_img = soup.find("meta", attrs={"name": "og:image"}) or soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        image_url = og_img["content"]

    return ScrapedYarn(
        name=name,
        weight=None,  # LoveCrafts weight labels don't match our enum reliably
        fibre=fibre,
        metres_per_ball=metres_per_ball,
        ball_weight_grams=ball_weight_grams,
        needle_size_mm=needle_size_mm,
        tension=tension,
        image_url=image_url,
        colourways=colourways,
        source_url=url,
    )


def scrape_lovecrafts(url: str) -> ScrapedYarn:
    """Fetch and parse a LoveCrafts product page."""
    response = httpx.get(
        url, follow_redirects=True, timeout=15.0,
        headers={"User-Agent": "WoolStashTracker/1.0"},
    )
    response.raise_for_status()
    return parse_lovecrafts(response.text, url)
