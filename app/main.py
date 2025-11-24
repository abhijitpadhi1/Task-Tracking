"""FastAPI application entrypoint."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import __version__
from app.api import api_router
from app.db.duckdb import init_db
from app.db.seeder import seed_static_data

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"

app = FastAPI(
    title="Task Tracking Dashboard",
    version=__version__,
    description="Sequential progress tracker for 20 staged ML repositories",
)

app.include_router(api_router, prefix="/api")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize database schema before serving traffic."""
    init_db()
    seed_static_data()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Serve the main dashboard template."""
    context = {"request": request}
    return templates.TemplateResponse("index.html", context)

