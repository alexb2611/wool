# URL Import Feature Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a URL import feature that scrapes yarn data from woolwarehouse.co.uk and lovecrafts.com product pages, auto-populating form fields including new fields for needle size, tension, ball weight, and product image.

**Architecture:** Backend scrapers (one per site) behind a `POST /api/yarns/scrape` endpoint. Frontend adds a URL input to the yarn form that fetches scraped data and populates fields. Four new nullable columns on the Yarn model with Alembic migration.

**Tech Stack:** httpx + beautifulsoup4 for scraping, existing FastAPI/React stack for the rest.

**Spec:** `docs/superpowers/specs/2026-03-10-url-import-design.md`

---

## File Structure

```
backend/
├── models.py                      # Modify: add 4 new columns
├── schemas.py                     # Modify: add new fields + scrape schemas
├── requirements.txt               # Modify: add httpx, beautifulsoup4
├── routers/yarns.py               # Modify: add POST /scrape endpoint
├── scrapers/
│   ├── __init__.py                # Scraper registry (SCRAPERS dict)
│   ├── schemas.py                 # ScrapedYarn, ScrapedColourway, ScrapeRequest
│   ├── wool_warehouse.py          # Wool Warehouse scraper
│   └── lovecrafts.py              # LoveCrafts scraper
├── tests/
│   ├── fixtures/
│   │   ├── wool_warehouse.html    # Saved HTML fixture
│   │   └── lovecrafts.html        # Saved HTML fixture
│   ├── test_yarns_crud.py         # Modify: add tests for new fields
│   ├── test_scraper_wool_warehouse.py  # Scraper unit tests
│   ├── test_scraper_lovecrafts.py      # Scraper unit tests
│   └── test_scrape_endpoint.py         # Endpoint tests
frontend/src/
├── types.ts                       # Modify: add new fields + scrape types
├── api/yarns.ts                   # Modify: add scrapeYarn function
├── hooks/use-yarns.ts             # Modify: add useScrapeYarn hook
├── components/
│   ├── yarn-form.tsx              # Modify: add URL input, new fields, image preview
│   └── yarn-table.tsx             # Modify: show image + new fields in expanded row
```

---

## Chunk 1: Backend Schema Changes

### Task 1: Add new columns to Yarn model

**Files:**
- Modify: `backend/models.py`

- [ ] **Step 1: Add four new columns to the Yarn model**

Add after line 28 (`estimated_total_metres`):

```python
needle_size_mm = Column(Float, nullable=True)
tension = Column(String, nullable=True)
ball_weight_grams = Column(Integer, nullable=True)
image_url = Column(String, nullable=True)
```

Also add `Float` to the imports from `sqlalchemy`.

- [ ] **Step 2: Create Alembic migration**

```bash
cd backend
source .venv/bin/activate
alembic revision --autogenerate -m "add needle_size tension ball_weight image_url to yarns"
```

Verify the generated migration uses `batch_alter_table` (SQLite requirement).

- [ ] **Step 3: Run migration**

```bash
alembic upgrade head
```

- [ ] **Step 4: Commit**

```bash
git add backend/models.py backend/alembic/versions/
git commit -m "Add needle_size_mm, tension, ball_weight_grams, image_url columns"
```

---

### Task 2: Update Pydantic schemas

**Files:**
- Modify: `backend/schemas.py`

- [ ] **Step 1: Add new fields to YarnCreate, YarnUpdate, and YarnResponse**

Add to `YarnCreate` (after `notes`):
```python
needle_size_mm: float | None = None
tension: str | None = None
ball_weight_grams: int | None = None
image_url: str | None = None
```

Add same fields to `YarnUpdate` (all optional, same types).

Add to `YarnResponse` (after `notes`, before `created_at`):
```python
needle_size_mm: float | None
tension: str | None
ball_weight_grams: int | None
image_url: str | None
```

- [ ] **Step 2: Verify imports work**

```bash
python -c "from backend.schemas import YarnCreate, YarnResponse; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend/schemas.py
git commit -m "Add new fields to Pydantic schemas"
```

---

### Task 3: Update CRUD tests for new fields

**Files:**
- Modify: `backend/tests/test_yarns_crud.py`

- [ ] **Step 1: Add test for creating yarn with new fields**

Append to `test_yarns_crud.py`:

```python
def test_create_yarn_with_new_fields(client):
    response = client.post("/api/yarns/", json={
        "name": "Test Yarn",
        "weight": "DK",
        "colour": "Red",
        "fibre": "Wool",
        "needle_size_mm": 4.5,
        "tension": "22 sts × 30 rows / 10cm",
        "ball_weight_grams": 50,
        "image_url": "https://example.com/yarn.jpg",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["needle_size_mm"] == 4.5
    assert data["tension"] == "22 sts × 30 rows / 10cm"
    assert data["ball_weight_grams"] == 50
    assert data["image_url"] == "https://example.com/yarn.jpg"


def test_update_yarn_new_fields(client):
    created = _create_yarn(client)
    response = client.put(f"/api/yarns/{created['id']}", json={
        "needle_size_mm": 5.0,
        "ball_weight_grams": 100,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["needle_size_mm"] == 5.0
    assert data["ball_weight_grams"] == 100
    assert data["name"] == "Test Yarn"  # unchanged
```

- [ ] **Step 2: Run tests**

```bash
python -m pytest backend/tests/test_yarns_crud.py -v
```

Expected: all pass (new fields are nullable, existing tests unaffected).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_yarns_crud.py
git commit -m "Add tests for new yarn fields"
```

---

### Task 4: Update TypeScript types and API client

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api/yarns.ts`
- Modify: `frontend/src/hooks/use-yarns.ts`

- [ ] **Step 1: Add new fields to TypeScript interfaces**

In `types.ts`, add to `Yarn` interface (after `notes`):
```typescript
needle_size_mm: number | null;
tension: string | null;
ball_weight_grams: number | null;
image_url: string | null;
```

Add same fields to `YarnCreate` (optional) and `YarnUpdate` (optional).

Add new types at the end of the file:
```typescript
export interface ScrapedColourway {
  name: string;
  shade_number: string | null;
  image_url: string | null;
}

export interface ScrapedYarn {
  name: string;
  weight: string | null;
  fibre: string | null;
  metres_per_ball: number | null;
  ball_weight_grams: number | null;
  needle_size_mm: number | null;
  tension: string | null;
  image_url: string | null;
  colourways: ScrapedColourway[];
  source_url: string;
}
```

- [ ] **Step 2: Add scrape API function**

Add to `frontend/src/api/yarns.ts`:
```typescript
import type { ..., ScrapedYarn } from "../types";

export function scrapeYarn(url: string): Promise<ScrapedYarn> {
  return request<ScrapedYarn>("/yarns/scrape", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}
```

- [ ] **Step 3: Add TanStack Query hook**

Add to `frontend/src/hooks/use-yarns.ts`:
```typescript
export function useScrapeYarn() {
  return useMutation({
    mutationFn: (url: string) => yarnsApi.scrapeYarn(url),
  });
}
```

- [ ] **Step 4: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types.ts frontend/src/api/yarns.ts frontend/src/hooks/use-yarns.ts
git commit -m "Add scrape types, API function, and hook to frontend"
```

---

## Chunk 2: Backend Scrapers

### Task 5: Create scraper schemas and registry

**Files:**
- Create: `backend/scrapers/__init__.py`
- Create: `backend/scrapers/schemas.py`

- [ ] **Step 1: Create scrapers package**

```bash
mkdir -p backend/scrapers
```

- [ ] **Step 2: Create scraper Pydantic schemas**

```python
# backend/scrapers/schemas.py
from pydantic import BaseModel


class ScrapeRequest(BaseModel):
    url: str


class ScrapedColourway(BaseModel):
    name: str
    shade_number: str | None = None
    image_url: str | None = None


class ScrapedYarn(BaseModel):
    name: str
    weight: str | None = None
    fibre: str | None = None
    metres_per_ball: int | None = None
    ball_weight_grams: int | None = None
    needle_size_mm: float | None = None
    tension: str | None = None
    image_url: str | None = None
    colourways: list[ScrapedColourway] = []
    source_url: str
```

- [ ] **Step 3: Create registry**

```python
# backend/scrapers/__init__.py
from typing import Callable, Awaitable
from backend.scrapers.schemas import ScrapedYarn

# Each scraper is a function: (url: str) -> ScrapedYarn
ScraperFn = Callable[[str], ScrapedYarn]

SCRAPERS: dict[str, ScraperFn] = {}


def get_scraper(url: str) -> ScraperFn | None:
    """Return the scraper function for the given URL's domain, or None."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    return SCRAPERS.get(domain)
```

- [ ] **Step 4: Commit**

```bash
git add backend/scrapers/
git commit -m "Add scraper schemas and registry"
```

---

### Task 6: Wool Warehouse scraper

**Files:**
- Create: `backend/scrapers/wool_warehouse.py`
- Create: `backend/tests/fixtures/wool_warehouse.html`
- Create: `backend/tests/test_scraper_wool_warehouse.py`

- [ ] **Step 1: Save HTML fixture**

Fetch and save the Wool Warehouse product page HTML to `backend/tests/fixtures/wool_warehouse.html`:

```bash
mkdir -p backend/tests/fixtures
curl -s -o backend/tests/fixtures/wool_warehouse.html "https://www.woolwarehouse.co.uk/yarn/drops-air-all-colours"
```

- [ ] **Step 2: Write failing tests**

```python
# backend/tests/test_scraper_wool_warehouse.py
from pathlib import Path
from backend.scrapers.wool_warehouse import parse_wool_warehouse

FIXTURE = Path(__file__).parent / "fixtures" / "wool_warehouse.html"


def test_parse_name():
    html = FIXTURE.read_text()
    result = parse_wool_warehouse(html, "https://www.woolwarehouse.co.uk/yarn/drops-air-all-colours")
    assert "Drops" in result.name
    assert "Air" in result.name


def test_parse_specs():
    html = FIXTURE.read_text()
    result = parse_wool_warehouse(html, "https://www.woolwarehouse.co.uk/yarn/drops-air-all-colours")
    assert result.metres_per_ball == 150
    assert result.ball_weight_grams == 50
    assert result.needle_size_mm == 5.0
    assert result.tension is not None
    assert "17" in result.tension  # 17 stitches


def test_parse_fibre():
    html = FIXTURE.read_text()
    result = parse_wool_warehouse(html, "https://www.woolwarehouse.co.uk/yarn/drops-air-all-colours")
    assert result.fibre is not None
    assert "Alpaca" in result.fibre


def test_parse_colourways():
    html = FIXTURE.read_text()
    result = parse_wool_warehouse(html, "https://www.woolwarehouse.co.uk/yarn/drops-air-all-colours")
    assert len(result.colourways) > 0
    # Check a known colourway
    names = [c.name for c in result.colourways]
    assert any("Pearl Grey" in n for n in names)


def test_source_url():
    html = FIXTURE.read_text()
    result = parse_wool_warehouse(html, "https://www.woolwarehouse.co.uk/yarn/drops-air-all-colours")
    assert result.source_url == "https://www.woolwarehouse.co.uk/yarn/drops-air-all-colours"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_scraper_wool_warehouse.py -v
```

- [ ] **Step 4: Implement the scraper**

```python
# backend/scrapers/wool_warehouse.py
import re
import httpx
from bs4 import BeautifulSoup
from backend.scrapers.schemas import ScrapedYarn, ScrapedColourway


def parse_wool_warehouse(html: str, url: str) -> ScrapedYarn:
    """Parse a Wool Warehouse product page HTML into ScrapedYarn."""
    soup = BeautifulSoup(html, "html.parser")

    # Product name from h1
    h1 = soup.find("h1")
    raw_name = h1.get_text(strip=True) if h1 else ""
    # Remove " - All Colours" suffix
    name = re.sub(r"\s*-\s*All Colours$", "", raw_name, flags=re.IGNORECASE)

    # Specs from the product attribute table
    specs: dict[str, str] = {}
    spec_table = soup.find("table", id="product-attribute-specs-table")
    if spec_table:
        for row in spec_table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                specs[th.get_text(strip=True).lower()] = td.get_text(strip=True)

    # Metres per ball
    metres_per_ball = None
    for key in specs:
        if "length" in key or "metre" in key:
            m = re.search(r"(\d+)\s*metres?", specs[key], re.IGNORECASE)
            if m:
                metres_per_ball = int(m.group(1))
            break

    # Ball weight
    ball_weight_grams = None
    for key in specs:
        if "weight" in key or "ball" in key:
            m = re.search(r"(\d+)\s*g", specs[key])
            if m:
                ball_weight_grams = int(m.group(1))
            break

    # Needle size
    needle_size_mm = None
    for key in specs:
        if "needle" in key:
            m = re.search(r"([\d.]+)\s*mm", specs[key])
            if m:
                needle_size_mm = float(m.group(1))
            break

    # Tension
    tension = None
    for key in specs:
        if "tension" in key or "gauge" in key:
            raw = specs[key]
            # Normalise: "17 stitches and 22 rows for a 10x10cm..." → "17 sts × 22 rows / 10cm"
            sts_match = re.search(r"(\d+)\s*stitch", raw, re.IGNORECASE)
            rows_match = re.search(r"(\d+)\s*row", raw, re.IGNORECASE)
            if sts_match and rows_match:
                tension = f"{sts_match.group(1)} sts × {rows_match.group(1)} rows / 10cm"
            elif sts_match:
                tension = f"{sts_match.group(1)} sts / 10cm"
            break

    # Fibre composition
    fibre = None
    for key in specs:
        if "content" in key or "fibre" in key or "fiber" in key or "composition" in key:
            fibre = specs[key]
            break
    # Also check page text for percentage-based composition
    if not fibre:
        page_text = soup.get_text()
        comp_match = re.search(r"(\d+%\s*\w+[\w\s/,]+\d+%\s*\w+)", page_text)
        if comp_match:
            fibre = comp_match.group(1).strip()

    # Weight category - check breadcrumbs or product info
    weight = None
    breadcrumbs = soup.find("div", class_="breadcrumbs")
    if breadcrumbs:
        bc_text = breadcrumbs.get_text()
        weight_keywords = ["Lace", "4 Ply", "DK", "Aran", "Worsted", "Chunky", "Super Chunky"]
        for w in weight_keywords:
            if w.lower() in bc_text.lower():
                weight = w
                break

    # Colourways from dropdown
    colourways: list[ScrapedColourway] = []
    select = soup.find("select", attrs={"name": re.compile("super_group")})
    if select:
        for option in select.find_all("option"):
            text = option.get_text(strip=True)
            if not text or text.lower() in ("all colours", "choose an option", ""):
                continue
            # Parse "03 Pearl Grey" → shade_number="03", name="Pearl Grey"
            shade_match = re.match(r"^(\d+)\s+(.+)$", text)
            if shade_match:
                colourways.append(ScrapedColourway(
                    name=shade_match.group(2).strip(),
                    shade_number=shade_match.group(1),
                    image_url=None,  # WW doesn't provide per-colourway images in the dropdown
                ))
            else:
                colourways.append(ScrapedColourway(name=text, shade_number=None, image_url=None))

    # Main product image
    image_url = None
    img_el = soup.find("img", id="image-main") or soup.find("img", class_=re.compile("product-image"))
    if img_el and img_el.get("src"):
        image_url = img_el["src"]

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
    response = httpx.get(url, follow_redirects=True, timeout=15.0,
                         headers={"User-Agent": "WoolStashTracker/1.0"})
    response.raise_for_status()
    return parse_wool_warehouse(response.text, url)
```

- [ ] **Step 5: Register the scraper**

Add to `backend/scrapers/__init__.py`:
```python
from backend.scrapers.wool_warehouse import scrape_wool_warehouse
SCRAPERS["www.woolwarehouse.co.uk"] = scrape_wool_warehouse
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
python -m pytest backend/tests/test_scraper_wool_warehouse.py -v
```

Note: Tests may need adjustment based on actual fixture HTML structure. The scraper's parsing logic should be tuned to pass the tests against the saved fixture.

- [ ] **Step 7: Commit**

```bash
git add backend/scrapers/wool_warehouse.py backend/tests/fixtures/wool_warehouse.html backend/tests/test_scraper_wool_warehouse.py backend/scrapers/__init__.py
git commit -m "Add Wool Warehouse scraper with tests"
```

---

### Task 7: LoveCrafts scraper

**Files:**
- Create: `backend/scrapers/lovecrafts.py`
- Create: `backend/tests/fixtures/lovecrafts.html`
- Create: `backend/tests/test_scraper_lovecrafts.py`

- [ ] **Step 1: Save HTML fixture**

```bash
curl -s -o backend/tests/fixtures/lovecrafts.html "https://www.lovecrafts.com/en-gb/p/rowan-four-seasons"
```

- [ ] **Step 2: Write failing tests**

```python
# backend/tests/test_scraper_lovecrafts.py
from pathlib import Path
from backend.scrapers.lovecrafts import parse_lovecrafts

FIXTURE = Path(__file__).parent / "fixtures" / "lovecrafts.html"


def test_parse_name():
    html = FIXTURE.read_text()
    result = parse_lovecrafts(html, "https://www.lovecrafts.com/en-gb/p/rowan-four-seasons")
    assert "Rowan" in result.name
    assert "Four Seasons" in result.name


def test_parse_specs():
    html = FIXTURE.read_text()
    result = parse_lovecrafts(html, "https://www.lovecrafts.com/en-gb/p/rowan-four-seasons")
    assert result.metres_per_ball == 75
    assert result.ball_weight_grams == 50
    assert result.needle_size_mm is not None
    assert result.tension is not None
    assert "16" in result.tension  # 16 stitches


def test_parse_fibre():
    html = FIXTURE.read_text()
    result = parse_lovecrafts(html, "https://www.lovecrafts.com/en-gb/p/rowan-four-seasons")
    assert result.fibre is not None
    assert "Cotton" in result.fibre


def test_parse_colourways():
    html = FIXTURE.read_text()
    result = parse_lovecrafts(html, "https://www.lovecrafts.com/en-gb/p/rowan-four-seasons")
    assert len(result.colourways) > 0
    names = [c.name for c in result.colourways]
    assert any("Beach" in n for n in names)


def test_source_url():
    html = FIXTURE.read_text()
    result = parse_lovecrafts(html, "https://www.lovecrafts.com/en-gb/p/rowan-four-seasons")
    assert result.source_url == "https://www.lovecrafts.com/en-gb/p/rowan-four-seasons"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_scraper_lovecrafts.py -v
```

- [ ] **Step 4: Implement the scraper**

```python
# backend/scrapers/lovecrafts.py
import json
import re
import httpx
from bs4 import BeautifulSoup
from backend.scrapers.schemas import ScrapedYarn, ScrapedColourway


def parse_lovecrafts(html: str, url: str) -> ScrapedYarn:
    """Parse a LoveCrafts product page HTML into ScrapedYarn."""
    soup = BeautifulSoup(html, "html.parser")

    # Try JSON-LD first for name and brand
    name = ""
    json_ld = soup.find("script", type="application/ld+json")
    if json_ld:
        try:
            data = json.loads(json_ld.string)
            if isinstance(data, list):
                data = data[0]
            name = data.get("name", "")
            brand = data.get("brand", {})
            if isinstance(brand, dict):
                brand_name = brand.get("name", "")
                if brand_name and not name.startswith(brand_name):
                    name = f"{brand_name} {name}"
        except (json.JSONDecodeError, AttributeError):
            pass

    # Fallback to h1
    if not name:
        h1 = soup.find("h1")
        name = h1.get_text(strip=True) if h1 else ""

    # Parse product details text for specs
    page_text = soup.get_text(separator="\n")

    # Fibre
    fibre = None
    blend_match = re.search(r"(?:Blend|Content|Composition)[:\s]*(.+?)(?:\n|$)", page_text, re.IGNORECASE)
    if blend_match:
        fibre = blend_match.group(1).strip()

    # Metres per ball
    metres_per_ball = None
    length_match = re.search(r"(?:Length)[:\s]*(\d+)\s*m", page_text, re.IGNORECASE)
    if length_match:
        metres_per_ball = int(length_match.group(1))

    # Ball weight
    ball_weight_grams = None
    weight_match = re.search(r"(?:Net Weight|Weight)[:\s]*(\d+)\s*g", page_text, re.IGNORECASE)
    if weight_match:
        ball_weight_grams = int(weight_match.group(1))

    # Needle size - take the first (smallest) value
    needle_size_mm = None
    needle_match = re.search(r"(?:Needles?)[:\s]*([\d.]+)\s*mm", page_text, re.IGNORECASE)
    if needle_match:
        needle_size_mm = float(needle_match.group(1))

    # Tension
    tension = None
    tension_match = re.search(r"(?:Tension|Gauge)[:\s]*(\d+)\s*stitch\w*[,\s]*(\d+)\s*rows?\s*(?:to|per|=)?\s*10\s*cm", page_text, re.IGNORECASE)
    if tension_match:
        tension = f"{tension_match.group(1)} sts × {tension_match.group(2)} rows / 10cm"

    # Colourways - look for shade selectors
    colourways: list[ScrapedColourway] = []
    # LoveCrafts uses variant/shade elements - look for them
    shade_elements = soup.find_all(attrs={"data-shade-name": True})
    if shade_elements:
        for el in shade_elements:
            shade_name = el.get("data-shade-name", "")
            shade_num = el.get("data-shade-number", None)
            img = el.find("img")
            img_url = img.get("src") if img else None
            if shade_name:
                colourways.append(ScrapedColourway(
                    name=shade_name,
                    shade_number=shade_num,
                    image_url=img_url,
                ))

    # If no shade elements, try alt text patterns from images
    if not colourways:
        for img in soup.find_all("img", alt=True):
            alt = img.get("alt", "")
            if name and name.lower() in alt.lower() and alt.lower() != name.lower():
                colour_part = alt.replace(name, "").strip(" -–—")
                if colour_part and len(colour_part) < 50:
                    img_src = img.get("src", "")
                    colourways.append(ScrapedColourway(
                        name=colour_part,
                        shade_number=None,
                        image_url=img_src or None,
                    ))

    # Deduplicate colourways by name
    seen: set[str] = set()
    unique_colourways: list[ScrapedColourway] = []
    for c in colourways:
        if c.name not in seen:
            seen.add(c.name)
            unique_colourways.append(c)

    # Main product image
    image_url = None
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        image_url = og_img["content"]

    return ScrapedYarn(
        name=name,
        weight=None,  # LoveCrafts weight labels don't always match our enum
        fibre=fibre,
        metres_per_ball=metres_per_ball,
        ball_weight_grams=ball_weight_grams,
        needle_size_mm=needle_size_mm,
        tension=tension,
        image_url=image_url,
        colourways=unique_colourways,
        source_url=url,
    )


def scrape_lovecrafts(url: str) -> ScrapedYarn:
    """Fetch and parse a LoveCrafts product page."""
    response = httpx.get(url, follow_redirects=True, timeout=15.0,
                         headers={"User-Agent": "WoolStashTracker/1.0"})
    response.raise_for_status()
    return parse_lovecrafts(response.text, url)
```

- [ ] **Step 5: Register the scraper**

Add to `backend/scrapers/__init__.py`:
```python
from backend.scrapers.lovecrafts import scrape_lovecrafts
SCRAPERS["www.lovecrafts.com"] = scrape_lovecrafts
```

- [ ] **Step 6: Run tests and tune parser to pass**

```bash
python -m pytest backend/tests/test_scraper_lovecrafts.py -v
```

The parser may need adjustments based on the actual fixture HTML. Tune the regex patterns and selectors until all tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/scrapers/lovecrafts.py backend/tests/fixtures/lovecrafts.html backend/tests/test_scraper_lovecrafts.py backend/scrapers/__init__.py
git commit -m "Add LoveCrafts scraper with tests"
```

---

### Task 8: Scrape endpoint

**Files:**
- Modify: `backend/routers/yarns.py`
- Create: `backend/tests/test_scrape_endpoint.py`

- [ ] **Step 1: Install new dependencies**

```bash
cd backend
source .venv/bin/activate
pip install httpx beautifulsoup4
```

Add to `backend/requirements.txt`:
```
httpx==0.28.1
beautifulsoup4==4.13.4
```

- [ ] **Step 2: Write failing endpoint tests**

```python
# backend/tests/test_scrape_endpoint.py
from unittest.mock import patch
from backend.scrapers.schemas import ScrapedYarn, ScrapedColourway


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
    with patch("backend.scrapers.wool_warehouse.scrape_wool_warehouse", return_value=mock_result):
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
    with patch("backend.scrapers.wool_warehouse.scrape_wool_warehouse",
               side_effect=Exception("Connection failed")):
        response = client.post("/api/yarns/scrape", json={
            "url": "https://www.woolwarehouse.co.uk/yarn/test"
        })
    assert response.status_code == 502
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_scrape_endpoint.py -v
```

- [ ] **Step 4: Implement the scrape endpoint**

Add to `backend/routers/yarns.py`, BEFORE the `/{yarn_id}` routes (after `/seed`):

```python
from backend.scrapers import get_scraper, SCRAPERS
from backend.scrapers.schemas import ScrapeRequest, ScrapedYarn

# 4.5 POST /scrape
@router.post("/scrape", response_model=ScrapedYarn)
def scrape_yarn(req: ScrapeRequest):
    scraper = get_scraper(req.url)
    if not scraper:
        supported = ", ".join(sorted(SCRAPERS.keys()))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported URL. Supported sites: {supported}",
        )
    try:
        return scraper(req.url)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to scrape URL: {str(e)}",
        )
```

- [ ] **Step 5: Run all backend tests**

```bash
python -m pytest backend/tests/ -v
```

Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add backend/routers/yarns.py backend/tests/test_scrape_endpoint.py backend/requirements.txt
git commit -m "Add scrape endpoint with supported URL validation"
```

---

## Chunk 3: Frontend Changes

### Task 9: Update yarn form with URL input and new fields

**Files:**
- Modify: `frontend/src/components/yarn-form.tsx`

- [ ] **Step 1: Add URL fetch section and new fields to the form**

At the top of the form (before the grid), add:
- URL input with placeholder "Paste a link from Wool Warehouse or LoveCrafts..."
- "Fetch" button that calls `useScrapeYarn()` mutation
- Helper text: "Supported: woolwarehouse.co.uk, lovecrafts.com"
- When fetch succeeds: populate all matching fields in state, show colourway dropdown if colourways exist
- When a colourway is selected: set colour and image_url from the selected colourway
- Image preview thumbnail (80×80px, rounded) shown when image_url is set

Add new form fields in the grid:
- Needle size (mm): number input with step="0.5"
- Tension: text input with placeholder "e.g. 22 sts × 30 rows / 10cm"
- Ball weight (g): number input
- Image URL: text input (auto-filled from scrape, but editable)

Add the new fields to the form state (useState hooks) and include them in handleSubmit.

The form props interface does NOT need to change — `initialData` is already typed as `Yarn` which will include the new fields.

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/yarn-form.tsx
git commit -m "Add URL import and new fields to yarn form"
```

---

### Task 10: Update yarn table to show new fields and image

**Files:**
- Modify: `frontend/src/components/yarn-table.tsx`

- [ ] **Step 1: Add image and new fields to expanded row**

In the expanded row section, add:
- Image thumbnail (80×80px) if `yarn.image_url` is set, displayed to the left of the details grid
- Needle size, tension, and ball weight in the details grid alongside existing fields (metres per ball, extra metres, dates)

Layout: use flex with the image on the left and details on the right.

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/yarn-table.tsx
git commit -m "Show image and new fields in expanded table row"
```

---

### Task 11: Final integration verification

- [ ] **Step 1: Verify all backend tests pass**

```bash
backend/.venv/bin/python -m pytest backend/tests/ -v
```

- [ ] **Step 2: Verify frontend builds clean**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Smoke test**

Start both servers and verify:
- Existing yarn list works (no regressions)
- Add Yarn dialog shows URL input with helper text
- Paste a Wool Warehouse URL, click Fetch, verify fields populate
- Select a colourway from the dropdown
- Save the yarn, verify new fields appear in expanded row
- Image thumbnail displays correctly

- [ ] **Step 4: Push**

```bash
git push origin feature/wool-stash-tracker
```
