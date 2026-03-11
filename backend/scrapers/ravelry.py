import json

import httpx
from bs4 import BeautifulSoup

from backend.scrapers.schemas import ScrapedPattern


def parse_ravelry(html: str, url: str) -> ScrapedPattern:
    """Parse a Ravelry pattern page HTML into ScrapedPattern."""
    soup = BeautifulSoup(html, "html.parser")

    # Pattern name from LD+JSON or og:title meta tag
    name = None
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and "name" in data:
                name = data["name"]
                break
        except (json.JSONDecodeError, TypeError):
            continue
    if not name:
        meta = soup.find("meta", property="og:title")
        if meta and meta.get("content"):
            # "Skyler pattern by Quail Studio" -> "Skyler"
            name = meta["content"].split(" pattern by ")[0]

    # Author from designer link
    author = None
    for a in soup.find_all("a", href=lambda h: h and "/designers/" in h):
        text = a.get_text(strip=True)
        if text and text.lower() != "designers" and "see them" not in text.lower():
            author = text
            break

    # Yarn weight and suggested yarn from label/value pairs
    yarn_weight = None
    suggested_yarn = None
    for label in soup.find_all("label", class_="core_item_content__label"):
        label_text = label.get_text(strip=True).lower()
        value_div = label.find_next_sibling("div", class_="value")
        if not value_div:
            # Try next sibling regardless of class
            value_div = label.find_next("div", class_="value")
        if not value_div:
            continue
        if "yarn weight" in label_text:
            yarn_weight = value_div.get_text(strip=True)
        elif "yarn" in label_text:
            yarn_link = value_div.find("a")
            if yarn_link:
                suggested_yarn = yarn_link.get_text(strip=True)
            else:
                suggested_yarn = value_div.get_text(strip=True)

    # Fall back to dt/dd pairs if label/value didn't work
    if not yarn_weight or not suggested_yarn:
        for dt in soup.find_all("dt"):
            label_text = dt.get_text(strip=True).lower()
            dd = dt.find_next_sibling("dd")
            if not dd:
                continue
            if "weight" in label_text and not yarn_weight:
                yarn_weight = dd.get_text(strip=True)
            elif "yarn" in label_text and not suggested_yarn:
                yarn_link = dd.find("a")
                if yarn_link:
                    suggested_yarn = yarn_link.get_text(strip=True)
                else:
                    suggested_yarn = dd.get_text(strip=True)

    # Also check for suggested yarn in a link with class 'fn'
    if not suggested_yarn:
        fn_link = soup.find("a", class_="fn")
        if fn_link:
            suggested_yarn = fn_link.get_text(strip=True)

    # Image URL from LD+JSON
    image_url = None
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and "image" in data:
                img = data["image"]
                if isinstance(img, list) and img:
                    image_url = img[0]
                elif isinstance(img, str):
                    image_url = img
                break
        except (json.JSONDecodeError, TypeError):
            continue
    if not image_url:
        img = soup.find("img", src=lambda s: s and "ravelrycache" in s and "uploads/" in s)
        if img:
            image_url = img["src"]

    return ScrapedPattern(
        name=name,
        author=author,
        suggested_yarn=suggested_yarn,
        yarn_weight=yarn_weight,
        image_url=image_url,
        source_url=url,
    )


def scrape_ravelry(url: str) -> ScrapedPattern:
    """Fetch and parse a Ravelry pattern page."""
    response = httpx.get(
        url,
        follow_redirects=True,
        timeout=15.0,
        headers={"User-Agent": "WoolStashTracker/1.0"},
    )
    response.raise_for_status()
    return parse_ravelry(response.text, url)
