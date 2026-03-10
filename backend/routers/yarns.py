from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Yarn, YarnWeight
from backend.schemas import StatsResponse, YarnCreate, YarnResponse, YarnUpdate

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
    yarn = Yarn(**yarn_in.model_dump())
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
    for field, value in yarn_in.model_dump(exclude_unset=True).items():
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
    db.delete(yarn)
    db.commit()
