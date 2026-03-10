# URL Import Feature — Design Specification

Import yarn data from product pages on supported retail sites, auto-populating form fields to save manual data entry.

---

## Context

Helen buys yarn from online retailers, primarily woolwarehouse.co.uk and lovecrafts.com. When adding yarn to her stash, she currently types all details manually. This feature lets her paste a product URL and auto-fill fields from the product page.

## New Fields

Four new columns on the `Yarn` model:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `needle_size_mm` | Float (`Column(Float)`) | No | Recommended needle size in mm (e.g. 5.0) |
| `tension` | String (`Column(String)`) | No | Gauge info, e.g. "17 sts × 22 rows / 10cm" |
| `ball_weight_grams` | Integer (`Column(Integer)`) | No | Weight per ball in grams (e.g. 50) |
| `image_url` | String (`Column(String)`) | No | URL to product/colourway image |

**Not adding:** hook size (Helen only knits), price (volatile, not useful for stash management), care instructions (out of scope).

Images are referenced by external URL, not stored locally.

## Scrape API

### Endpoint

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `POST` | `/api/yarns/scrape` | 200 | Scrape product data from a supported URL |

### Request

```json
{"url": "https://www.woolwarehouse.co.uk/yarn/drops-air-all-colours"}
```

### Response

```json
{
  "name": "Drops Air",
  "weight": "Aran",
  "fibre": "Alpaca/Wool/Polyamide",
  "metres_per_ball": 150,
  "ball_weight_grams": 50,
  "needle_size_mm": 5.0,
  "tension": "17 sts × 22 rows / 10cm",
  "image_url": "https://www.woolwarehouse.co.uk/media/.../drops-air.jpg",
  "colourways": [
    {"name": "Pearl Grey", "shade_number": "03", "image_url": "https://..."},
    {"name": "Off White", "shade_number": "01", "image_url": "https://..."}
  ],
  "source_url": "https://www.woolwarehouse.co.uk/yarn/drops-air-all-colours"
}
```

### Error Handling

- Unsupported URL → 400 with message listing supported sites
- Site unreachable / parse failure → 502 with descriptive message

### Backend Structure

One scraper function per site, registered in a domain-keyed dict:

```python
SCRAPERS = {
    "www.woolwarehouse.co.uk": scrape_wool_warehouse,
    "www.lovecrafts.com": scrape_lovecrafts,
}
```

Each scraper takes a URL and returns a common `ScrapedYarn` Pydantic model. Adding a new site means writing one function and adding one dict entry.

**Route ordering:** The `POST /api/yarns/scrape` endpoint must be registered before the `/{yarn_id}` parameterised routes in the router, following the existing pattern for `/stats` and `/seed`.

**New dependencies:** `httpx`, `beautifulsoup4`

## Supported Sites

### woolwarehouse.co.uk

Data available: product name, brand, yarn weight, fibre composition, metres per ball, ball weight, needle size, tension/gauge, colourway images. Colourways listed in a dropdown with shade numbers and names.

### lovecrafts.com

Data available: product name, brand, fibre composition, metres per ball, ball weight, needle size range, tension/gauge, colourway images. Note: weight classification may differ from Helen's preference (e.g. "Worsted" vs "Aran") — auto-filled but editable.

## Frontend Changes

### URL Input in Add/Edit Form

A new section at the top of the yarn form:

- URL text input with placeholder: "Paste a link from Wool Warehouse or LoveCrafts..."
- "Fetch" button beside it
- Helper text below: "Supported: woolwarehouse.co.uk, lovecrafts.com"

### Fetch Flow

1. Helen pastes URL, clicks Fetch
2. Loading spinner on button
3. On success: auto-populate name, weight, fibre, metres per ball, ball weight, needle size, tension, image URL
4. If colourways returned: show colourway dropdown — selecting one fills the `colour` field with the colourway name (e.g. "Pearl Grey"), not the shade number, and updates image URL to the colourway-specific image
5. All auto-filled fields remain editable
6. On error: toast notification, form unchanged

### Image Display

When `image_url` is set, show a thumbnail (~80×80px):
- In the form, as a preview next to the URL input
- In the expanded table row, alongside notes/details

### Backwards Compatibility

The URL field is entirely optional. Manual yarn entry works exactly as before. Existing yarns without the new fields display normally (null values hidden).

## Schema Changes

### Pydantic Schemas

Add to `YarnCreate` and `YarnUpdate`:
- `needle_size_mm: float | None = None`
- `tension: str | None = None`
- `ball_weight_grams: int | None = None`
- `image_url: str | None = None`

Add to `YarnResponse`: same four fields.

New schemas:
- `ScrapeRequest` — `url: str`
- `ScrapedColourway` — `name: str`, `shade_number: str | None`, `image_url: str | None`
- `ScrapedYarn` — `name: str`, `weight: str | None`, `fibre: str | None`, `metres_per_ball: int | None`, `ball_weight_grams: int | None`, `needle_size_mm: float | None`, `tension: str | None`, `image_url: str | None`, `colourways: list[ScrapedColourway]`, `source_url: str`

Note: `brand` is available from both sites but is not included as a separate field — it forms part of the `name` field (e.g. "Drops Air" includes the brand "Drops"). The scraper should combine brand + product name into `name` where appropriate.

### TypeScript Types

Mirror the new fields in `Yarn`, `YarnCreate`, `YarnUpdate` interfaces. Add `ScrapedYarn`, `ScrapedColourway`, `ScrapeRequest` types.

### Alembic Migration

Add four nullable columns to `yarns` table: `needle_size_mm` (Float), `tension` (String), `ball_weight_grams` (Integer), `image_url` (String). All nullable, no defaults. No data migration needed — existing rows get null values.

## Testing

### Backend

- Unit tests for each scraper using saved HTML fixtures (`backend/tests/fixtures/wool_warehouse.html`, `backend/tests/fixtures/lovecrafts.html`) — no live site dependency
- Endpoint tests: valid URL returns scraped data, unsupported domain returns 400, parse failure returns 502
- CRUD tests for new fields: create/update/get yarn with needle_size_mm, tension, ball_weight_grams, image_url

### Frontend

No additional frontend tests for v1.

## Out of Scope

- Local image storage / caching
- Automatic site detection from URL patterns beyond domain matching
- Scraping sites beyond Wool Warehouse and LoveCrafts
- Price tracking
- Hook size (Helen only knits)
