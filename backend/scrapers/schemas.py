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


class ScrapedPattern(BaseModel):
    name: str | None = None
    author: str | None = None
    suggested_yarn: str | None = None
    yarn_weight: str | None = None
    image_url: str | None = None
    source_url: str
