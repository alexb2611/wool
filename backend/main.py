from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from starlette.requests import Request
from starlette.responses import Response

from backend.routers import yarns

app = FastAPI(title="Wool Stash Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(yarns.router)

static_dir = Path(__file__).parent / "static"


@app.middleware("http")
async def serve_spa(request: Request, call_next) -> Response:
    response = await call_next(request)
    if response.status_code == 404 and not request.url.path.startswith("/api"):
        index = static_dir / "index.html"
        if index.is_file():
            return FileResponse(str(index))
    return response


# Pattern images directory
pattern_images_dir = Path(__file__).parent.parent / "data" / "pattern_images"
pattern_images_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/api/pattern-images",
    StaticFiles(directory=str(pattern_images_dir)),
    name="pattern-images",
)

if static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(static_dir)), name="static")
