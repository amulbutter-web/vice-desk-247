"""
FastAPI Application Entrypoint for Operator Web Dashboard and REST API.
"""
import os
import base64
import secrets
import logging
from urllib.parse import urlsplit
from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# Ensure standard production logging with ISO timestamps and info level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

from src.config import settings
from src.db.database import init_db
from src.server.routes import router
from src.server.background_scheduler import daemon_instance
from src.server.supervisor import supervisor_instance
from src.detection.first_time_ledger import FirstTimeLedger

app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="Gaming Content Intelligence & Live/Uploaded Clip Automation Platform",
)

@app.on_event("startup")
def start_autonomous_daemon():
    from src.publishing.owner_release import start as start_owner_release
    start_owner_release()
    # Seed historic First-Time GTA 6 ledger into DB if empty
    try:
        ledger = FirstTimeLedger()
        ledger.seed_initial_catalog()
        # Unstick any blocked / 403 events
        from src.db.database import get_db_session
        from src.db.models import FirstTimeEvent
        with get_db_session() as session:
            stuck = session.query(FirstTimeEvent).filter(
                FirstTimeEvent.stream_url.like("%1GtrjKhSwzM%")
            ).all()
            for s in stuck:
                s.status = "FAILED"
    except Exception as e:
        print(f"Ledger seeding note: {e}")

    if os.environ.get("ENABLE_BACKGROUND_DAEMON", "true").lower() in ("true", "1", "yes"):
        daemon_instance.start()
        supervisor_instance.start()
        supervisor_instance.send_startup_notification()

@app.on_event("shutdown")
def stop_autonomous_daemon():
    daemon_instance.stop()
    supervisor_instance.stop()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBLIC_PAGES = {"/privacy", "/privacy-policy", "/terms", "/terms-of-service", "/data-deletion",
                "/deletion", "/app_icon.png", "/icon.png", "/api/health",
                "/api/daemon/status", "/api/accounts/instagram/status"}
WEBHOOK_PATHS = {prefix + path for prefix in ("", "/api")
                 for path in ("/webhooks/instagram", "/webhook/instagram")}


@app.middleware("http")
async def require_operator(request: Request, call_next):
    path = request.url.path
    if path in WEBHOOK_PATHS or path == "/api/media/upload" or (
        request.method in {"GET", "HEAD"} and (path in PUBLIC_PAGES or path.startswith("/media/"))
    ):
        return await call_next(request)
    password = os.environ.get("VICE_OPERATOR_PASSWORD")
    if not password:
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return await call_next(request)
        return PlainTextResponse("Operator login is not configured", status_code=503)
    expected = b"Basic " + base64.b64encode(("owner:" + password).encode())
    if not secrets.compare_digest(request.headers.get("authorization", "").encode(), expected):
        return PlainTextResponse("Operator login required", status_code=401,
                                 headers={"WWW-Authenticate": 'Basic realm="Vice Desk"'})
    origin = request.headers.get("origin")
    if origin and urlsplit(origin).netloc != request.url.netloc:
        return PlainTextResponse("Cross-origin request rejected", status_code=403)
    return await call_next(request)


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
    expected_token = os.environ.get("META_VERIFY_TOKEN")
    if expected_token and hub_mode == "subscribe" and hub_verify_token == expected_token:
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


@app.get("/app_icon.png")
@app.get("/icon.png")
def get_app_icon():
    icon_path = Path(__file__).parent / "static" / "app_icon.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")


@app.get("/api/daemon/status")
def get_daemon_status():
    return {
        "running": daemon_instance.running,
        "current_stream_idx": daemon_instance.current_stream_idx,
        "published_count": daemon_instance.published_count,
        "ig_published_count": getattr(daemon_instance, "ig_published_count", 0),
        "daily_quota_hit": daemon_instance.daily_quota_hit,
        "interval_sec": daemon_instance.interval_sec,
        "supervisor_running": supervisor_instance.running,
        "stall_cycles": supervisor_instance.stall_cycles,
    }




# Mount Rendered Media Files for Web Previews and Direct Downloads
rendered_dir = Path(__file__).parent.parent.parent / "data" / "rendered"
rendered_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(rendered_dir)), name="media")

# Mount Static Dashboard
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
