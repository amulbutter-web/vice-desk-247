"""
FastAPI Application Entrypoint for Operator Web Dashboard and REST API.
"""
import os
import base64
import secrets
import logging
from typing import Optional, Dict, Any, List
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
                "/api/diag/pot", "/api/diag/warp", "/api/supervisor/hierarchy", "/api/diag/sync_cookies"}
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


@app.get("/api/diag/sync_cookies")
@app.post("/api/diag/sync_cookies")
def sync_cookies():
    b64_env = os.getenv("YOUTUBE_COOKIES_BASE64")
    if not b64_env:
        return {"status": "error", "message": "YOUTUBE_COOKIES_BASE64 environment variable not set"}
    try:
        import re, base64
        clean = re.sub(r'[^A-Za-z0-9+/=]', '', b64_env)
        decoded = base64.b64decode(clean)
        for target in [Path("/app/data/youtube_cookies.txt"), Path("/tmp/youtube_cookies.txt"), Path("data/youtube_cookies.txt")]:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(decoded)
                target.chmod(0o600)
            except Exception:
                pass
        return {"status": "ok", "bytes_synced": len(decoded)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/diag/ytdlp")
def diag_ytdlp(
    url: str = "https://www.youtube.com/watch?v=169ZzvPxvvM",
    use_cookies: bool = True,
    client: str = "visionos,ios,web",
    proxy: Optional[str] = None,
    section: Optional[str] = None,
    download: bool = False,
):
    import subprocess, shutil, uuid, re
    ytdlp = shutil.which("yt-dlp") or "yt-dlp"
    
    # Always decode a fresh, pristine temporary cookie file to guarantee yt-dlp never mutates or corrupts the master session
    temp_cookie_path: Optional[Path] = None
    b64_env = os.getenv("YOUTUBE_COOKIES_BASE64")
    
    if use_cookies:
        if b64_env:
            try:
                clean = re.sub(r'[^A-Za-z0-9+/=]', '', b64_env)
                decoded = base64.b64decode(clean)
                if len(decoded) > 500:
                    temp_dir = Path("/tmp") if Path("/tmp").exists() else Path("data/temp")
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    temp_cookie_path = temp_dir / f"diag_cookie_{uuid.uuid4().hex[:8]}.txt"
                    temp_cookie_path.write_bytes(decoded)
                    temp_cookie_path.chmod(0o600)
            except Exception:
                pass

        if not temp_cookie_path:
            for cand in [Path("/app/data/youtube_cookies.txt"), Path("data/youtube_cookies.txt"), Path("/tmp/youtube_cookies.txt")]:
                if cand.exists() and cand.stat().st_size > 500:
                    temp_dir = Path("/tmp") if Path("/tmp").exists() else Path("data/temp")
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    temp_cookie_path = temp_dir / f"diag_cookie_{uuid.uuid4().hex[:8]}.txt"
                    shutil.copy2(cand, temp_cookie_path)
                    break

    cmd = [
        ytdlp,
        "-v",
        "-4",
        "--extractor-args", "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416",
        "--extractor-args", f"youtube:player_client={client}",
        "--socket-timeout", "15",
    ]
    if not download:
        cmd.append("--skip-download")
    else:
        out_file = Path("/app/data/temp/diag_test.mp4")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.unlink(missing_ok=True)
        cmd.extend([
            "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "--force-overwrites",
            "-o", str(out_file),
        ])
        if section:
            cmd.extend(["--download-sections", section])

    if proxy == "warp":
        proxy = "http://127.0.0.1:8080"
    elif proxy == "warp-socks":
        proxy = "socks5h://127.0.0.1:1080"

    if proxy:
        cmd.extend(["--proxy", proxy])
    if use_cookies and temp_cookie_path and temp_cookie_path.exists() and temp_cookie_path.stat().st_size > 0:
        cmd.extend(["--cookies", str(temp_cookie_path)])

    cmd.append(url)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=60)
    finally:
        # Guarantee temporary cookie file is purged so corrupted state never lingers
        if temp_cookie_path and temp_cookie_path.exists():
            temp_cookie_path.unlink(missing_ok=True)
    
    download_info = {}
    if download:
        test_f = Path("/app/data/temp/diag_test.mp4")
        found = None
        if test_f.exists() and test_f.stat().st_size > 500_000:
            found = test_f
        else:
            candidates = list(test_f.parent.glob("diag_test*"))
            if candidates:
                found = max(candidates, key=lambda c: c.stat().st_size)
        download_info = {
            "downloaded": bool(found),
            "path": str(found) if found else None,
            "size_bytes": found.stat().st_size if found else 0,
        }

    cookie_file_exists = bool(temp_cookie_path or (b64_env and len(b64_env) > 500))
    return {
        "returncode": res.returncode,
        "cookie_file_exists": cookie_file_exists,
        "cookie_file_size": len(b64_env) if b64_env else 0,
        "use_cookies": use_cookies,
        "client": client,
        "proxy": proxy,
        "download_info": download_info,
        "env_var_present": bool(b64_env),
        "env_var_len": len(b64_env) if b64_env else 0,
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


@app.get("/api/diag/pot")
def diag_pot():
    import urllib.request
    results = {}
    for path in ["/", "/ping", "/token"]:
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:4416{path}", timeout=3)
            results[path] = {"code": req.getcode(), "body": req.read().decode(errors="replace")}
        except Exception as e:
            results[path] = {"error": str(e)}
    # Test POST /get_pot
    try:
        data = b'{}'
        req_post = urllib.request.Request("http://127.0.0.1:4416/get_pot", data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req_post, timeout=5)
        results["/get_pot_post"] = {"code": resp.getcode(), "body": resp.read().decode(errors="replace")}
    except Exception as pe:
        results["/get_pot_post"] = {"error": str(pe)}
    return results


@app.get("/api/diag/warp")
def diag_warp():
    import subprocess
    output = {}
    profile_path = Path("/app/data/warp/wgcf-profile.conf")
    if profile_path.exists():
        lines = []
        for line in profile_path.read_text().splitlines():
            if "PrivateKey" in line:
                lines.append("PrivateKey = [REDACTED]")
            else:
                lines.append(line)
        output["profile"] = "\n".join(lines)
    
    # Direct trace (baseline)
    try:
        res_dir = subprocess.run(
            ["curl", "-s", "--max-time", "6", "https://www.cloudflare.com/cdn-cgi/trace"],
            capture_output=True, text=True, timeout=8
        )
        output["direct_trace"] = res_dir.stdout
    except Exception as de:
        output["direct_trace"] = f"error: {de}"

    # Test HTTP proxy (:8080)
    try:
        res_http = subprocess.run(
            ["curl", "-s", "--max-time", "10", "--proxy", "http://127.0.0.1:8080", "https://api.ipify.org?format=json"],
            capture_output=True, text=True, timeout=12
        )
        output["http_proxy_8080"] = {
            "status": "ok" if res_http.returncode == 0 else "failed",
            "returncode": res_http.returncode,
            "ip": res_http.stdout.strip(),
            "error": res_http.stderr,
        }
    except Exception as e:
        output["http_proxy_8080"] = {"status": "error", "error": str(e)}

    # Test SOCKS5 proxy (:1080)
    try:
        res_socks = subprocess.run(
            ["curl", "-s", "--max-time", "10", "--proxy", "socks5h://127.0.0.1:1080", "https://api.ipify.org?format=json"],
            capture_output=True, text=True, timeout=12
        )
        output["socks5_proxy_1080"] = {
            "status": "ok" if res_socks.returncode == 0 else "failed",
            "returncode": res_socks.returncode,
            "ip": res_socks.stdout.strip(),
            "error": res_socks.stderr,
        }
    except Exception as e:
        output["socks5_proxy_1080"] = {"status": "error", "error": str(e)}

    return output




# Mount Rendered Media Files for Web Previews and Direct Downloads
rendered_dir = Path(__file__).parent.parent.parent / "data" / "rendered"
rendered_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(rendered_dir)), name="media")

# Mount Static Dashboard
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
