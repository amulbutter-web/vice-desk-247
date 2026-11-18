"""
FastAPI Application Entrypoint for Operator Web Dashboard and REST API.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from src.config import settings
from src.db.database import init_db
from src.server.routes import router

app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="Gaming Content Intelligence & Live/Uploaded Clip Automation Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database Schema
init_db()

# Mount API routes
app.include_router(router, prefix="/api")


# Mount Rendered Media Files for Web Previews and Direct Downloads
rendered_dir = Path(__file__).parent.parent.parent / "data" / "rendered"
rendered_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(rendered_dir)), name="media")

# Mount Static Dashboard
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
