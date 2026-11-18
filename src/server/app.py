"""
FastAPI Application Entrypoint for Operator Web Dashboard and REST API.
"""
import os
from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import PlainTextResponse, FileResponse
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


# Meta / Instagram Webhook root-level endpoints
@app.get("/webhooks/instagram")
@app.get("/webhook/instagram")
def root_verify_instagram_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    expected_token = os.environ.get("META_VERIFY_TOKEN", "vicedesk_meta_verify_2026")
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return PlainTextResponse(content=hub_challenge or "", status_code=200)
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@app.post("/webhooks/instagram")
@app.post("/webhook/instagram")
async def root_receive_instagram_webhook(request: Request):
    return {"status": "EVENT_RECEIVED"}


# Policy and Compliance Pages for Meta / Instagram App Settings
@app.get("/privacy")
@app.get("/privacy-policy")
def get_privacy_page():
    return FileResponse(Path(__file__).parent / "static" / "privacy.html")


@app.get("/terms")
@app.get("/terms-of-service")
def get_terms_page():
    return FileResponse(Path(__file__).parent / "static" / "terms.html")


@app.get("/data-deletion")
@app.get("/deletion")
def get_data_deletion_page():
    return FileResponse(Path(__file__).parent / "static" / "deletion.html")




# Mount Rendered Media Files for Web Previews and Direct Downloads
rendered_dir = Path(__file__).parent.parent.parent / "data" / "rendered"
rendered_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(rendered_dir)), name="media")

# Mount Static Dashboard
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
