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
