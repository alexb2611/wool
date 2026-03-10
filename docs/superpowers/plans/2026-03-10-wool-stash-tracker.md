# Wool Stash Tracker Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a locally-hosted wool/yarn cataloguing web app to replace Helen's Excel spreadsheet.

**Architecture:** Single-entity FastAPI backend with SQLite, React + TypeScript frontend using shadcn/ui. Table-based UI with expandable rows, search/filter/sort, summary dashboard. Dockerised for deployment on port 8001.

**Tech Stack:** Python 3.11+ / FastAPI / SQLAlchemy 2.x / Alembic / Pydantic v2 / React 18 / TypeScript / Vite / shadcn/ui / Tailwind CSS v4 / TanStack Query v5 / React Router v7 / SQLite / Docker

**Spec:** `docs/superpowers/specs/2026-03-10-wool-stash-tracker-design.md`

**Methodology:** See `/home/alex/Documents/cataloguing-app-methodology.md` for patterns and conventions.

---

## File Structure

```
wool/
├── backend/
│   ├── main.py                    # FastAPI app, SPA middleware, router registration
│   ├── database.py                # SQLAlchemy engine, SessionLocal, get_db dependency
│   ├── models.py                  # Yarn ORM model + YarnWeight enum
│   ├── schemas.py                 # YarnCreate, YarnUpdate, YarnResponse, StatsResponse
│   ├── seed_data.py               # 34 yarns as Python dicts
│   ├── routers/
│   │   └── yarns.py               # All yarn CRUD + stats + seed endpoints
│   ├── tests/
│   │   ├── conftest.py            # In-memory SQLite fixtures (engine, db, client)
│   │   ├── test_yarns_crud.py     # Create, get, update, delete tests
│   │   ├── test_yarns_list.py     # List, search, filter, sort, pagination tests
│   │   ├── test_yarns_stats.py    # Stats endpoint tests
│   │   └── test_yarns_seed.py     # Seed endpoint + idempotency tests
│   ├── alembic/
│   │   ├── env.py                 # Alembic env with render_as_batch=True
│   │   └── versions/              # Migration files
│   ├── alembic.ini                # Alembic config
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                 # Multi-stage: Node build → Python runtime
│   └── static/                    # (Generated) Frontend build output
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts          # Typed fetch wrapper with error handling
│   │   │   └── yarns.ts           # Yarn API functions (CRUD + stats + seed)
│   │   ├── hooks/
│   │   │   └── use-yarns.ts       # TanStack Query hooks for all yarn operations
│   │   ├── types.ts               # TypeScript interfaces mirroring Pydantic schemas
│   │   ├── components/
│   │   │   ├── layout.tsx         # App shell with header and navigation
│   │   │   ├── yarn-table.tsx     # Main data table with expandable rows
│   │   │   ├── yarn-form.tsx      # Add/Edit form used in dialog
│   │   │   ├── yarn-dialog.tsx    # Dialog wrapper for add/edit
│   │   │   ├── delete-dialog.tsx  # Delete confirmation dialog
│   │   │   ├── search-filters.tsx # Search bar + filter controls
│   │   │   ├── dashboard.tsx      # Summary stats display
│   │   │   └── weight-badge.tsx   # Coloured weight category badge
│   │   ├── pages/
│   │   │   └── yarns-page.tsx     # Main page composing all components
│   │   ├── data/
│   │   │   └── constants.ts       # Weight badge colours, sort options
│   │   ├── lib/
│   │   │   └── utils.ts           # cn() helper (shadcn default)
│   │   ├── App.tsx                # Router setup
│   │   └── main.tsx               # Entry point
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts             # Build output to ../backend/static/, dev proxy
│   ├── tailwind.config.ts         # Warm craft-shop colour palette
│   └── components.json            # shadcn/ui config
├── docker-compose.yml             # Single service, port 8001:8000, data volume
├── CLAUDE.md                      # AI assistant instructions
└── data/                          # (Runtime) SQLite DB
```

---

## Chunk 1: Backend Foundation

### Task 1: Project scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/__init__.py`
- Create: `backend/routers/__init__.py`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: Create backend directory structure**

```bash
mkdir -p backend/routers backend/tests backend/static
```

- [ ] **Step 2: Create requirements.txt**

```
fastapi==0.115.12
uvicorn[standard]==0.34.0
sqlalchemy==2.0.40
alembic==1.14.1
pydantic==2.11.1
```

- [ ] **Step 3: Create empty __init__.py files**

Create empty files at:
- `backend/__init__.py`
- `backend/routers/__init__.py`
- `backend/tests/__init__.py`

- [ ] **Step 4: Create Python venv and install dependencies**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest httpx  # test dependencies
```

- [ ] **Step 5: Create .gitignore**

Create `backend/.gitignore`:
```
.venv/
__pycache__/
*.pyc
static/
```

Also create top-level `.gitignore`:
```
data/
```

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/__init__.py backend/routers/__init__.py backend/tests/__init__.py backend/.gitignore .gitignore
git commit -m "Add backend project scaffolding"
```

---

### Task 2: Database and ORM model

**Files:**
- Create: `backend/database.py`
- Create: `backend/models.py`

- [ ] **Step 1: Create database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/wool.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: Create models.py with Yarn model and YarnWeight enum**

```python
import enum
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, func
from backend.database import Base


class YarnWeight(str, enum.Enum):
    LACE = "Lace"
    FOUR_PLY = "4 Ply"
    DK = "DK"
    ARAN = "Aran"
    WORSTED = "Worsted"
    CHUNKY = "Chunky"
    SUPER_CHUNKY = "Super Chunky"


class Yarn(Base):
    __tablename__ = "yarns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    weight = Column(Enum(YarnWeight), nullable=False)
    colour = Column(String, nullable=False)
    fibre = Column(String, nullable=False)
    metres_per_ball = Column(Integer, nullable=True)
    full_balls = Column(Integer, nullable=False, default=0)
    part_balls = Column(Integer, nullable=False, default=0)
    extra_metres = Column(Integer, nullable=True)
    estimated_total_metres = Column(Integer, nullable=True)
    intended_project = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 3: Verify model imports work**

```bash
cd backend && source .venv/bin/activate
python -c "from backend.models import Yarn, YarnWeight; print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add backend/database.py backend/models.py
git commit -m "Add database setup and Yarn ORM model"
```

---

### Task 3: Pydantic schemas

**Files:**
- Create: `backend/schemas.py`

- [ ] **Step 1: Create schemas.py**

```python
from datetime import datetime
from pydantic import BaseModel
from backend.models import YarnWeight


class YarnCreate(BaseModel):
    name: str
    weight: YarnWeight
    colour: str
    fibre: str
    metres_per_ball: int | None = None
    full_balls: int = 0
    part_balls: int = 0
    extra_metres: int | None = None
    intended_project: str | None = None
    notes: str | None = None


class YarnUpdate(BaseModel):
    name: str | None = None
    weight: YarnWeight | None = None
    colour: str | None = None
    fibre: str | None = None
    metres_per_ball: int | None = None
    full_balls: int | None = None
    part_balls: int | None = None
    extra_metres: int | None = None
    intended_project: str | None = None
    notes: str | None = None


class YarnResponse(BaseModel):
    id: int
    name: str
    weight: YarnWeight
    colour: str
    fibre: str
    metres_per_ball: int | None
    full_balls: int
    part_balls: int
    extra_metres: int | None
    estimated_total_metres: int | None
    intended_project: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StatsResponse(BaseModel):
    total_yarns: int
    total_estimated_metres: int
    by_weight: dict[str, int]
    by_fibre: dict[str, int]
```

- [ ] **Step 2: Verify schema imports**

```bash
python -c "from backend.schemas import YarnCreate, YarnResponse, StatsResponse; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend/schemas.py
git commit -m "Add Pydantic schemas for Yarn entity"
```

---

### Task 4: Test fixtures

**Files:**
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Create conftest.py with in-memory SQLite fixtures**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

Note: This fixture depends on `backend/main.py` existing (Task 5 creates a minimal version). These two tasks should be done together.

- [ ] **Step 2: Commit**

```bash
git add backend/tests/conftest.py
git commit -m "Add test fixtures with in-memory SQLite"
```

---

### Task 5: Minimal FastAPI app + Alembic setup

**Files:**
- Create: `backend/main.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`

- [ ] **Step 1: Create minimal main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from starlette.requests import Request
from starlette.responses import Response

app = FastAPI(title="Wool Stash Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"


@app.middleware("http")
async def serve_spa(request: Request, call_next) -> Response:
    response = await call_next(request)
    if response.status_code == 404 and not request.url.path.startswith("/api"):
        index = static_dir / "index.html"
        if index.is_file():
            return FileResponse(str(index))
    return response


if static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(static_dir)), name="static")
```

- [ ] **Step 2: Initialise Alembic**

```bash
cd backend
source .venv/bin/activate
alembic init alembic
```

- [ ] **Step 3: Update alembic/env.py**

Replace the `target_metadata` line and configure `render_as_batch=True`:

Set `target_metadata = Base.metadata` (import from `backend.database`).
In `run_migrations_online()`, add `render_as_batch=True` to `context.configure()`.

- [ ] **Step 4: Update alembic.ini**

Set `sqlalchemy.url = sqlite:///./data/wool.db`

- [ ] **Step 5: Create initial migration**

```bash
mkdir -p data
alembic revision --autogenerate -m "create yarns table"
```

- [ ] **Step 6: Verify migration**

Check the generated migration uses `batch_alter_table` (for SQLite compatibility).

```bash
alembic upgrade head
```

- [ ] **Step 7: Verify tests can import app**

```bash
python -m pytest backend/tests/ -v --co  # collect-only, no tests yet
```

- [ ] **Step 8: Commit**

```bash
git add backend/main.py backend/alembic.ini backend/alembic/ data/.gitkeep
git commit -m "Add FastAPI app and Alembic migration setup"
```

---

## Chunk 2: Backend CRUD Endpoints (TDD)

### Task 6: Create yarn endpoint

**Files:**
- Create: `backend/routers/yarns.py`
- Modify: `backend/main.py` (register router)
- Create: `backend/tests/test_yarns_crud.py`

- [ ] **Step 1: Write failing test for create yarn**

```python
# backend/tests/test_yarns_crud.py
from backend.models import YarnWeight


def test_create_yarn(client):
    response = client.post("/api/yarns/", json={
        "name": "Drops Alpaca",
        "weight": "4 Ply",
        "colour": "Light Sea Green",
        "fibre": "Alpaca",
        "metres_per_ball": 167,
        "full_balls": 1,
        "part_balls": 0,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Drops Alpaca"
    assert data["weight"] == "4 Ply"
    assert data["colour"] == "Light Sea Green"
    assert data["fibre"] == "Alpaca"
    assert data["metres_per_ball"] == 167
    assert data["full_balls"] == 1
    assert data["part_balls"] == 0
    assert data["estimated_total_metres"] == 167  # 1 * 167 + 0 * 83.5 + 0
    assert data["id"] is not None
    assert data["created_at"] is not None


def test_create_yarn_minimal(client):
    """Create with only required fields."""
    response = client.post("/api/yarns/", json={
        "name": "Mystery Yarn",
        "weight": "Aran",
        "colour": "Blue",
        "fibre": "Unknown",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["full_balls"] == 0
    assert data["part_balls"] == 0
    assert data["metres_per_ball"] is None
    assert data["estimated_total_metres"] is None
    assert data["intended_project"] is None
    assert data["notes"] is None


def test_create_yarn_with_extra_metres(client):
    """Verify computed field with extra_metres."""
    response = client.post("/api/yarns/", json={
        "name": "Test Yarn",
        "weight": "DK",
        "colour": "Red",
        "fibre": "Wool",
        "metres_per_ball": 100,
        "full_balls": 2,
        "part_balls": 3,
        "extra_metres": 30,
    })
    assert response.status_code == 201
    data = response.json()
    # (2 * 100) + (3 * 100 * 0.5) + 30 = 200 + 150 + 30 = 380
    assert data["estimated_total_metres"] == 380
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_yarns_crud.py -v
```

Expected: FAIL (no route registered)

- [ ] **Step 3: Create yarns router with create endpoint**

```python
# backend/routers/yarns.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Yarn
from backend.schemas import YarnCreate, YarnUpdate, YarnResponse

router = APIRouter(prefix="/api/yarns", tags=["yarns"])

# IMPORTANT: Route registration order matters. Fixed-path routes (/stats, /seed)
# MUST appear before the parameterised route (/{yarn_id}) in this file.
# Final order should be: POST /, GET / (list), GET /stats, POST /seed,
# GET /{yarn_id}, PUT /{yarn_id}, DELETE /{yarn_id}.


def _compute_estimated_metres(yarn: Yarn) -> int | None:
    if yarn.metres_per_ball is None:
        return None
    return int(
        (yarn.full_balls * yarn.metres_per_ball)
        + (yarn.part_balls * yarn.metres_per_ball * 0.5)
        + (yarn.extra_metres or 0)
    )


@router.post("/", response_model=YarnResponse, status_code=201)
def create_yarn(yarn: YarnCreate, db: Session = Depends(get_db)):
    db_yarn = Yarn(**yarn.model_dump())
    db_yarn.estimated_total_metres = _compute_estimated_metres(db_yarn)
    db.add(db_yarn)
    db.commit()
    db.refresh(db_yarn)
    return db_yarn
```

- [ ] **Step 4: Register router in main.py**

Add to `backend/main.py`:
```python
from backend.routers import yarns
app.include_router(yarns.router)
```

Place the router registration after CORS middleware but before the static files mount.

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest backend/tests/test_yarns_crud.py -v
```

Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add backend/routers/yarns.py backend/tests/test_yarns_crud.py backend/main.py
git commit -m "Add create yarn endpoint with computed metreage"
```

---

### Task 7: Get, update, delete endpoints

**Files:**
- Modify: `backend/routers/yarns.py`
- Modify: `backend/tests/test_yarns_crud.py`

- [ ] **Step 1: Write failing tests for get, update, delete**

Append to `backend/tests/test_yarns_crud.py`:

```python
def _create_yarn(client, **overrides):
    """Helper to create a yarn and return the response data."""
    data = {
        "name": "Test Yarn",
        "weight": "DK",
        "colour": "Red",
        "fibre": "Wool",
        "metres_per_ball": 100,
        "full_balls": 1,
        "part_balls": 0,
    }
    data.update(overrides)
    response = client.post("/api/yarns/", json=data)
    assert response.status_code == 201
    return response.json()


def test_get_yarn(client):
    created = _create_yarn(client)
    response = client.get(f"/api/yarns/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Yarn"


def test_get_yarn_not_found(client):
    response = client.get("/api/yarns/999")
    assert response.status_code == 404


def test_update_yarn(client):
    created = _create_yarn(client)
    response = client.put(f"/api/yarns/{created['id']}", json={
        "colour": "Blue",
        "full_balls": 3,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["colour"] == "Blue"
    assert data["full_balls"] == 3
    assert data["name"] == "Test Yarn"  # unchanged
    assert data["estimated_total_metres"] == 300  # recomputed: 3 * 100


def test_update_yarn_not_found(client):
    response = client.put("/api/yarns/999", json={"colour": "Blue"})
    assert response.status_code == 404


def test_delete_yarn(client):
    created = _create_yarn(client)
    response = client.delete(f"/api/yarns/{created['id']}")
    assert response.status_code == 204
    # Verify it's gone
    response = client.get(f"/api/yarns/{created['id']}")
    assert response.status_code == 404


def test_delete_yarn_not_found(client):
    response = client.delete("/api/yarns/999")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify new tests fail**

```bash
python -m pytest backend/tests/test_yarns_crud.py -v
```

- [ ] **Step 3: Implement get, update, delete in yarns router**

Add to `backend/routers/yarns.py`:

```python
@router.get("/{yarn_id}", response_model=YarnResponse)
def get_yarn(yarn_id: int, db: Session = Depends(get_db)):
    yarn = db.query(Yarn).filter(Yarn.id == yarn_id).first()
    if not yarn:
        raise HTTPException(status_code=404, detail="Yarn not found")
    return yarn


@router.put("/{yarn_id}", response_model=YarnResponse)
def update_yarn(yarn_id: int, yarn_update: YarnUpdate, db: Session = Depends(get_db)):
    yarn = db.query(Yarn).filter(Yarn.id == yarn_id).first()
    if not yarn:
        raise HTTPException(status_code=404, detail="Yarn not found")
    update_data = yarn_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(yarn, field, value)
    yarn.estimated_total_metres = _compute_estimated_metres(yarn)
    db.commit()
    db.refresh(yarn)
    return yarn


@router.delete("/{yarn_id}", status_code=204)
def delete_yarn(yarn_id: int, db: Session = Depends(get_db)):
    yarn = db.query(Yarn).filter(Yarn.id == yarn_id).first()
    if not yarn:
        raise HTTPException(status_code=404, detail="Yarn not found")
    db.delete(yarn)
    db.commit()
```

- [ ] **Step 4: Run tests to verify all pass**

```bash
python -m pytest backend/tests/test_yarns_crud.py -v
```

Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add backend/routers/yarns.py backend/tests/test_yarns_crud.py
git commit -m "Add get, update, delete yarn endpoints"
```

---

### Task 8: List endpoint with search, filters, sorting, pagination

**Files:**
- Modify: `backend/routers/yarns.py`
- Create: `backend/tests/test_yarns_list.py`

- [ ] **Step 1: Write failing tests for list endpoint**

```python
# backend/tests/test_yarns_list.py

def _create_yarn(client, **overrides):
    data = {
        "name": "Test Yarn",
        "weight": "DK",
        "colour": "Red",
        "fibre": "Wool",
        "metres_per_ball": 100,
        "full_balls": 1,
        "part_balls": 0,
    }
    data.update(overrides)
    response = client.post("/api/yarns/", json=data)
    assert response.status_code == 201
    return response.json()


def test_list_yarns_empty(client):
    response = client.get("/api/yarns/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_yarns(client):
    _create_yarn(client, name="Yarn A")
    _create_yarn(client, name="Yarn B")
    response = client.get("/api/yarns/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_yarns_search(client):
    _create_yarn(client, name="Drops Alpaca", colour="Green")
    _create_yarn(client, name="Stylecraft Special", colour="Red")
    response = client.get("/api/yarns/", params={"q": "alpaca"})
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Drops Alpaca"


def test_list_yarns_search_colour(client):
    _create_yarn(client, name="Yarn A", colour="Teal Tweed")
    _create_yarn(client, name="Yarn B", colour="Red")
    response = client.get("/api/yarns/", params={"q": "teal"})
    assert len(response.json()) == 1


def test_list_yarns_search_notes(client):
    _create_yarn(client, name="Yarn A", notes="Left over from scarf")
    _create_yarn(client, name="Yarn B", notes="Brand new")
    response = client.get("/api/yarns/", params={"q": "scarf"})
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Yarn A"


def test_list_yarns_search_intended_project(client):
    _create_yarn(client, name="Yarn A", intended_project="Summer blanket")
    _create_yarn(client, name="Yarn B")
    response = client.get("/api/yarns/", params={"q": "blanket"})
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Yarn A"


def test_list_yarns_filter_weight(client):
    _create_yarn(client, name="Yarn A", weight="DK")
    _create_yarn(client, name="Yarn B", weight="Aran")
    response = client.get("/api/yarns/", params={"weight": "Aran"})
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Yarn B"


def test_list_yarns_filter_fibre(client):
    _create_yarn(client, name="Yarn A", fibre="Alpaca/Wool/Polyamide")
    _create_yarn(client, name="Yarn B", fibre="Cotton")
    response = client.get("/api/yarns/", params={"fibre": "wool"})
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Yarn A"


def test_list_yarns_filter_has_project(client):
    _create_yarn(client, name="Yarn A", intended_project="Scarf")
    _create_yarn(client, name="Yarn B")
    response = client.get("/api/yarns/", params={"has_project": "true"})
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Yarn A"
    response = client.get("/api/yarns/", params={"has_project": "false"})
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Yarn B"


def test_list_yarns_sort(client):
    _create_yarn(client, name="Zebra Yarn")
    _create_yarn(client, name="Apple Yarn")
    response = client.get("/api/yarns/", params={"sort_by": "name", "sort_dir": "asc"})
    names = [y["name"] for y in response.json()]
    assert names == ["Apple Yarn", "Zebra Yarn"]
    response = client.get("/api/yarns/", params={"sort_by": "name", "sort_dir": "desc"})
    names = [y["name"] for y in response.json()]
    assert names == ["Zebra Yarn", "Apple Yarn"]


def test_list_yarns_pagination(client):
    for i in range(5):
        _create_yarn(client, name=f"Yarn {i}", colour=f"Colour {i}")
    response = client.get("/api/yarns/", params={"limit": 2, "offset": 0})
    assert len(response.json()) == 2
    response = client.get("/api/yarns/", params={"limit": 2, "offset": 3})
    assert len(response.json()) == 2
    response = client.get("/api/yarns/", params={"limit": 2, "offset": 4})
    assert len(response.json()) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_yarns_list.py -v
```

- [ ] **Step 3: Implement list endpoint**

Add to `backend/routers/yarns.py`:

```python
from sqlalchemy import or_

@router.get("/", response_model=list[YarnResponse])
def list_yarns(
    q: str | None = None,
    weight: str | None = None,
    fibre: str | None = None,
    has_project: bool | None = None,
    sort_by: str = "name",
    sort_dir: str = "asc",
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Yarn)

    if q:
        query = query.filter(or_(
            Yarn.name.ilike(f"%{q}%"),
            Yarn.colour.ilike(f"%{q}%"),
            Yarn.fibre.ilike(f"%{q}%"),
            Yarn.intended_project.ilike(f"%{q}%"),
            Yarn.notes.ilike(f"%{q}%"),
        ))

    if weight:
        query = query.filter(Yarn.weight == weight)

    if fibre:
        query = query.filter(Yarn.fibre.ilike(f"%{fibre}%"))

    if has_project is True:
        query = query.filter(Yarn.intended_project.isnot(None), Yarn.intended_project != "")
    elif has_project is False:
        query = query.filter(or_(Yarn.intended_project.is_(None), Yarn.intended_project == ""))

    # Sorting
    sort_column = getattr(Yarn, sort_by, Yarn.name)
    if sort_dir == "desc":
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)

    query = query.offset(offset).limit(limit)
    return query.all()
```

Important: The list endpoint (`GET /`) must be registered BEFORE the get-by-id endpoint (`GET /{yarn_id}`) in the router to avoid `/stats` being interpreted as an id. Alternatively, register the stats route before the `{yarn_id}` route.

- [ ] **Step 4: Run tests to verify all pass**

```bash
python -m pytest backend/tests/test_yarns_list.py -v
```

Expected: 10 passed

- [ ] **Step 5: Run all tests**

```bash
python -m pytest backend/tests/ -v
```

Expected: 19 passed (9 CRUD + 10 list)

- [ ] **Step 6: Commit**

```bash
git add backend/routers/yarns.py backend/tests/test_yarns_list.py
git commit -m "Add list yarns endpoint with search, filters, sorting, pagination"
```

---

### Task 9: Stats endpoint

**Files:**
- Modify: `backend/routers/yarns.py`
- Create: `backend/tests/test_yarns_stats.py`

- [ ] **Step 1: Write failing tests for stats endpoint**

```python
# backend/tests/test_yarns_stats.py
from backend.tests.test_yarns_list import _create_yarn


def test_stats_empty(client):
    response = client.get("/api/yarns/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_yarns"] == 0
    assert data["total_estimated_metres"] == 0
    assert data["by_weight"] == {}
    assert data["by_fibre"] == {}


def test_stats_with_data(client):
    _create_yarn(client, name="Yarn A", weight="DK", fibre="Wool",
                 metres_per_ball=100, full_balls=2, part_balls=0)
    _create_yarn(client, name="Yarn B", weight="Aran", fibre="Cotton/Acrylic",
                 metres_per_ball=200, full_balls=1, part_balls=1)
    _create_yarn(client, name="Yarn C", weight="DK", fibre="Wool",
                 metres_per_ball=None)

    response = client.get("/api/yarns/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_yarns"] == 3
    # Yarn A: 200, Yarn B: 200 + 100 = 300, Yarn C: None → 0 for total
    assert data["total_estimated_metres"] == 500
    assert data["by_weight"] == {"DK": 2, "Aran": 1}
    assert data["by_fibre"] == {"Wool": 2, "Cotton/Acrylic": 1}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_yarns_stats.py -v
```

- [ ] **Step 3: Implement stats endpoint**

Add to `backend/routers/yarns.py` (must be BEFORE the `/{yarn_id}` route):

```python
from backend.schemas import StatsResponse
from sqlalchemy import func as sa_func
from collections import Counter

@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    yarns = db.query(Yarn).all()
    total_yarns = len(yarns)
    total_estimated_metres = sum(
        y.estimated_total_metres for y in yarns if y.estimated_total_metres is not None
    )
    by_weight: dict[str, int] = Counter()
    by_fibre: dict[str, int] = Counter()
    for y in yarns:
        by_weight[y.weight.value] += 1
        by_fibre[y.fibre] += 1

    return StatsResponse(
        total_yarns=total_yarns,
        total_estimated_metres=total_estimated_metres,
        by_weight=dict(by_weight),
        by_fibre=dict(by_fibre),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest backend/tests/test_yarns_stats.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add backend/routers/yarns.py backend/tests/test_yarns_stats.py
git commit -m "Add stats endpoint with weight and fibre breakdowns"
```

---

### Task 10: Seed endpoint

**Files:**
- Create: `backend/seed_data.py`
- Modify: `backend/routers/yarns.py`
- Create: `backend/tests/test_yarns_seed.py`

- [ ] **Step 1: Create seed_data.py with all 33 yarns from the spreadsheet**

```python
# backend/seed_data.py
SEED_YARNS = [
    {
        "name": "Drops Alpaca",
        "weight": "4 Ply",
        "colour": "Light Sea Green",
        "fibre": "Alpaca",
        "metres_per_ball": 167,
        "full_balls": 1,
        "part_balls": 0,
    },
    {
        "name": "Drops Air",
        "weight": "Aran",
        "colour": "Pearl Grey 03",
        "fibre": "Alpaca/Wool/Polyamide",
        "metres_per_ball": 150,
        "full_balls": 2,
        "part_balls": 2,
    },
    {
        "name": "Drops Alaska",
        "weight": "Aran",
        "colour": "Olive green",
        "fibre": "Wool",
        "metres_per_ball": 70,
        "full_balls": 0,
        "part_balls": 0,
        "extra_metres": 30,
        "notes": "Left over from Alex scarf",
    },
    {
        "name": "Hobbycraft Everyday",
        "weight": "Aran",
        "colour": "Sage green",
        "fibre": "Acrylic",
        "metres_per_ball": 195,
        "full_balls": 0,
        "part_balls": 1,
    },
    {
        "name": "Rowan Four Seasons",
        "weight": "Aran",
        "colour": "Blue",
        "fibre": "Cotton/Acrylic",
        "metres_per_ball": 75,
        "full_balls": 5,
        "part_balls": 5,
        "intended_project": "Summer bag - or a top from Rowan book?",
    },
    {
        "name": "Sandnes Garn Tykke Line",
        "weight": "Aran",
        "colour": "Green",
        "fibre": "Cotton/Viscose/Linen",
        "metres_per_ball": 60,
        "full_balls": 14,
        "part_balls": 0,
        "intended_project": "Knit Sisu Picnic Pullover",
    },
    {
        "name": "Sirdar Hayfield Bonus Tweed",
        "weight": "Aran",
        "colour": "Teal Tweed",
        "fibre": "Acrylic/Wool/Viscose",
        "metres_per_ball": 840,
        "full_balls": 0,
        "part_balls": 1,
    },
    {
        "name": "Stylecraft Special",
        "weight": "Aran",
        "colour": "Burgundy",
        "fibre": "Acrylic",
        "metres_per_ball": 196,
        "full_balls": 1,
        "part_balls": 0,
    },
    {
        "name": "Aran Woollen Mill",
        "weight": "Aran",
        "colour": "Light purple tweed",
        "fibre": "Merino",
        "metres_per_ball": 225,
        "full_balls": 3,
        "part_balls": 1,
        "intended_project": "Maybe the Phildar tank top?",
        "notes": "Guess 811m",
    },
    {
        "name": "Rowan Sultano",
        "weight": "Chunky",
        "colour": "Burgundy",
        "fibre": "Cashmere/Silk",
        "metres_per_ball": 85,
        "full_balls": 11,
        "part_balls": 1,
    },
    {
        "name": "Rowan Sultano",
        "weight": "Chunky",
        "colour": "Juniper",
        "fibre": "Cashmere/Silk",
        "metres_per_ball": 85,
        "full_balls": 7,
        "part_balls": 1,
    },
    {
        "name": "Stylecraft Special",
        "weight": "Chunky",
        "colour": "Black",
        "fibre": "Acrylic",
        "metres_per_ball": 144,
        "full_balls": 8,
        "part_balls": 0,
        "intended_project": "King Cole v-neck top - pattern 6379",
        "notes": "Two new balls, need to unpick Wallis jumper to use other six.",
    },
    {
        "name": "Stylecraft Special Babies",
        "weight": "Chunky",
        "colour": "Off-white",
        "fibre": "Acrylic",
        "metres_per_ball": 136,
        "full_balls": 1,
        "part_balls": 1,
        "notes": "Left over from baby blanket",
    },
    {
        "name": "Stylecraft Weekender",
        "weight": "Chunky",
        "colour": "Duck Egg",
        "fibre": "Acrylic",
        "metres_per_ball": 100,
        "full_balls": 5,
        "part_balls": 0,
        "intended_project": "Blanket",
    },
    {
        "name": "Stylecraft Weekender",
        "weight": "Chunky",
        "colour": "Clay",
        "fibre": "Acrylic",
        "metres_per_ball": 100,
        "full_balls": 0,
        "part_balls": 1,
        "extra_metres": 10,
        "intended_project": "Blanket",
    },
    {
        "name": "Unknown",
        "weight": "Chunky",
        "colour": "Brown",
        "fibre": "Acrylic",
        "full_balls": 0,
        "part_balls": 3,
        "notes": "Scarves?",
    },
    {
        "name": "Drops Karisma",
        "weight": "DK",
        "colour": "Greeny/blue",
        "fibre": "Wool",
        "metres_per_ball": 100,
        "full_balls": 0,
        "part_balls": 1,
    },
    {
        "name": "Hobbycraft Cotton Blend Plain",
        "weight": "DK",
        "colour": "Light grey",
        "fibre": "Cotton/Acrylic",
        "metres_per_ball": 215,
        "full_balls": 1,
        "part_balls": 0,
    },
    {
        "name": "King Cole Merino Blend",
        "weight": "DK",
        "colour": "Caramel 790",
        "fibre": "Merino",
        "metres_per_ball": 112,
        "full_balls": 1,
        "part_balls": 1,
        "notes": "Left over from scarf knit for Shelley. Superwash.",
    },
    {
        "name": "Lana Grossa Bacca",
        "weight": "DK",
        "colour": "Dark blue",
        "fibre": "Cotton",
        "metres_per_ball": 120,
        "full_balls": 7,
        "part_balls": 0,
        "intended_project": "Rowan Skyler pattern from book",
    },
    {
        "name": "Paintbox Metallic",
        "weight": "DK",
        "colour": "Pina Colada",
        "fibre": "Cotton/Polyamide",
        "metres_per_ball": 120,
        "full_balls": 1,
        "part_balls": 0,
        "notes": "Left over from top mum reknitted",
    },
    {
        "name": "Rico Fashion Nature",
        "weight": "DK",
        "colour": "Beige 001",
        "fibre": "Acrylic/Wool/Camel/Viscose",
        "metres_per_ball": 233,
        "full_balls": 0,
        "part_balls": 1,
        "notes": "Left over from cushion cover",
    },
    {
        "name": "Stylecraft Naturals",
        "weight": "DK",
        "colour": "Pink",
        "fibre": "Cotton",
        "metres_per_ball": 105,
        "full_balls": 13,
        "part_balls": 0,
        "intended_project": "Stylecraft summer jumper pattern",
    },
    {
        "name": "West Yorkshire Spinners Elements",
        "weight": "DK",
        "colour": "Caribbean Sea",
        "fibre": "Lyocell/Wool",
        "metres_per_ball": 112,
        "full_balls": 9,
        "part_balls": 0,
        "intended_project": "Summer top from Elements pattern book",
    },
    {
        "name": "DMC",
        "weight": "DK",
        "colour": "Beige 773",
        "fibre": "Cotton",
        "metres_per_ball": 106,
        "full_balls": 7,
        "part_balls": 0,
        "intended_project": "A summer top?",
        "notes": "DK weight but thin",
    },
    {
        "name": "Drops Alpaca Silk",
        "weight": "Lace",
        "colour": "Heather (pink)",
        "fibre": "Alpaca/Silk",
        "metres_per_ball": 140,
        "full_balls": 1,
        "part_balls": 1,
    },
    {
        "name": "Drops Andes",
        "weight": "Super Chunky",
        "colour": "Green mix",
        "fibre": "Wool/Alpaca",
        "metres_per_ball": 90,
        "full_balls": 0,
        "part_balls": 1,
    },
    {
        "name": "Drops Eskimo",
        "weight": "Super Chunky",
        "colour": "Plum (dark purple)",
        "fibre": "Wool",
        "metres_per_ball": 50,
        "full_balls": 0,
        "part_balls": 1,
        "notes": "Left over from scarf knit for Tommy. Now called Snow",
    },
    {
        "name": "Drops Eskimo",
        "weight": "Super Chunky",
        "colour": "Dark Grape (purple)",
        "fibre": "Wool",
        "metres_per_ball": 50,
        "full_balls": 0,
        "part_balls": 0,
        "extra_metres": 20,
        "notes": "Now called Snow.",
    },
    {
        "name": "Sublime Extra Fine Merino",
        "weight": "Worsted",
        "colour": "Aubergine",
        "fibre": "Merino",
        "metres_per_ball": 100,
        "full_balls": 0,
        "part_balls": 1,
        "notes": "Discontinued",
    },
    {
        "name": "Sublime Extra Fine Merino",
        "weight": "Worsted",
        "colour": "Mole",
        "fibre": "Merino",
        "metres_per_ball": 100,
        "full_balls": 0,
        "part_balls": 1,
        "notes": "Discontinued",
    },
    {
        "name": "Rico Creative Cotton",
        "weight": "Worsted",
        "colour": "White",
        "fibre": "Cotton",
        "metres_per_ball": 85,
        "full_balls": 1,
        "part_balls": 0,
        "intended_project": "Use for a stripe in a summer top?",
    },
    {
        "name": "Rico Creative Cotton",
        "weight": "Worsted",
        "colour": "Light Blue",
        "fibre": "Cotton",
        "metres_per_ball": 85,
        "full_balls": 0,
        "part_balls": 1,
        "intended_project": "Use for a stripe in a summer top?",
        "notes": "Nice and soft once knitted",
    },
    {
        "name": "Rico Creative Cotton",
        "weight": "Worsted",
        "colour": "Turquoise",
        "fibre": "Cotton",
        "metres_per_ball": 85,
        "full_balls": 1,
        "part_balls": 0,
        "intended_project": "Use for a stripe in a summer top?",
    },
]
```

Note: The brief maps "Worsted/DK" to "Worsted" and "Aran / Worsted" to "Aran" (nearest standard match). "DK (but thin!)" maps to "DK" with a note.

- [ ] **Step 2: Write failing tests for seed endpoint**

```python
# backend/tests/test_yarns_seed.py
from backend.seed_data import SEED_YARNS


def test_seed_yarns(client):
    response = client.post("/api/yarns/seed")
    assert response.status_code == 200
    data = response.json()
    assert data["created"] == len(SEED_YARNS)
    assert data["skipped"] == 0
    # Verify yarns exist
    list_response = client.get("/api/yarns/")
    assert len(list_response.json()) == len(SEED_YARNS)


def test_seed_yarns_idempotent(client):
    """Running seed twice should not create duplicates."""
    client.post("/api/yarns/seed")
    response = client.post("/api/yarns/seed")
    data = response.json()
    assert data["created"] == 0
    assert data["skipped"] == len(SEED_YARNS)
    list_response = client.get("/api/yarns/")
    assert len(list_response.json()) == len(SEED_YARNS)
```

Note: Tests use `len(SEED_YARNS)` to stay in sync with the seed data list.

- [ ] **Step 3: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_yarns_seed.py -v
```

- [ ] **Step 4: Implement seed endpoint**

Add to `backend/routers/yarns.py`:

```python
from backend.seed_data import SEED_YARNS

@router.post("/seed")
def seed_yarns(db: Session = Depends(get_db)):
    created = 0
    skipped = 0
    for yarn_data in SEED_YARNS:
        existing = db.query(Yarn).filter(
            Yarn.name == yarn_data["name"],
            Yarn.colour == yarn_data["colour"],
            Yarn.weight == yarn_data["weight"],
        ).first()
        if existing:
            skipped += 1
            continue
        db_yarn = Yarn(**yarn_data)
        db_yarn.estimated_total_metres = _compute_estimated_metres(db_yarn)
        db.add(db_yarn)
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}
```

Important: The `/seed` route must be registered BEFORE `/{yarn_id}` to avoid "seed" being interpreted as a yarn ID.

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest backend/tests/test_yarns_seed.py -v
```

- [ ] **Step 6: Run all backend tests**

```bash
python -m pytest backend/tests/ -v
```

Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/seed_data.py backend/routers/yarns.py backend/tests/test_yarns_seed.py
git commit -m "Add seed endpoint with 34 yarns from spreadsheet"
```

---

## Chunk 3: Frontend Scaffold

### Task 11: Vite + React + TypeScript project setup

**Files:**
- Create: `frontend/` directory with Vite scaffold

- [ ] **Step 1: Create Vite project**

```bash
cd /path/to/wool
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: Install dependencies**

```bash
npm install @tanstack/react-query react-router-dom sonner
npm install -D @types/node
```

- [ ] **Step 3: Configure vite.config.ts**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: "../backend/static",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
```

- [ ] **Step 4: Add frontend/.gitignore entry for node_modules**

Ensure `node_modules/` is in `frontend/.gitignore` (Vite scaffold usually includes this).

- [ ] **Step 5: Verify dev server starts**

```bash
npm run dev
```

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "Add Vite + React + TypeScript frontend scaffold"
```

---

### Task 12: Tailwind CSS v4 + shadcn/ui setup

**Files:**
- Modify: `frontend/` (Tailwind + shadcn config)

- [ ] **Step 1: Install Tailwind CSS v4**

```bash
cd frontend
npm install tailwindcss @tailwindcss/vite
```

Add the Tailwind Vite plugin to `vite.config.ts`:
```typescript
import tailwindcss from "@tailwindcss/vite";
// add to plugins array: tailwindcss()
```

Replace content of `src/index.css` with:
```css
@import "tailwindcss";
```

- [ ] **Step 2: Initialise shadcn/ui**

```bash
npx shadcn@latest init
```

Select: New York style, neutral base colour. This creates `components.json` and `src/lib/utils.ts`.

- [ ] **Step 3: Add required shadcn components**

```bash
npx shadcn@latest add button input table dialog select card badge separator dropdown-menu collapsible label textarea
```

- [ ] **Step 4: Configure warm craft-shop colour palette**

Update `src/index.css` to include custom CSS variables for the warm teal/neutral palette. Override the shadcn theme variables with craft-shop colours.

- [ ] **Step 5: Verify build works**

```bash
npm run build
```

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "Add Tailwind CSS v4 and shadcn/ui with craft-shop theme"
```

---

### Task 13: TypeScript types and API client

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/yarns.ts`

- [ ] **Step 1: Create types.ts mirroring Pydantic schemas**

```typescript
// frontend/src/types.ts

export type YarnWeight =
  | "Lace"
  | "4 Ply"
  | "DK"
  | "Aran"
  | "Worsted"
  | "Chunky"
  | "Super Chunky";

export interface Yarn {
  id: number;
  name: string;
  weight: YarnWeight;
  colour: string;
  fibre: string;
  metres_per_ball: number | null;
  full_balls: number;
  part_balls: number;
  extra_metres: number | null;
  estimated_total_metres: number | null;
  intended_project: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface YarnCreate {
  name: string;
  weight: YarnWeight;
  colour: string;
  fibre: string;
  metres_per_ball?: number | null;
  full_balls?: number;
  part_balls?: number;
  extra_metres?: number | null;
  intended_project?: string | null;
  notes?: string | null;
}

export interface YarnUpdate {
  name?: string;
  weight?: YarnWeight;
  colour?: string;
  fibre?: string;
  metres_per_ball?: number | null;
  full_balls?: number;
  part_balls?: number;
  extra_metres?: number | null;
  intended_project?: string | null;
  notes?: string | null;
}

export interface YarnStats {
  total_yarns: number;
  total_estimated_metres: number;
  by_weight: Record<string, number>;
  by_fibre: Record<string, number>;
}

export interface YarnListParams {
  q?: string;
  weight?: YarnWeight;
  fibre?: string;
  has_project?: boolean;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

export interface SeedResult {
  created: number;
  skipped: number;
}
```

- [ ] **Step 2: Create API client**

```typescript
// frontend/src/api/client.ts

const BASE_URL = "/api";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export { request, ApiError };
```

- [ ] **Step 3: Create yarns API module**

```typescript
// frontend/src/api/yarns.ts

import { request } from "./client";
import type { Yarn, YarnCreate, YarnUpdate, YarnStats, YarnListParams, SeedResult } from "../types";

export function listYarns(params?: YarnListParams): Promise<Yarn[]> {
  const searchParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        searchParams.set(key, String(value));
      }
    });
  }
  const query = searchParams.toString();
  return request<Yarn[]>(`/yarns/${query ? `?${query}` : ""}`);
}

export function getYarn(id: number): Promise<Yarn> {
  return request<Yarn>(`/yarns/${id}`);
}

export function createYarn(data: YarnCreate): Promise<Yarn> {
  return request<Yarn>("/yarns/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateYarn(id: number, data: YarnUpdate): Promise<Yarn> {
  return request<Yarn>(`/yarns/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteYarn(id: number): Promise<void> {
  return request<void>(`/yarns/${id}`, { method: "DELETE" });
}

export function getYarnStats(): Promise<YarnStats> {
  return request<YarnStats>("/yarns/stats");
}

export function seedYarns(): Promise<SeedResult> {
  return request<SeedResult>("/yarns/seed", { method: "POST" });
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/api/
git commit -m "Add TypeScript types and API client for yarns"
```

---

### Task 14: TanStack Query hooks

**Files:**
- Create: `frontend/src/hooks/use-yarns.ts`

- [ ] **Step 1: Create TanStack Query hooks**

```typescript
// frontend/src/hooks/use-yarns.ts

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as yarnsApi from "../api/yarns";
import type { YarnCreate, YarnUpdate, YarnListParams } from "../types";

const YARNS_KEY = ["yarns"];
const STATS_KEY = ["yarns", "stats"];

export function useYarnList(params?: YarnListParams) {
  return useQuery({
    queryKey: [...YARNS_KEY, params],
    queryFn: () => yarnsApi.listYarns(params),
  });
}

export function useYarn(id: number) {
  return useQuery({
    queryKey: [...YARNS_KEY, id],
    queryFn: () => yarnsApi.getYarn(id),
  });
}

export function useYarnStats() {
  return useQuery({
    queryKey: STATS_KEY,
    queryFn: yarnsApi.getYarnStats,
  });
}

export function useCreateYarn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: YarnCreate) => yarnsApi.createYarn(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: YARNS_KEY });
      queryClient.invalidateQueries({ queryKey: STATS_KEY });
    },
  });
}

export function useUpdateYarn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: YarnUpdate }) =>
      yarnsApi.updateYarn(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: YARNS_KEY });
      queryClient.invalidateQueries({ queryKey: STATS_KEY });
    },
  });
}

export function useDeleteYarn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => yarnsApi.deleteYarn(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: YARNS_KEY });
      queryClient.invalidateQueries({ queryKey: STATS_KEY });
    },
  });
}

export function useSeedYarns() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: yarnsApi.seedYarns,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: YARNS_KEY });
      queryClient.invalidateQueries({ queryKey: STATS_KEY });
    },
  });
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/use-yarns.ts
git commit -m "Add TanStack Query hooks for yarn operations"
```

---

### Task 15: App shell and layout

**Files:**
- Create: `frontend/src/components/layout.tsx`
- Create: `frontend/src/data/constants.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Create constants with weight badge colours**

```typescript
// frontend/src/data/constants.ts

export const WEIGHT_COLOURS: Record<string, string> = {
  "Lace": "bg-violet-100 text-violet-800",
  "4 Ply": "bg-sky-100 text-sky-800",
  "DK": "bg-teal-100 text-teal-800",
  "Aran": "bg-amber-100 text-amber-800",
  "Worsted": "bg-orange-100 text-orange-800",
  "Chunky": "bg-rose-100 text-rose-800",
  "Super Chunky": "bg-fuchsia-100 text-fuchsia-800",
};

export const YARN_WEIGHTS = [
  "Lace",
  "4 Ply",
  "DK",
  "Aran",
  "Worsted",
  "Chunky",
  "Super Chunky",
] as const;

export const SORT_OPTIONS = [
  { value: "name", label: "Name" },
  { value: "weight", label: "Weight" },
  { value: "colour", label: "Colour" },
  { value: "fibre", label: "Fibre" },
  { value: "estimated_total_metres", label: "Est. Metres" },
  { value: "created_at", label: "Date Added" },
  { value: "updated_at", label: "Last Updated" },
] as const;
```

- [ ] **Step 2: Create layout component**

```typescript
// frontend/src/components/layout.tsx

import { ReactNode } from "react";

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <h1 className="text-2xl font-bold text-teal-800">
            Wool Stash
          </h1>
          <p className="text-sm text-stone-500">
            Helen's yarn catalogue
          </p>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        {children}
      </main>
    </div>
  );
}
```

- [ ] **Step 3: Update App.tsx with router and query provider**

```typescript
// frontend/src/App.tsx

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { Layout } from "./components/layout";
import { YarnsPage } from "./pages/yarns-page";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<YarnsPage />} />
          </Routes>
        </Layout>
        <Toaster position="bottom-right" />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

- [ ] **Step 4: Create placeholder YarnsPage**

```typescript
// frontend/src/pages/yarns-page.tsx

export function YarnsPage() {
  return <div>Yarns page — coming soon</div>;
}
```

- [ ] **Step 5: Update main.tsx**

Ensure `main.tsx` imports `index.css` and renders `App`.

- [ ] **Step 6: Verify dev server runs**

```bash
npm run dev
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/
git commit -m "Add app shell with layout, routing, and query provider"
```

---

## Chunk 4: Frontend Pages & Features

### Task 16: Weight badge component

**Files:**
- Create: `frontend/src/components/weight-badge.tsx`

- [ ] **Step 1: Create weight badge component**

```typescript
// frontend/src/components/weight-badge.tsx

import { Badge } from "@/components/ui/badge";
import { WEIGHT_COLOURS } from "@/data/constants";

export function WeightBadge({ weight }: { weight: string }) {
  const colours = WEIGHT_COLOURS[weight] ?? "bg-stone-100 text-stone-800";
  return <Badge className={colours}>{weight}</Badge>;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/weight-badge.tsx
git commit -m "Add weight badge component with colour coding"
```

---

### Task 17: Summary dashboard component

**Files:**
- Create: `frontend/src/components/dashboard.tsx`

- [ ] **Step 1: Create dashboard component**

```typescript
// frontend/src/components/dashboard.tsx

import { Card, CardContent } from "@/components/ui/card";
import { useYarnStats } from "@/hooks/use-yarns";
import { WeightBadge } from "./weight-badge";

export function Dashboard() {
  const { data: stats, isLoading } = useYarnStats();

  if (isLoading || !stats) return null;

  return (
    <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-stone-500">Total Yarns</p>
          <p className="text-2xl font-bold text-teal-800">{stats.total_yarns}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-stone-500">Est. Total Metres</p>
          <p className="text-2xl font-bold text-teal-800">
            {stats.total_estimated_metres.toLocaleString()}m
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-stone-500">By Weight</p>
          <div className="mt-2 flex flex-wrap gap-1">
            {Object.entries(stats.by_weight).map(([weight, count]) => (
              <span key={weight} className="flex items-center gap-1">
                <WeightBadge weight={weight} />
                <span className="text-xs text-stone-500">{count}</span>
              </span>
            ))}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-stone-500">Top Fibres</p>
          <div className="mt-2 space-y-1">
            {Object.entries(stats.by_fibre)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 5)
              .map(([fibre, count]) => (
                <div key={fibre} className="flex justify-between text-sm">
                  <span className="text-stone-700">{fibre}</span>
                  <span className="text-stone-500">{count}</span>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/dashboard.tsx
git commit -m "Add summary dashboard component"
```

---

### Task 18: Search and filter controls

**Files:**
- Create: `frontend/src/components/search-filters.tsx`

- [ ] **Step 1: Create search and filter controls**

The component should accept current filter values and an `onChange` callback. Include:
- Debounced search input (use a `useEffect` with `setTimeout` for debounce)
- Weight dropdown (Select from shadcn, with "All weights" option)
- Fibre text filter input
- Has-project toggle (three-state: all / with project / without project)
- Sort field dropdown + sort direction toggle button

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/search-filters.tsx
git commit -m "Add search and filter controls component"
```

---

### Task 19: Yarn table with expandable rows

**Files:**
- Create: `frontend/src/components/yarn-table.tsx`

- [ ] **Step 1: Create yarn table component**

Use shadcn `Table` components. Each row shows: name, weight badge, colour, fibre, quantity summary, est. metres, intended project. Clicking a row toggles an expanded section showing: notes, metres per ball, extra metres, created/updated timestamps, edit/delete buttons.

Quantity summary helper:
```typescript
function formatQuantity(yarn: Yarn): string {
  const parts: string[] = [];
  if (yarn.full_balls > 0) parts.push(`${yarn.full_balls} ball${yarn.full_balls !== 1 ? "s" : ""}`);
  if (yarn.part_balls > 0) parts.push(`${yarn.part_balls} part`);
  if (yarn.extra_metres) parts.push(`${yarn.extra_metres}m extra`);
  return parts.join(" + ") || "None";
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/yarn-table.tsx
git commit -m "Add yarn table component with expandable rows"
```

---

### Task 20: Yarn form and dialog

**Files:**
- Create: `frontend/src/components/yarn-form.tsx`
- Create: `frontend/src/components/yarn-dialog.tsx`

- [ ] **Step 1: Create yarn form component**

A form with all editable fields. Accepts optional `initialData` for edit mode. Uses shadcn `Input`, `Select`, `Textarea`, `Label`. Name and fibre inputs should offer autocomplete suggestions from existing values (pass `existingNames` and `existingFibres` as props, use a datalist or custom dropdown).

- [ ] **Step 2: Create yarn dialog component**

A shadcn `Dialog` wrapping the form. Props: `open`, `onOpenChange`, `yarn` (optional, for edit mode). Uses `useCreateYarn` or `useUpdateYarn` mutation. Shows toast on success/error.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/yarn-form.tsx frontend/src/components/yarn-dialog.tsx
git commit -m "Add yarn form and dialog components"
```

---

### Task 21: Delete confirmation dialog

**Files:**
- Create: `frontend/src/components/delete-dialog.tsx`

- [ ] **Step 1: Create delete confirmation dialog**

A shadcn `Dialog` confirming deletion. Shows yarn name. Uses `useDeleteYarn` mutation. Toast on success.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/delete-dialog.tsx
git commit -m "Add delete confirmation dialog"
```

---

### Task 22: Compose the yarns page

**Files:**
- Modify: `frontend/src/pages/yarns-page.tsx`

- [ ] **Step 1: Compose all components into YarnsPage**

Wire together:
- `Dashboard` at the top
- `SearchFilters` below with state managed via `useState` / URL params
- `YarnTable` with data from `useYarnList(params)`
- "Add Yarn" button opening `YarnDialog`
- Edit/delete actions from table rows opening respective dialogs
- Loading and empty states

- [ ] **Step 2: Verify the full UI works with dev server + backend running**

```bash
# Terminal 1: backend
cd backend && source .venv/bin/activate && uvicorn backend.main:app --reload

# Terminal 2: frontend
cd frontend && npm run dev
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/yarns-page.tsx
git commit -m "Compose yarns page with all components"
```

---

### Task 23: Frontend testing setup

**Files:**
- Modify: `frontend/package.json` (add test dependencies)
- Create: `frontend/src/mocks/handlers.ts`
- Create: `frontend/src/mocks/server.ts`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/pages/yarns-page.test.tsx`

- [ ] **Step 1: Install test dependencies**

```bash
cd frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event msw jsdom
```

- [ ] **Step 2: Configure Vitest**

Add to `vite.config.ts`:
```typescript
/// <reference types="vitest/config" />
// In defineConfig, add:
test: {
  globals: true,
  environment: "jsdom",
  setupFiles: "./src/test/setup.ts",
}
```

- [ ] **Step 3: Create test setup file**

```typescript
// frontend/src/test/setup.ts
import "@testing-library/jest-dom";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "../mocks/server";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

- [ ] **Step 4: Create MSW handlers**

```typescript
// frontend/src/mocks/handlers.ts
import { http, HttpResponse } from "msw";

const mockYarns = [
  {
    id: 1,
    name: "Test Yarn",
    weight: "DK",
    colour: "Red",
    fibre: "Wool",
    metres_per_ball: 100,
    full_balls: 2,
    part_balls: 1,
    extra_metres: null,
    estimated_total_metres: 250,
    intended_project: null,
    notes: null,
    created_at: "2026-01-01T00:00:00",
    updated_at: "2026-01-01T00:00:00",
  },
];

export const handlers = [
  http.get("/api/yarns/", () => HttpResponse.json(mockYarns)),
  http.get("/api/yarns/stats", () =>
    HttpResponse.json({
      total_yarns: 1,
      total_estimated_metres: 250,
      by_weight: { DK: 1 },
      by_fibre: { Wool: 1 },
    })
  ),
  http.post("/api/yarns/", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: 2, ...body, created_at: "2026-01-01T00:00:00", updated_at: "2026-01-01T00:00:00" }, { status: 201 });
  }),
  http.delete("/api/yarns/:id", () => new HttpResponse(null, { status: 204 })),
];
```

```typescript
// frontend/src/mocks/server.ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

- [ ] **Step 5: Write basic page rendering test**

```typescript
// frontend/src/pages/yarns-page.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { YarnsPage } from "./yarns-page";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
}

test("renders yarn list", async () => {
  renderWithProviders(<YarnsPage />);
  await waitFor(() => {
    expect(screen.getByText("Test Yarn")).toBeInTheDocument();
  });
});

test("renders dashboard stats", async () => {
  renderWithProviders(<YarnsPage />);
  await waitFor(() => {
    expect(screen.getByText("250m")).toBeInTheDocument();
  });
});
```

- [ ] **Step 6: Verify tests pass**

```bash
npm run test -- --run
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/mocks/ frontend/src/test/ frontend/src/pages/yarns-page.test.tsx frontend/vite.config.ts
git commit -m "Add frontend testing setup with Vitest and MSW"
```

---

## Chunk 5: Deployment & Final Setup

### Task 24: Multi-stage Dockerfile

**Files:**
- Create: `backend/Dockerfile`

- [ ] **Step 1: Create multi-stage Dockerfile**

```dockerfile
# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY --from=frontend-build /app/backend/static ./backend/static/

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Commit**

```bash
git add backend/Dockerfile
git commit -m "Add multi-stage Dockerfile"
```

---

### Task 25: Docker Compose

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Create docker-compose.yml**

```yaml
services:
  wool:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8001:8000"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

- [ ] **Step 2: Create data/.gitkeep**

```bash
mkdir -p data
touch data/.gitkeep
```

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml data/.gitkeep
git commit -m "Add Docker Compose config on port 8001"
```

---

### Task 26: CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Create CLAUDE.md with project conventions**

Include:
- Project overview (wool stash tracker)
- Tech stack summary
- How to run locally (backend + frontend dev servers)
- How to run tests
- Key conventions (British English, TDD, Alembic for schema changes)
- Project structure overview
- Deployment instructions

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "Add CLAUDE.md with project conventions"
```

---

### Task 27: Final integration test

- [ ] **Step 1: Build and run with Docker Compose**

```bash
docker compose up --build -d
docker compose exec -w /app/backend wool alembic upgrade head
```

- [ ] **Step 2: Seed the database**

```bash
curl -X POST http://localhost:8001/api/yarns/seed
```

- [ ] **Step 3: Verify the app works**

- Open http://localhost:8001 in browser
- Verify dashboard shows stats
- Verify table shows all seeded yarns
- Test search, filter, sort
- Test add, edit, delete
- Verify responsive layout on narrow viewport

- [ ] **Step 4: Push to remote**

```bash
git push origin main
```
