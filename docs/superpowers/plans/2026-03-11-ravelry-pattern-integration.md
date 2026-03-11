# Ravelry Pattern Integration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow users to link a Ravelry pattern URL to a yarn entry, automatically scraping pattern metadata and image.

**Architecture:** Six new nullable columns on the existing Yarn model. A new scraper module (`backend/scrapers/ravelry.py`) fetches and parses Ravelry pattern pages. Pattern images are downloaded to `data/pattern_images/` and served via a StaticFiles mount. Frontend adds a URL input field, a table column, and a pattern card in the expanded row view.

**Tech Stack:** Python/FastAPI/SQLAlchemy/Alembic/BeautifulSoup/httpx (backend), React/TypeScript/shadcn/ui (frontend)

**Spec:** `docs/superpowers/specs/2026-03-11-ravelry-pattern-integration-design.md`

---

## Chunk 1: Backend — Scraper, Schema, Model, Migration

### Task 1: Add ScrapedPattern schema

**Files:**
- Modify: `backend/scrapers/schemas.py`
- [ ] **Step 1: Write the ScrapedPattern model**

Add to `backend/scrapers/schemas.py`:

```python
class ScrapedPattern(BaseModel):
    name: str | None = None
    author: str | None = None
    suggested_yarn: str | None = None
    yarn_weight: str | None = None
    image_url: str | None = None
    source_url: str
```

- [ ] **Step 2: Commit**

```bash
git add backend/scrapers/schemas.py
git commit -m "feat: add ScrapedPattern schema for Ravelry scraper"
```

### Task 2: Create Ravelry scraper with TDD

**Files:**
- Create: `backend/scrapers/ravelry.py`
- Create: `backend/tests/test_scraper_ravelry.py`
- Create: `backend/tests/fixtures/ravelry_pattern.html`

The scraper follows the same pattern as `wool_warehouse.py`: a `parse_ravelry(html, url)` function that parses HTML, and a `scrape_ravelry(url)` function that fetches then parses.

- [ ] **Step 3: Save a Ravelry HTML fixture**

Fetch the HTML from `https://www.ravelry.com/patterns/library/skyler-5` and save it to `backend/tests/fixtures/ravelry_pattern.html`. Use httpx in a quick script or curl:

```bash
curl -o backend/tests/fixtures/ravelry_pattern.html \
  -H "User-Agent: WoolStashTracker/1.0" \
  "https://www.ravelry.com/patterns/library/skyler-5"
```

- [ ] **Step 4: Write failing test for pattern name extraction**

Create `backend/tests/test_scraper_ravelry.py`:

```python
from pathlib import Path

from backend.scrapers.ravelry import parse_ravelry

FIXTURE = Path(__file__).parent / "fixtures" / "ravelry_pattern.html"
URL = "https://www.ravelry.com/patterns/library/skyler-5"


def test_parse_name():
    result = parse_ravelry(FIXTURE.read_text(), URL)
    assert result.name == "Skyler"
```

- [ ] **Step 5: Run test to verify it fails**

```bash
cd backend && .venv/bin/python -m pytest tests/test_scraper_ravelry.py::test_parse_name -v
```

Expected: FAIL (ImportError — `parse_ravelry` does not exist yet)

- [ ] **Step 6: Write minimal parse_ravelry implementation**

Create `backend/scrapers/ravelry.py`:

```python
import json

import httpx
from bs4 import BeautifulSoup

from backend.scrapers.schemas import ScrapedPattern


def parse_ravelry(html: str, url: str) -> ScrapedPattern:
    """Parse a Ravelry pattern page HTML into ScrapedPattern."""
    soup = BeautifulSoup(html, "html.parser")

    # Pattern name from the first h1
    name = None
    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(strip=True)

    # Designer/author — look for the link after "by" text
    author = None
    designer_link = soup.find("a", href=lambda h: h and "/designers/" in h)
    if designer_link:
        author = designer_link.get_text(strip=True)

    # Yarn weight — find in description list (dt/dd pairs)
    yarn_weight = None
    suggested_yarn = None
    for dt in soup.find_all("dt"):
        label = dt.get_text(strip=True).lower()
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue
        if "weight" in label:
            yarn_weight = dd.get_text(strip=True)
        elif "yarn" in label:
            # The yarn name is usually in an anchor tag
            yarn_link = dd.find("a")
            if yarn_link:
                suggested_yarn = yarn_link.get_text(strip=True)
            else:
                suggested_yarn = dd.get_text(strip=True)

    # Main image — look for the primary pattern photo
    image_url = None
    # Try JSON-LD structured data first
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and "image" in data:
                image_url = data["image"]
                break
        except (json.JSONDecodeError, TypeError):
            continue
    # Fallback: find an img with ravelrycache in src
    if not image_url:
        img = soup.find("img", src=lambda s: s and "ravelrycache" in s)
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
        url, follow_redirects=True, timeout=15.0,
        headers={"User-Agent": "WoolStashTracker/1.0"},
    )
    response.raise_for_status()
    return parse_ravelry(response.text, url)
```

- [ ] **Step 7: Run test to verify it passes**

```bash
cd backend && .venv/bin/python -m pytest tests/test_scraper_ravelry.py::test_parse_name -v
```

Expected: PASS

- [ ] **Step 8: Write remaining scraper tests**

Add to `backend/tests/test_scraper_ravelry.py`:

```python
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
```

- [ ] **Step 9: Run all scraper tests**

```bash
cd backend && .venv/bin/python -m pytest tests/test_scraper_ravelry.py -v
```

Expected: All PASS. If any fail, adjust the `parse_ravelry` selectors based on the actual fixture HTML structure.

- [ ] **Step 10: Commit**

```bash
git add backend/scrapers/ravelry.py backend/tests/test_scraper_ravelry.py backend/tests/fixtures/ravelry_pattern.html
git commit -m "feat: add Ravelry pattern scraper with tests"
```

### Task 3: Add pattern columns to database model

**Files:**
- Modify: `backend/models.py`

- [ ] **Step 11: Add six new columns to Yarn model**

Add after the `image_url` column (line 34) in `backend/models.py`:

```python
    ravelry_url = Column(String, nullable=True)
    pattern_name = Column(String, nullable=True)
    pattern_author = Column(String, nullable=True)
    pattern_suggested_yarn = Column(String, nullable=True)
    pattern_yarn_weight = Column(String, nullable=True)
    pattern_image_filename = Column(String, nullable=True)
```

- [ ] **Step 12: Commit**

```bash
git add backend/models.py
git commit -m "feat: add Ravelry pattern columns to Yarn model"
```

### Task 4: Generate Alembic migration

**Files:**
- Create: `backend/alembic/versions/<auto>_add_ravelry_pattern_fields.py`

- [ ] **Step 13: Generate migration**

```bash
cd backend && .venv/bin/python -m alembic revision --autogenerate -m "add ravelry pattern fields to yarns"
```

- [ ] **Step 14: Review the generated migration**

Open the generated file in `backend/alembic/versions/` and verify it adds six `add_column` operations for `ravelry_url`, `pattern_name`, `pattern_author`, `pattern_suggested_yarn`, `pattern_yarn_weight`, `pattern_image_filename` — all `String, nullable=True`.

- [ ] **Step 15: Test migration**

```bash
cd backend && .venv/bin/python -m alembic upgrade head
```

Expected: Migration applies cleanly.

- [ ] **Step 16: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat: add alembic migration for ravelry pattern fields"
```

### Task 5: Update Pydantic schemas

**Files:**
- Modify: `backend/schemas.py`

- [ ] **Step 17: Add ravelry_url to YarnCreate and YarnUpdate**

In `backend/schemas.py`, add to `YarnCreate` (after `image_url` field):

```python
    ravelry_url: str | None = None
```

Add the same field to `YarnUpdate`.

- [ ] **Step 18: Add pattern fields and computed URL to YarnResponse**

Add to `YarnResponse` (after `image_url` field):

```python
    ravelry_url: str | None
    pattern_name: str | None
    pattern_author: str | None
    pattern_suggested_yarn: str | None
    pattern_yarn_weight: str | None
    pattern_image_filename: str | None

    @computed_field
    @property
    def pattern_image_url(self) -> str | None:
        if self.pattern_image_filename:
            return f"/api/pattern-images/{self.pattern_image_filename}"
        return None
```

Add the import at the top of the file:

```python
from pydantic import BaseModel, computed_field
```

- [ ] **Step 19: Run existing tests to verify nothing broke**

```bash
cd backend && .venv/bin/python -m pytest tests/ -v
```

Expected: All existing tests PASS (new nullable fields default to None).

- [ ] **Step 20: Commit**

```bash
git add backend/schemas.py
git commit -m "feat: add ravelry pattern fields to Pydantic schemas"
```

### Task 6: Write API integration tests (TDD — tests before implementation)

**Files:**
- Create: `backend/tests/test_yarns_ravelry.py`

- [ ] **Step 21: Write all failing integration tests**

Create `backend/tests/test_yarns_ravelry.py`:

```python
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
```

- [ ] **Step 22: Run tests to verify they fail**

```bash
cd backend && .venv/bin/python -m pytest tests/test_yarns_ravelry.py -v
```

Expected: All FAIL (router doesn't handle `ravelry_url` yet).

- [ ] **Step 23: Commit failing tests**

```bash
git add backend/tests/test_yarns_ravelry.py
git commit -m "test: add failing integration tests for Ravelry pattern CRUD flow"
```

### Task 7: Implement router and image serving to make tests pass

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/routers/yarns.py`

- [ ] **Step 24: Add StaticFiles mount for pattern images**

In `backend/main.py`, add before the SPA static files mount (before line 36 `if static_dir.is_dir():`). The `/api` prefix means the SPA middleware won't intercept these requests:

```python
# Pattern images directory
pattern_images_dir = Path(__file__).parent.parent / "data" / "pattern_images"
pattern_images_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/api/pattern-images",
    StaticFiles(directory=str(pattern_images_dir)),
    name="pattern-images",
)
```

- [ ] **Step 25: Add URL validation and image helpers to router**

In `backend/routers/yarns.py`, add new imports and helpers at the top (after existing imports):

```python
import logging
import re
from pathlib import Path
from uuid import uuid4

import httpx

from backend.scrapers.ravelry import scrape_ravelry

logger = logging.getLogger(__name__)

RAVELRY_URL_PATTERN = re.compile(
    r"^https?://(www\.)?ravelry\.com/patterns/library/.+"
)

PATTERN_IMAGES_DIR = Path(__file__).parent.parent.parent / "data" / "pattern_images"


def _download_image(image_url: str) -> str | None:
    """Download an image and return the saved filename, or None on failure."""
    try:
        resp = httpx.get(image_url, follow_redirects=True, timeout=15.0,
                         headers={"User-Agent": "WoolStashTracker/1.0"})
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        ext = ".jpg"
        if "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"
        filename = f"{uuid4().hex}{ext}"
        PATTERN_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        (PATTERN_IMAGES_DIR / filename).write_bytes(resp.content)
        return filename
    except Exception:
        logger.warning("Failed to download pattern image from %s", image_url, exc_info=True)
        return None


def _delete_pattern_image(filename: str | None) -> None:
    """Delete a pattern image file if it exists."""
    if not filename:
        return
    path = PATTERN_IMAGES_DIR / filename
    if path.is_file():
        path.unlink()
```

- [ ] **Step 26: Update create_yarn to handle ravelry_url**

Replace the `create_yarn` function in `backend/routers/yarns.py`:

```python
@router.post("/", response_model=YarnResponse, status_code=201)
def create_yarn(yarn_in: YarnCreate, db: Session = Depends(get_db)):
    data = yarn_in.model_dump()

    # Validate and process ravelry_url
    ravelry_url = data.get("ravelry_url")
    if ravelry_url and not RAVELRY_URL_PATTERN.match(ravelry_url):
        raise HTTPException(status_code=422, detail="Invalid Ravelry URL. Expected: https://www.ravelry.com/patterns/library/...")

    if ravelry_url:
        try:
            pattern = scrape_ravelry(ravelry_url)
            data["pattern_name"] = pattern.name
            data["pattern_author"] = pattern.author
            data["pattern_suggested_yarn"] = pattern.suggested_yarn
            data["pattern_yarn_weight"] = pattern.yarn_weight
            if pattern.image_url:
                data["pattern_image_filename"] = _download_image(pattern.image_url)
        except Exception:
            logger.warning("Failed to scrape Ravelry URL: %s", ravelry_url, exc_info=True)

    yarn = Yarn(**data)
    yarn.estimated_total_metres = _compute_estimated_metres(yarn)
    db.add(yarn)
    db.commit()
    db.refresh(yarn)
    return yarn
```

- [ ] **Step 27: Update update_yarn to handle ravelry_url changes**

Replace the `update_yarn` function in `backend/routers/yarns.py`:

```python
@router.put("/{yarn_id}", response_model=YarnResponse)
def update_yarn(yarn_id: int, yarn_in: YarnUpdate, db: Session = Depends(get_db)):
    yarn = db.query(Yarn).filter(Yarn.id == yarn_id).first()
    if not yarn:
        raise HTTPException(status_code=404, detail="Yarn not found")

    update_data = yarn_in.model_dump(exclude_unset=True)

    # Handle ravelry_url changes
    if "ravelry_url" in update_data:
        new_url = update_data["ravelry_url"]

        # Validate URL format
        if new_url and not RAVELRY_URL_PATTERN.match(new_url):
            raise HTTPException(status_code=422, detail="Invalid Ravelry URL. Expected: https://www.ravelry.com/patterns/library/...")

        if new_url != yarn.ravelry_url:
            old_image = yarn.pattern_image_filename
            if new_url:
                # Scrape new pattern
                try:
                    pattern = scrape_ravelry(new_url)
                    update_data["pattern_name"] = pattern.name
                    update_data["pattern_author"] = pattern.author
                    update_data["pattern_suggested_yarn"] = pattern.suggested_yarn
                    update_data["pattern_yarn_weight"] = pattern.yarn_weight
                    if pattern.image_url:
                        update_data["pattern_image_filename"] = _download_image(pattern.image_url)
                    else:
                        update_data["pattern_image_filename"] = None
                except Exception:
                    logger.warning("Failed to scrape Ravelry URL: %s", new_url, exc_info=True)
                    update_data["pattern_name"] = None
                    update_data["pattern_author"] = None
                    update_data["pattern_suggested_yarn"] = None
                    update_data["pattern_yarn_weight"] = None
                    update_data["pattern_image_filename"] = None
            else:
                # URL cleared — remove all pattern fields
                update_data["pattern_name"] = None
                update_data["pattern_author"] = None
                update_data["pattern_suggested_yarn"] = None
                update_data["pattern_yarn_weight"] = None
                update_data["pattern_image_filename"] = None
            _delete_pattern_image(old_image)

    for field, value in update_data.items():
        setattr(yarn, field, value)
    yarn.estimated_total_metres = _compute_estimated_metres(yarn)
    db.commit()
    db.refresh(yarn)
    return yarn
```

- [ ] **Step 28: Update delete_yarn to clean up pattern images**

Replace the `delete_yarn` function:

```python
@router.delete("/{yarn_id}", status_code=204)
def delete_yarn(yarn_id: int, db: Session = Depends(get_db)):
    yarn = db.query(Yarn).filter(Yarn.id == yarn_id).first()
    if not yarn:
        raise HTTPException(status_code=404, detail="Yarn not found")
    _delete_pattern_image(yarn.pattern_image_filename)
    db.delete(yarn)
    db.commit()
```

- [ ] **Step 29: Add pattern fields to search filter**

In the `list_yarns` function, update the `q` filter (around line 53) to include pattern fields:

```python
    if q:
        query = query.filter(
            or_(
                Yarn.name.ilike(f"%{q}%"),
                Yarn.colour.ilike(f"%{q}%"),
                Yarn.fibre.ilike(f"%{q}%"),
                Yarn.intended_project.ilike(f"%{q}%"),
                Yarn.notes.ilike(f"%{q}%"),
                Yarn.pattern_name.ilike(f"%{q}%"),
                Yarn.pattern_author.ilike(f"%{q}%"),
            )
        )
```

- [ ] **Step 30: Run all tests to verify they pass**

```bash
cd backend && .venv/bin/python -m pytest tests/ -v
```

Expected: All PASS (including the previously-failing Ravelry tests).

- [ ] **Step 31: Commit**

```bash
git add backend/main.py backend/routers/yarns.py
git commit -m "feat: add Ravelry pattern scraping to create/update/delete endpoints"
```

---

## Chunk 2: Frontend — Types, Form, Table, Expanded View

### Task 8: Update TypeScript types

**Files:**
- Modify: `frontend/src/types.ts`

- [ ] **Step 32: Add pattern fields to Yarn interface**

In `frontend/src/types.ts`, add after `image_url: string | null;` in the `Yarn` interface:

```typescript
  ravelry_url: string | null;
  pattern_name: string | null;
  pattern_author: string | null;
  pattern_suggested_yarn: string | null;
  pattern_yarn_weight: string | null;
  pattern_image_filename: string | null;
  pattern_image_url: string | null;
```

- [ ] **Step 33: Add ravelry_url to YarnCreate and YarnUpdate**

Add to both `YarnCreate` and `YarnUpdate` interfaces:

```typescript
  ravelry_url?: string | null;
```

- [ ] **Step 34: Commit**

```bash
git add frontend/src/types.ts
git commit -m "feat: add Ravelry pattern fields to TypeScript types"
```

### Task 9: Add Ravelry URL field to form

**Files:**
- Modify: `frontend/src/components/yarn-form.tsx`

- [ ] **Step 35: Add ravelryUrl state**

In `frontend/src/components/yarn-form.tsx`, add after the `notes` state (line 58):

```typescript
  const [ravelryUrl, setRavelryUrl] = useState(initialData?.ravelry_url ?? "");
```

- [ ] **Step 36: Include ravelry_url in form submission**

In the `handleSubmit` function, add to the `data` object (after `notes`):

```typescript
      ravelry_url: ravelryUrl.trim() || null,
```

- [ ] **Step 37: Add Ravelry URL input to form JSX**

Add a new field after the "Intended project" field (after the closing `</div>` on line 357):

```tsx
        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor="yarn-ravelry-url">Ravelry pattern URL</Label>
          <Input
            id="yarn-ravelry-url"
            type="url"
            value={ravelryUrl}
            onChange={(e) => setRavelryUrl(e.target.value)}
            placeholder="https://www.ravelry.com/patterns/library/..."
          />
        </div>
```

- [ ] **Step 38: Commit**

```bash
git add frontend/src/components/yarn-form.tsx
git commit -m "feat: add Ravelry pattern URL field to yarn form"
```

### Task 10: Add Pattern column to table

**Files:**
- Modify: `frontend/src/components/yarn-table.tsx`

- [ ] **Step 39: Add Pattern column header**

In `frontend/src/components/yarn-table.tsx`, add after the "Project" `TableHead` (line 63):

```tsx
          <TableHead className="hidden lg:table-cell">Pattern</TableHead>
```

- [ ] **Step 40: Add Pattern column cell**

Add after the "Project" `TableCell` (after line 97):

```tsx
                <TableCell className="hidden lg:table-cell">
                  {yarn.pattern_name && yarn.ravelry_url ? (
                    <a
                      href={yarn.ravelry_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {yarn.pattern_name}
                    </a>
                  ) : (
                    "—"
                  )}
                </TableCell>
```

- [ ] **Step 41: Update colSpan in expanded row**

In the expanded row `TableCell`, update `colSpan={7}` to `colSpan={8}` to account for the new column (line 102).

- [ ] **Step 42: Commit**

```bash
git add frontend/src/components/yarn-table.tsx
git commit -m "feat: add Pattern column to yarn table"
```

### Task 11: Add pattern card to expanded row view

**Files:**
- Modify: `frontend/src/components/yarn-table.tsx`

- [ ] **Step 43: Add pattern card to expanded view**

In the expanded row section of `yarn-table.tsx`, add a pattern card after the existing details grid (before the notes section, around line 149). Add it inside the `<div className="flex items-start gap-4">` block, or as a separate section:

```tsx
                      {yarn.pattern_name && (
                        <div className="flex items-start gap-3 rounded-md border border-stone-200 bg-white p-3">
                          {yarn.pattern_image_url && (
                            <img
                              src={yarn.pattern_image_url}
                              alt={yarn.pattern_name}
                              className="size-20 rounded border border-stone-200 object-cover flex-shrink-0"
                            />
                          )}
                          <div className="flex flex-col gap-0.5 text-sm">
                            <span className="font-medium">
                              {yarn.ravelry_url ? (
                                <a
                                  href={yarn.ravelry_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:underline"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  {yarn.pattern_name}
                                </a>
                              ) : (
                                yarn.pattern_name
                              )}
                            </span>
                            {yarn.pattern_author && (
                              <span className="text-stone-500">
                                by {yarn.pattern_author}
                              </span>
                            )}
                            {yarn.pattern_suggested_yarn && (
                              <span className="text-stone-500">
                                Yarn: {yarn.pattern_suggested_yarn}
                              </span>
                            )}
                            {yarn.pattern_yarn_weight && (
                              <span className="text-stone-500">
                                Weight: {yarn.pattern_yarn_weight}
                              </span>
                            )}
                          </div>
                        </div>
                      )}
```

Insert this block after the existing `</div>` that closes the `flex items-start gap-4` div (line 148) and before the notes section.

- [ ] **Step 44: Run frontend dev server and verify visually**

```bash
cd frontend && npm run dev
```

Open http://localhost:5173 and verify:
- The form has a "Ravelry pattern URL" field
- The table has a "Pattern" column
- Test by adding a yarn with a Ravelry URL (backend must be running)

- [ ] **Step 45: Commit**

```bash
git add frontend/src/components/yarn-table.tsx
git commit -m "feat: add pattern card to expanded yarn row view"
```

### Task 12: Final verification

- [ ] **Step 46: Run all backend tests**

```bash
cd backend && .venv/bin/python -m pytest tests/ -v
```

Expected: All PASS.

- [ ] **Step 47: Run frontend build to check for type errors**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with no TypeScript errors.

- [ ] **Step 48: End-to-end manual test**

With both backend and frontend running:
1. Add a new yarn with `ravelry_url` = `https://www.ravelry.com/patterns/library/skyler-5`
2. Verify the table shows "Skyler" in the Pattern column as a clickable link
3. Expand the row and verify the pattern card shows image, name, author, yarn, weight
4. Edit the yarn and clear the Ravelry URL — verify pattern data is removed
5. Delete the yarn — verify no errors

- [ ] **Step 49: Final commit if any adjustments were needed**

```bash
git add -A
git commit -m "chore: final adjustments for Ravelry pattern integration"
```
