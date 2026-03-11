# Ravelry Pattern Integration

**Date:** 2026-03-11
**Status:** Approved

## Overview

Add the ability to link a Ravelry pattern URL to a yarn entry. When a URL is provided, the backend scrapes the pattern page to extract metadata (name, author, suggested yarn, yarn weight) and downloads the main pattern image for local storage. This data is displayed in both the yarn table (compact) and an expanded detail view (full).

## Requirements

- Users can paste a Ravelry pattern URL (e.g. `https://www.ravelry.com/patterns/library/skyler-5`) into a dedicated field on the yarn form
- The existing free-text "Intended project" field remains unchanged and independent
- On form submit, the backend fetches the Ravelry page and extracts: pattern name, author, suggested yarn, yarn weight, and main image
- Pattern images are downloaded and stored locally in `data/pattern_images/` (a new pattern for this project — existing yarn/colourway images are stored as remote URLs)
- The yarn table shows the pattern name as a clickable link
- An expanded/detail view shows the full pattern card with image and all metadata
- If scraping fails, the yarn is still saved with null pattern fields
- The `ravelry_url` field is validated to match `https://www.ravelry.com/patterns/library/...`

## Data Model

Six new nullable columns on the `Yarn` table:

| Column | Type | Description |
|--------|------|-------------|
| `ravelry_url` | `String, nullable` | The Ravelry pattern URL |
| `pattern_name` | `String, nullable` | e.g. "Skyler" |
| `pattern_author` | `String, nullable` | e.g. "Quail Studio" |
| `pattern_suggested_yarn` | `String, nullable` | e.g. "Rowan Summerlite DK" |
| `pattern_yarn_weight` | `String, nullable` | e.g. "DK / 8 ply" |
| `pattern_image_filename` | `String, nullable` | Filename of downloaded image in `data/pattern_images/` |

All fields are nullable — a yarn entry does not require a pattern.

## Backend

### Scraping Module

New module: `backend/scrapers/ravelry.py` (in the existing `backend/scrapers/` directory, following the established pattern).

**Scraper function (`scrape_ravelry`):**
- Fetches the page HTML using `httpx` (already a dependency, used by existing scrapers)
- Parses with BeautifulSoup to extract: pattern name, author, suggested yarn, yarn weight, and main image URL
- Returns a new `ScrapedPattern` Pydantic model (added to `backend/scrapers/schemas.py`)

**Note on authentication:** Ravelry pattern pages are publicly accessible without login — confirmed by successfully scraping the example URL. If Ravelry changes this in future, the scraper will fail gracefully (yarn saved, pattern fields null).

**Image downloading:** A separate utility function downloads the image from the extracted URL and saves it to `data/pattern_images/` with a unique filename (e.g. UUID or hash-based). This is handled in the router, not in the scraper function itself (scrapers are parse-only, consistent with existing `wool_warehouse.py` and `lovecrafts.py`).

**Registration:** The Ravelry scraper is NOT added to the `SCRAPERS` dict in `backend/scrapers/__init__.py`, since that registry is typed for `ScrapedYarn` and used by the `/scrape` endpoint. Instead, the router calls `scrape_ravelry` directly during yarn create/update.

**`ScrapedPattern` model** (added to `backend/scrapers/schemas.py`):
- `name: str | None = None`
- `author: str | None = None`
- `suggested_yarn: str | None = None`
- `yarn_weight: str | None = None`
- `image_url: str | None = None`
- `source_url: str`

### API Changes

**Schemas (`backend/schemas.py`):**
- `YarnCreate` and `YarnUpdate`: add `ravelry_url: str | None = None`
- `YarnResponse`: add all six DB columns plus a computed `pattern_image_url: str | None` field using a Pydantic `@computed_field` that constructs `/api/pattern-images/{filename}` from `pattern_image_filename`

**URL validation:** Validate that `ravelry_url`, if provided, matches the pattern `https://www.ravelry.com/patterns/library/...`. Reject other URLs with a 422 response.

**Router (`backend/routers/yarns.py`):**
- On create/update: if `ravelry_url` is provided and differs from the current value, call the Ravelry scraper, download the new image, delete the old image file (if any), and populate all pattern fields
- If `ravelry_url` is cleared (set to null), clear all pattern fields and delete the old image file from disk
- On yarn deletion: delete the associated pattern image file if one exists
- If scraping fails, save the yarn with null pattern fields and log a warning

**Image serving:**
- New `StaticFiles` mount in `backend/main.py`: mount `data/pattern_images/` at `/api/pattern-images/`
- This mount must be added **before** the catch-all `/` static files mount for the SPA, otherwise it will be shadowed
- Create the `data/pattern_images/` directory on app startup if it doesn't exist

### Migration

- Alembic migration adding six nullable columns to the `yarn` table
- No data migration required (existing rows get null values)

## Frontend

### Form (`yarn-form.tsx`)

- New "Ravelry pattern" URL input field, separate from "Intended project"
- Simple text input for pasting URLs
- Sent to backend on form submit; scraping happens server-side

### Table (`yarn-table.tsx`)

- New "Pattern" column showing pattern name as a clickable link (opens Ravelry URL in new tab)
- Displays "—" when no pattern is linked

### Search

The existing `q` search filter should include `pattern_name` and `pattern_author` so users can search for yarns by their linked pattern.

### Detail/Expanded View

- When a yarn row is expanded, show a pattern card with:
  - Pattern image
  - Pattern name (linked to Ravelry)
  - Author
  - Suggested yarn
  - Yarn weight
- Styled with shadcn/ui components, consistent with existing UI

### TypeScript Types (`types.ts`)

- Add to `Yarn`: `ravelry_url`, `pattern_name`, `pattern_author`, `pattern_suggested_yarn`, `pattern_yarn_weight`, `pattern_image_filename`, `pattern_image_url` (all `string | null`)
- Add to `YarnCreate` and `YarnUpdate`: `ravelry_url?: string | null`

## Testing

### Backend (TDD)

- **Scraper unit tests:** Mock HTTP responses with sample Ravelry HTML, verify extraction of all fields and image URL
- **API integration tests:**
  - Create yarn with `ravelry_url` — verify pattern fields populated and image downloaded
  - Update yarn to change/clear `ravelry_url` — verify fields updated/cleared and old image deleted
  - Create yarn with invalid/non-Ravelry URL — verify 422 validation error
  - Create yarn when scraping fails — verify yarn saved with null pattern fields

### Migration

- Standard Alembic autogenerate, verify with `alembic upgrade head`

## Docker

- The `data/` directory is already a Docker volume, so `data/pattern_images/` is persisted automatically
- No new Python dependencies needed (`httpx` and `beautifulsoup4` are already used)

## Decisions

- **Flat columns over separate table:** Pattern data is metadata about a yarn entry, not an independent entity. Keeps queries simple and matches existing codebase patterns.
- **Local image storage over hotlinking:** More reliable, no dependency on Ravelry CDN availability or hotlink policies. This is a new pattern (existing images use remote URLs) but appropriate since Ravelry CDN URLs could change.
- **Scrape on submit over live preview:** Simpler implementation, fewer API calls, avoids complexity of preview state management.
- **Separate field from "Intended project":** Keeps concerns independent — a yarn can have a pattern link, a project note, both, or neither.
- **Scraper in existing `backend/scrapers/` directory:** Follows established project structure and conventions, reuses `httpx` and BeautifulSoup.
