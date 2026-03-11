# Ravelry Pattern Integration

**Date:** 2026-03-11
**Status:** Approved

## Overview

Add the ability to link a Ravelry pattern URL to a yarn entry. When a URL is provided, the backend scrapes the pattern page to extract metadata (name, author, suggested yarn, yarn weight) and downloads the main pattern image for local storage. This data is displayed in both the yarn table (compact) and an expanded detail view (full).

## Requirements

- Users can paste a Ravelry pattern URL (e.g. `https://www.ravelry.com/patterns/library/skyler-5`) into a dedicated field on the yarn form
- The existing free-text "Intended project" field remains unchanged and independent
- On form submit, the backend fetches the Ravelry page and extracts: pattern name, author, suggested yarn, yarn weight, and main image
- Pattern images are downloaded and stored locally (consistent with colourway swatch images)
- The yarn table shows the pattern name as a clickable link
- An expanded/detail view shows the full pattern card with image and all metadata
- If scraping fails, the yarn is still saved with null pattern fields

## Data Model

Six new nullable columns on the `Yarn` table:

| Column | Type | Description |
|--------|------|-------------|
| `ravelry_url` | `String, nullable` | The Ravelry pattern URL |
| `pattern_name` | `String, nullable` | e.g. "Skyler" |
| `pattern_author` | `String, nullable` | e.g. "Quail Studio" |
| `pattern_suggested_yarn` | `String, nullable` | e.g. "Rowan Summerlite DK" |
| `pattern_yarn_weight` | `String, nullable` | e.g. "DK / 8 ply" |
| `pattern_image_filename` | `String, nullable` | Filename in `data/pattern_images/` |

All fields are nullable — a yarn entry does not require a pattern.

## Backend

### Scraping Module

New module: `backend/scraping/ravelry.py`

- Accepts a Ravelry pattern URL
- Fetches the page HTML using `httpx` (already used) or `requests`
- Parses with BeautifulSoup to extract: pattern name, author, suggested yarn, yarn weight
- Downloads the main pattern image to `data/pattern_images/`
- Returns a dataclass/dict with all extracted fields
- Raises/returns gracefully on failure (network error, unexpected page structure)

### API Changes

**Schemas (`backend/schemas.py`):**
- `YarnCreate` and `YarnUpdate`: add `ravelry_url: str | None = None`
- `YarnResponse`: add all six new fields plus computed `pattern_image_url: str | None`

**Router (`backend/routers/yarns.py`):**
- On create/update: if `ravelry_url` is provided and changed from current value, call the scraper and populate pattern fields
- If `ravelry_url` is cleared (set to null), clear all pattern fields and delete the old image file
- If scraping fails, save the yarn with null pattern fields (log a warning)

**Static files:**
- New route: `GET /api/pattern-images/{filename}` serving from `data/pattern_images/`

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

- **Scraper unit tests:** Mock HTTP responses with sample Ravelry HTML, verify extraction of all fields and image download
- **API integration tests:**
  - Create yarn with `ravelry_url` — verify pattern fields populated
  - Update yarn to change/clear `ravelry_url` — verify fields updated/cleared
  - Create yarn with invalid URL — verify graceful failure, yarn still saved

### Migration

- Standard Alembic autogenerate, verify with `alembic upgrade head`

## Decisions

- **Flat columns over separate table:** Pattern data is metadata about a yarn entry, not an independent entity. Keeps queries simple and matches existing codebase patterns.
- **Local image storage over hotlinking:** Consistent with colourway swatch images, more reliable, no dependency on Ravelry CDN availability.
- **Scrape on submit over live preview:** Simpler implementation, fewer API calls, avoids complexity of preview state management.
- **Separate field from "Intended project":** Keeps concerns independent — a yarn can have a pattern link, a project note, both, or neither.
