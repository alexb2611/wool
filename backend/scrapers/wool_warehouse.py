import re

import httpx
from bs4 import BeautifulSoup

from backend.scrapers.schemas import ScrapedColourway, ScrapedYarn


def _get_spec(spec_table, label: str) -> str | None:
    """Extract a value from the specs table by its row label."""
    if not spec_table:
        return None
    for row in spec_table.find_all("tr"):
        th = row.find("th")
        if th and label.lower() in th.get_text(strip=True).lower():
            td = row.find("td")
            if td:
                return td.get_text(separator=" ", strip=True)
    return None


def parse_wool_warehouse(html: str, url: str) -> ScrapedYarn:
    """Parse a Wool Warehouse product page HTML into ScrapedYarn."""
    soup = BeautifulSoup(html, "html.parser")

    # Product name from h1 inside div.product-name
    name = ""
    name_div = soup.find("div", class_="product-name")
    if name_div:
        h1 = name_div.find("h1")
        if h1:
            name = h1.get_text(strip=True)
    # Remove " - All Colours" suffix
    name = re.sub(r"\s*-\s*All Colours$", "", name, flags=re.IGNORECASE)

    # Specs from the product-attribute-specs-table
    spec_table = soup.find("table", id="product-attribute-specs-table")

    # Metres per ball
    metres_per_ball = None
    length_text = _get_spec(spec_table, "Length")
    if length_text:
        m = re.search(r"(\d+)\s*metres?", length_text, re.IGNORECASE)
        if m:
            metres_per_ball = int(m.group(1))

    # Ball weight
    ball_weight_grams = None
    weight_text = _get_spec(spec_table, "Ball Weight")
    if weight_text:
        m = re.search(r"(\d+)\s*g", weight_text)
        if m:
            ball_weight_grams = int(m.group(1))

    # Needle size
    needle_size_mm = None
    needle_text = _get_spec(spec_table, "Needle Size")
    if needle_text:
        m = re.search(r"([\d.]+)\s*mm", needle_text)
        if m:
            needle_size_mm = float(m.group(1))

    # Tension
    tension = None
    tension_text = _get_spec(spec_table, "Tension")
    if tension_text:
        sts_match = re.search(r"(\d+)\s*stitch", tension_text, re.IGNORECASE)
        rows_match = re.search(r"(\d+)\s*row", tension_text, re.IGNORECASE)
        if sts_match and rows_match:
            tension = f"{sts_match.group(1)} sts × {rows_match.group(1)} rows / 10cm"
        elif sts_match:
            tension = f"{sts_match.group(1)} sts / 10cm"

    # Fibre composition from "Blend" row
    fibre = None
    blend_text = _get_spec(spec_table, "Blend")
    if blend_text:
        # Format: "28% Polyamide 7% Wool 65% Alpaca" (br tags become spaces)
        # Reformat to "65% Alpaca/28% Polyamide/7% Wool" sorted by percentage desc
        parts = re.findall(r"(\d+)%\s*(\w+)", blend_text)
        if parts:
            sorted_parts = sorted(parts, key=lambda p: int(p[0]), reverse=True)
            fibre = "/".join(f"{name}" for _, name in sorted_parts)

    # Yarn weight category from specs table
    weight = _get_spec(spec_table, "Yarn Weight")

    # Colourways from dropdown
    colourways: list[ScrapedColourway] = []
    select = soup.find("select", id="subprod_colourdropdown")
    if select:
        for option in select.find_all("option"):
            text = option.get_text(strip=True)
            if not text or text.lower() in ("all colours", ""):
                continue
            shade_match = re.match(r"^(\d+)\s+(.+)$", text)
            if shade_match:
                colourways.append(ScrapedColourway(
                    name=shade_match.group(2).strip(),
                    shade_number=shade_match.group(1),
                    image_url=None,
                ))
            else:
                colourways.append(ScrapedColourway(
                    name=text, shade_number=None, image_url=None,
                ))

    # Main product image from div#imageGallery
    image_url = None
    gallery = soup.find("div", id="imageGallery")
    if gallery:
        img = gallery.find("img")
        if img and img.get("src"):
            image_url = img["src"]

    return ScrapedYarn(
        name=name,
        weight=weight,
        fibre=fibre,
        metres_per_ball=metres_per_ball,
        ball_weight_grams=ball_weight_grams,
        needle_size_mm=needle_size_mm,
        tension=tension,
        image_url=image_url,
        colourways=colourways,
        source_url=url,
    )


def scrape_wool_warehouse(url: str) -> ScrapedYarn:
    """Fetch and parse a Wool Warehouse product page."""
    response = httpx.get(
        url, follow_redirects=True, timeout=15.0,
        headers={"User-Agent": "WoolStashTracker/1.0"},
    )
    response.raise_for_status()
    return parse_wool_warehouse(response.text, url)
