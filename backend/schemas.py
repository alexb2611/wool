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
