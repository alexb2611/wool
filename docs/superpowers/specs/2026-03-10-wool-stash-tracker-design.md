# Wool Stash Tracker — Design Specification

A locally-hosted web application for cataloguing a personal wool/yarn stash, replacing a manually maintained Excel spreadsheet.

---

## Context

Helen maintains a spreadsheet of ~34 yarns. The app provides a searchable, filterable interface for browsing the collection, planning projects, and tracking quantities. It will be deployed on an Ubuntu server (192.168.5.153:8001) alongside Model Mate (port 8000).

## Tech Stack

Per the cataloguing app methodology:

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.x (sync), Alembic, Pydantic v2
- **Frontend:** React 18 + TypeScript, Vite, shadcn/ui + Tailwind CSS v4, TanStack Query v5, React Router v7
- **Database:** SQLite (single file in `data/` volume mount)
- **Testing:** pytest (backend), Vitest + React Testing Library + MSW (frontend)
- **Deployment:** Docker Compose, single service, multi-stage Dockerfile

## Data Model

### Yarn Entity

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | Integer PK | Auto | Auto-increment |
| `name` | String | Yes | Brand + product name, e.g. "Drops Alpaca" |
| `weight` | Enum | Yes | Lace, 4 Ply, DK, Aran, Worsted, Chunky, Super Chunky |
| `colour` | String | Yes | Colourway name or description |
| `fibre` | String | Yes | Fibre composition, e.g. "Wool", "Cotton/Acrylic" |
| `metres_per_ball` | Integer | No | Null if unknown |
| `full_balls` | Integer | No | Default 0 |
| `part_balls` | Integer | No | Default 0 |
| `extra_metres` | Integer | No | Null if not applicable |
| `estimated_total_metres` | Integer | No | Computed server-side on save |
| `intended_project` | String | No | What Helen plans to make |
| `notes` | Text | No | Free-text |
| `created_at` | DateTime | Auto | `server_default=func.now()` |
| `updated_at` | DateTime | Auto | `onupdate=func.now()` |

### Weight Enum

Lace, 4 Ply, DK, Aran, Worsted, Chunky, Super Chunky

### Computed Field Logic

```
if metres_per_ball is not None:
    estimated_total_metres = (full_balls * metres_per_ball) + (part_balls * metres_per_ball * 0.5) + (extra_metres or 0)
else:
    estimated_total_metres = None
```

### Pydantic Schemas

- **YarnCreate** — all editable fields (name, weight, colour, fibre required; rest optional)
- **YarnUpdate** — all fields optional
- **YarnResponse** — all fields including computed + timestamps, `from_attributes=True`

## API Design

### CRUD Endpoints

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `POST` | `/api/yarns/` | 201 | Create a yarn |
| `GET` | `/api/yarns/` | 200 | List with pagination, search, filters, sorting |
| `GET` | `/api/yarns/{id}` | 200/404 | Get single yarn |
| `PUT` | `/api/yarns/{id}` | 200/404 | Update a yarn |
| `DELETE` | `/api/yarns/{id}` | 204/404 | Delete a yarn |
| `GET` | `/api/yarns/stats` | 200 | Summary statistics |
| `POST` | `/api/yarns/seed` | 200 | Idempotent seed from spreadsheet data |

### List Query Parameters

- `q` — search across name, colour, fibre, intended_project, notes (case-insensitive `ilike`)
- `weight` — exact enum match
- `fibre` — partial match (e.g. "wool" matches "Alpaca/Wool/Polyamide")
- `has_project` — boolean: `true` = intended_project is not null/empty, `false` = no project
- `sort_by` — name (default), weight, colour, fibre, estimated_total_metres, created_at, updated_at
- `sort_dir` — asc (default) or desc
- `limit` / `offset` — pagination (default limit 50)

### Stats Response

```json
{
  "total_yarns": 33,
  "total_estimated_metres": 12450,
  "by_weight": {"DK": 8, "Aran": 7, "Chunky": 6},
  "by_fibre": {"Wool": 5, "Acrylic": 5, "Cotton/Acrylic": 3}
}
```

The `by_fibre` breakdown treats each unique fibre string as its own category exactly as entered. Blended fibres (e.g. "Cotton/Acrylic") are not split into constituents.

## Frontend Design

### Layout

Single-page app with a header ("Wool Stash") and main content area.

### Summary Dashboard

Displayed above the table (always visible, not a separate tab):

- Total yarns count, total estimated metres
- Weight breakdown as coloured badges with counts
- Top fibre categories with counts

### Main Table

- **Controls row:** debounced search input, weight dropdown filter, fibre text filter, has-project toggle, sort field + direction
- **Columns:** Name, Weight (coloured badge), Colour, Fibre, Quantity (e.g. "3 balls + 2 part"), Est. Metres, Intended Project
- **Expandable rows:** clicking reveals notes, metres per ball, extra metres, timestamps
- **Row actions:** Edit and Delete buttons in expanded view

### Add/Edit Dialog

- Name: text input with autocomplete from existing yarn names
- Weight: dropdown select from enum
- Colour: text input
- Fibre: text input with autocomplete from existing fibre values
- Metres per ball: number input (optional)
- Full balls: number input (default 0)
- Part balls: number input (default 0)
- Extra metres: number input (optional)
- Intended project: text input
- Notes: textarea
- Toast notifications via `sonner`

### Aesthetic

Warm, crafty feel — soft teals and warm neutrals. Weight badges use distinct colours for quick scanning. British English throughout ("colour", "metres", "catalogue"). Responsive for desktop and tablet (iPad).

## Seed Data

- 34 yarns from Helen's spreadsheet hardcoded as a Python list of dicts
- `POST /api/yarns/seed` imports them with free-text quantity mappings per the brief
- Idempotent: skips entries matching on name + colour + weight combination
- No runtime Excel dependency

## Deployment

- **Port:** 8001 on host, 8000 internally (`8001:8000` in Docker Compose)
- **Server:** 192.168.5.153 (coexists with Model Mate on port 8000)
- **Volume:** `./data:/app/data` for SQLite persistence
- **Build:** Multi-stage Dockerfile (Node build → Python runtime)
- **SPA:** Middleware-based serving (not catch-all route)
- **No authentication** — single user on local network
- **Backup:** `tar czf` the `data/` directory

## Testing Strategy

### Backend (pytest)

In-memory SQLite with `StaticPool`, TDD approach. Per entity:
- Create (201, verify all fields)
- Create with optional fields omitted
- List (correct count)
- List with each filter (weight, fibre, has_project, q)
- List with pagination
- List with sorting
- Get by ID (200 and 404)
- Update (200, verify changed + unchanged fields)
- Delete (204, verify gone)
- Stats endpoint
- Seed endpoint (including idempotency)

### Frontend (Vitest + MSW)

- MSW intercepts `/api/*` — no real backend needed
- Test page rendering, form submission, error states
- Accessible queries (`getByRole`, `getByLabelText`)

## Non-Functional Requirements

- No authentication — local network only
- CORS open for local development
- SQLite in `data/` volume mount
- All measurements in metres
- British English throughout the UI
- Responsive layout (desktop + tablet)

## Out of Scope

- Photo uploads
- Project entity with yarn linking
- Low-stock alerts
- Ravelry API integration
- Barcode scanning
- CSV/Excel export
