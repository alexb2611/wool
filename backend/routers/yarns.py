import logging
import re
from collections import Counter
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Yarn, YarnWeight
from backend.schemas import StatsResponse, YarnCreate, YarnResponse, YarnUpdate
from backend.scrapers import SCRAPERS, get_scraper
from backend.scrapers.ravelry import scrape_ravelry
from backend.scrapers.schemas import ScrapeRequest

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
    path = (PATTERN_IMAGES_DIR / filename).resolve()
    if path.is_relative_to(PATTERN_IMAGES_DIR.resolve()) and path.is_file():
        path.unlink()


_PATTERN_FIELDS = (
    "pattern_name", "pattern_author", "pattern_suggested_yarn",
    "pattern_yarn_weight", "pattern_image_filename",
)


def _clear_pattern_fields(data: dict) -> None:
    """Set all pattern metadata fields to None."""
    for field in _PATTERN_FIELDS:
        data[field] = None


router = APIRouter(prefix="/api/yarns", tags=["yarns"])


def _compute_estimated_metres(yarn: Yarn) -> int | None:
    if yarn.metres_per_ball is None:
        return None
    return int(
        (yarn.full_balls * yarn.metres_per_ball)
        + (yarn.part_balls * yarn.metres_per_ball * 0.5)
        + (yarn.extra_metres or 0)
    )


# 1. POST / (create)
@router.post("/", response_model=YarnResponse, status_code=201)
def create_yarn(yarn_in: YarnCreate, db: Session = Depends(get_db)):
    data = yarn_in.model_dump()

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


# 2. GET / (list)
@router.get("/", response_model=list[YarnResponse])
def list_yarns(
    q: str | None = Query(None),
    weight: str | None = Query(None),
    fibre: str | None = Query(None),
    has_project: bool | None = Query(None),
    sort_by: str = Query("name"),
    sort_dir: str = Query("asc"),
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    query = db.query(Yarn)

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

    if weight:
        query = query.filter(Yarn.weight == weight)

    if fibre:
        query = query.filter(Yarn.fibre.ilike(f"%{fibre}%"))

    if has_project is True:
        query = query.filter(
            Yarn.intended_project.isnot(None),
            Yarn.intended_project != "",
        )
    elif has_project is False:
        query = query.filter(
            or_(
                Yarn.intended_project.is_(None),
                Yarn.intended_project == "",
            )
        )

    sort_col = getattr(Yarn, sort_by, Yarn.name)
    if sort_dir == "desc":
        sort_col = sort_col.desc()
    query = query.order_by(sort_col)

    return query.offset(offset).limit(limit).all()


# 3. GET /stats
@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    yarns = db.query(Yarn).all()
    total_yarns = len(yarns)
    total_estimated_metres = sum(
        y.estimated_total_metres for y in yarns if y.estimated_total_metres is not None
    )
    by_weight = dict(Counter(y.weight.value for y in yarns))
    by_fibre = dict(Counter(y.fibre for y in yarns))
    return StatsResponse(
        total_yarns=total_yarns,
        total_estimated_metres=total_estimated_metres,
        by_weight=by_weight,
        by_fibre=by_fibre,
    )


# 4. POST /seed
@router.post("/seed")
def seed_yarns(db: Session = Depends(get_db)):
    from backend.seed_data import SEED_YARNS

    created = 0
    skipped = 0
    for yarn_data in SEED_YARNS:
        existing = (
            db.query(Yarn)
            .filter(
                Yarn.name == yarn_data["name"],
                Yarn.colour == yarn_data["colour"],
                Yarn.weight == yarn_data["weight"],
            )
            .first()
        )
        if existing:
            skipped += 1
            continue
        yarn = Yarn(**yarn_data)
        yarn.estimated_total_metres = _compute_estimated_metres(yarn)
        db.add(yarn)
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}


# 4.5 POST /scrape — must be before /{yarn_id} parameterised routes
@router.post("/scrape")
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


# 5. GET /{yarn_id}
@router.get("/{yarn_id}", response_model=YarnResponse)
def get_yarn(yarn_id: int, db: Session = Depends(get_db)):
    yarn = db.query(Yarn).filter(Yarn.id == yarn_id).first()
    if not yarn:
        raise HTTPException(status_code=404, detail="Yarn not found")
    return yarn


# 6. PUT /{yarn_id}
@router.put("/{yarn_id}", response_model=YarnResponse)
def update_yarn(yarn_id: int, yarn_in: YarnUpdate, db: Session = Depends(get_db)):
    yarn = db.query(Yarn).filter(Yarn.id == yarn_id).first()
    if not yarn:
        raise HTTPException(status_code=404, detail="Yarn not found")

    update_data = yarn_in.model_dump(exclude_unset=True)

    if "ravelry_url" in update_data:
        new_url = update_data["ravelry_url"]

        if new_url and not RAVELRY_URL_PATTERN.match(new_url):
            raise HTTPException(status_code=422, detail="Invalid Ravelry URL. Expected: https://www.ravelry.com/patterns/library/...")

        if new_url != yarn.ravelry_url:
            old_image = yarn.pattern_image_filename
            if new_url:
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
                    _clear_pattern_fields(update_data)
            else:
                _clear_pattern_fields(update_data)
            _delete_pattern_image(old_image)

    for field, value in update_data.items():
        setattr(yarn, field, value)
    yarn.estimated_total_metres = _compute_estimated_metres(yarn)
    db.commit()
    db.refresh(yarn)
    return yarn


# 7. DELETE /{yarn_id}
@router.delete("/{yarn_id}", status_code=204)
def delete_yarn(yarn_id: int, db: Session = Depends(get_db)):
    yarn = db.query(Yarn).filter(Yarn.id == yarn_id).first()
    if not yarn:
        raise HTTPException(status_code=404, detail="Yarn not found")
    _delete_pattern_image(yarn.pattern_image_filename)
    db.delete(yarn)
    db.commit()
