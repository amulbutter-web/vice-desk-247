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
        from src.supervisor.hierarchy import chief_supervisor_instance
        chief_supervisor_instance.start()

@app.on_event("shutdown")
def stop_autonomous_daemon():
    daemon_instance.stop()
    supervisor_instance.stop()
    from src.supervisor.hierarchy import chief_supervisor_instance
    chief_supervisor_instance.stop()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBLIC_PAGES = {"/privacy", "/privacy-policy", "/terms", "/terms-of-service", "/data-deletion",
                "/deletion", "/app_icon.png", "/icon.png", "/api/health",
                "/api/daemon/status", "/api/accounts/instagram/status", "/api/supervisor/directive", "/api/diag/ytdlp",
                "/api/diag/pot", "/api/supervisor/hierarchy"}
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
    from src.supervisor.supervisor_instructions import SUPERVISOR_INSTRUCTIONS
    published_total = daemon_instance.published_count + getattr(daemon_instance, "ig_published_count", 0)
    return {
        "running": daemon_instance.running,
        "current_stream_idx": daemon_instance.current_stream_idx,
        "published_count": daemon_instance.published_count,
        "ig_published_count": getattr(daemon_instance, "ig_published_count", 0),
        "daily_quota_hit": daemon_instance.daily_quota_hit,
        "interval_sec": daemon_instance.interval_sec,
        "supervisor_running": supervisor_instance.running,
        "stall_cycles": supervisor_instance.stall_cycles,
        "mandate": {
            "game": SUPERVISOR_INSTRUCTIONS.get("primary_game", "GTA 6"),
            "daily_target": SUPERVISOR_INSTRUCTIONS.get("target_daily_uploads", 50),
            "creator_count": SUPERVISOR_INSTRUCTIONS.get("creator_count", 15),
            "published_today": published_total,
            "progress_percent": round((published_total / max(1, SUPERVISOR_INSTRUCTIONS.get("target_daily_uploads", 50))) * 100, 1),
        }
    }


@app.get("/api/supervisor/directive")
def get_supervisor_directive():
    from src.supervisor.supervisor_instructions import SUPERVISOR_INSTRUCTIONS
    published_total = daemon_instance.published_count + getattr(daemon_instance, "ig_published_count", 0)
    return {
        "status": "active",
        "supervisor_running": supervisor_instance.running,
        "instructions": SUPERVISOR_INSTRUCTIONS,
        "metrics": {
            "published_total": published_total,
            "target_daily": SUPERVISOR_INSTRUCTIONS.get("target_daily_uploads", 50),
            "progress_percent": round((published_total / max(1, SUPERVISOR_INSTRUCTIONS.get("target_daily_uploads", 50))) * 100, 1),
            "stall_cycles": supervisor_instance.stall_cycles,
        }
    }


@app.get("/api/supervisor/hierarchy")
def get_supervisor_hierarchy():
    from src.supervisor.hierarchy import chief_supervisor_instance
    return chief_supervisor_instance.get_hierarchy_telemetry()


@app.get("/api/diag/ytdlp")
def diag_ytdlp(url: str = "https://www.youtube.com/watch?v=u1OGXGfOEI0"):
    import subprocess, shutil
    ytdlp = shutil.which("yt-dlp") or "yt-dlp"
    
    # Ensure cookie file is found (check repo data first, then /tmp, then env decode)
    cookie_path = Path("/app/data/youtube_cookies.txt")
    if not cookie_path.exists() or cookie_path.stat().st_size == 0:
        cookie_path = Path("data/youtube_cookies.txt")
    if not cookie_path.exists() or cookie_path.stat().st_size == 0:
        cookie_path = Path("/tmp/youtube_cookies.txt")
    
    b64_env = os.getenv("YOUTUBE_COOKIES_BASE64")
    if b64_env and (not cookie_path.exists() or cookie_path.stat().st_size == 0):
        try:
            import re
            clean = re.sub(r'[^A-Za-z0-9+/=]', '', b64_env)
            cookie_path.write_bytes(base64.b64decode(clean))
            cookie_path.chmod(0o600)
        except Exception:
            pass

    cmd = [
        ytdlp,
        "-v",
        "--extractor-args", "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416",
        "--extractor-args", "youtube:player_client=android,web",
        "--skip-download",
    ]
    if cookie_path.exists() and cookie_path.stat().st_size > 0:
        cmd.extend(["--cookies", str(cookie_path)])

    cmd.append(url)
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=25)
    return {
        "returncode": res.returncode,
        "cookie_file_exists": cookie_path.exists(),
        "cookie_file_size": cookie_path.stat().st_size if cookie_path.exists() else 0,
        "env_var_present": bool(b64_env),
        "env_var_len": len(b64_env) if b64_env else 0,
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


@app.get("/api/diag/pot")
def diag_pot():
    import urllib.request
    results = {}
    for path in ["/", "/ping", "/token", "/get_pot"]:
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:4416{path}", timeout=3)
            results[path] = {"code": req.getcode(), "body": req.read().decode(errors="replace")}
        except Exception as e:
            results[path] = {"error": str(e)}
    return results




# Mount Rendered Media Files for Web Previews and Direct Downloads
rendered_dir = Path(__file__).parent.parent.parent / "data" / "rendered"
rendered_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(rendered_dir)), name="media")

# Mount Static Dashboard
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
