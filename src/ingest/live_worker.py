"""
Automated Live Ingest and Clipping Worker.
Processes live stream feeds, YouTube/Twitch VODs (e.g. CarryMinati, Mythpat, Typical Gamer, Speed),
and executes the complete multi-signal detection, Groq Whisper transcription,
kinetic editorial planning, FFmpeg rendering, and QC pipeline asynchronously.
"""
import os
import shutil
import subprocess
import uuid
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from src.config import settings
from src.db.database import get_db_session
from src.db.repository import Repository
from src.db.models import EventRevision, RenderedAsset, QCAudit
from src.ingest.probe import MediaProbe
from src.detection.audio_detector import AudioDetector
from src.detection.visual_detector import VisualDetector
from src.detection.narrative_boundary import NarrativeBoundaryEngine
from src.detection.false_positive_filter import FalsePositiveFilter
from src.editor.planner import EditorialPlanner
from src.editor.subtitles import SubtitleGenerator
from src.editor.renderer import VideoRenderer
from src.editor.transcription import GroqTranscriptionEngine
from src.core.groq_pool import GroqPool
from src.qc.hard_gates import HardQualityGates
from src.qc.editorial_judge import EditorialJudge
from src.qc.supervisor import QCSupervisor
from src.editor.clip_copy import clip_copy
from src.db.database import init_db

logger = logging.getLogger("live_worker")
groq_pool = GroqPool()

# Verified pool of Webshare residential proxies for automatic failover
# Top 3 are verified unblocked on YouTube live stream downloads
WEBSHARE_PROXIES = [
    "http://vkfhjzqg:e95qnn2d11ml@84.247.60.125:6095",
    "http://vkfhjzqg:e95qnn2d11ml@64.137.10.153:5803",
    "http://vkfhjzqg:e95qnn2d11ml@23.26.71.145:5628",
    "http://vkfhjzqg:e95qnn2d11ml@45.38.107.97:6014",
    "http://vkfhjzqg:e95qnn2d11ml@64.137.96.74:6641",
    "http://vkfhjzqg:e95qnn2d11ml@198.23.243.226:6361",
    "http://vkfhjzqg:e95qnn2d11ml@38.154.185.97:6370",
    "http://vkfhjzqg:e95qnn2d11ml@191.96.254.138:6185",
    "http://vkfhjzqg:e95qnn2d11ml@198.46.161.42:5092",
    "http://vkfhjzqg:e95qnn2d11ml@104.164.49.38:7693",
]

def get_candidate_proxies() -> List[str]:
    primary = os.getenv("YOUTUBE_PROXY")
    # If YOUTUBE_PROXY is explicitly 'none' or 'direct', do NOT use proxy pool
    if primary in ("none", "direct"):
        return []
    
    pool = []
    # Priority 1: Cloudflare WARP local bridge (port 8080 HTTP, port 1080 SOCKS5)
    import socket
    for p_addr, p_url in [
        (("127.0.0.1", 8080), "http://127.0.0.1:8080"),
        (("127.0.0.1", 1080), "socks5://127.0.0.1:1080"),
    ]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            if s.connect_ex(p_addr) == 0:
                pool.append(p_url)
            s.close()
        except Exception:
            pass

    if primary and primary not in pool:
        pool.insert(0, primary)
    for wp in WEBSHARE_PROXIES:
        if wp not in pool:
            pool.append(wp)
    return pool

def _proxy_is_dead(stderr: str) -> bool:
    """Returns True if the proxy itself is dead (402 Payment Required / connection refused / error page)."""
    dead_signals = [
        "402 Payment Required",
        "Tunnel connection failed",
        "Unable to connect to proxy",
        "ProxyError",
        "Cannot connect to proxy",
        "invalid start byte",
        "codec can't decode",
    ]
    return any(sig.lower() in stderr.lower() for sig in dead_signals)

# Global rate-limiter: only 1 yt-dlp process runs at a time across all workers
# Prevents 3 workers simultaneously hammering YouTube's rate-limit detection
_ytdlp_global_lock = threading.Semaphore(1)
_ytdlp_last_call_time: float = 0.0
_YTDLP_MIN_INTERVAL_SEC = 5  # Throttled between any two yt-dlp calls globally


class LiveIngestWorker:
    def __init__(self, probe: Optional[MediaProbe] = None, ffmpeg_bin: Optional[str] = None):
        init_db()
        self.probe = probe or MediaProbe()
        self.ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_binary
        self.ytdlp_bin = shutil.which("yt-dlp") or r"C:\Users\rudra\AppData\Local\Programs\Python\Python313\Scripts\yt-dlp.EXE"

    def fetch_stream_sample(self, url: str, output_dir: Path, section_range: str = "*00:15:00-00:16:15") -> Path:
        """
        Fetches genuine 1080p stream footage for the exact section range.
        Uses yt-dlp -g + FFmpeg direct stream slicing with HTTP User-Agent.
        NEVER falls back to dummy sample footage for social publishing.
        """
        global _ytdlp_last_call_time
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Local file passthrough
        local_path = Path(url)
        if local_path.is_file():
            return local_path

        # 2. Parse section range
        clean = section_range.lstrip("*").strip()
        if "-" in clean:
            parts = clean.split("-")
            start_str = parts[0].strip()
            end_str = parts[1].strip()

            def _to_sec(t):
                nums = list(map(int, t.split(":")))
                if len(nums) == 3:
                    return nums[0] * 3600 + nums[1] * 60 + nums[2]
                elif len(nums) == 2:
                    return nums[0] * 60 + nums[1]
                return int(nums[0])

            duration_sec = max(20, _to_sec(end_str) - _to_sec(start_str))
        else:
            start_str = clean
            duration_sec = 65

        from src.ingest.owner_archive import archive_excerpt
        archived = archive_excerpt(url, start_str, duration_sec, output_dir, self.ffmpeg_bin)
        if archived is not None:
            logger.info("[INGEST] Using matching operator-supplied original for requested interval")
            return archived

        target_file = output_dir / f"stream_{uuid.uuid4().hex[:8]}.mp4"
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Multi-proxy candidate pool with automatic failover
        candidate_proxies = get_candidate_proxies()
        # Locate valid cookies file (prioritize verified repo file, then /tmp)
        cookies_cand = Path("/app/data/youtube_cookies.txt")
        if not cookies_cand.exists() or cookies_cand.stat().st_size == 0:
            cookies_cand = Path("data/youtube_cookies.txt")
        if not cookies_cand.exists() or cookies_cand.stat().st_size == 0:
            cookies_cand = Path("/tmp/youtube_cookies.txt")

        # Fallback to env decoding only if file does not exist
        if not cookies_cand.exists() or cookies_cand.stat().st_size == 0:
            b64_env = os.getenv("YOUTUBE_COOKIES_BASE64")
            if b64_env:
                try:
                    import base64, re
                    clean = re.sub(r'[^A-Za-z0-9+/=]', '', b64_env)
                    cookies_cand = Path("/tmp/youtube_cookies.txt")
                    cookies_cand.write_bytes(base64.b64decode(clean))
                    cookies_cand.chmod(0o600)
                except Exception as _ce:
                    logger.warning(f"Failed to decode YOUTUBE_COOKIES_BASE64: {_ce}")

        has_cookies = (cookies_cand.exists() and cookies_cand.stat().st_size > 0)

        # 3. Primary Method: Direct yt-dlp slice with visionos,ios,web and bgutil-pot (via Cloudflare WARP if active)
        if os.path.exists(self.ytdlp_bin) and (url.startswith("http://") or url.startswith("https://")):
            local_warp = [p for p in candidate_proxies if "127.0.0.1" in p]
            warp_proxy = local_warp[0] if local_warp else None

            # Primary strategies ladder:
            # 1. Direct connection + cookies (proven fastest & most reliable on Railway with bgutil-pot + visionos,ios,web)
            # 2. Direct connection without cookies
            # 3. WARP proxy + cookies (if WARP active)
            # 4. WARP proxy without cookies
            primary_strategies = []
            if has_cookies:
                primary_strategies.append(["--cookies", str(cookies_cand)])
            primary_strategies.append([])
            if warp_proxy and has_cookies:
                primary_strategies.append(["--proxy", warp_proxy, "--cookies", str(cookies_cand)])
            if warp_proxy:
                primary_strategies.append(["--proxy", warp_proxy])

            for auth_args_primary in primary_strategies:
                is_cookie = "--cookies" in auth_args_primary
                is_proxy = "--proxy" in auth_args_primary
                proxy_label = [auth_args_primary[i+1] for i, a in enumerate(auth_args_primary) if a == "--proxy"]
                proxy_str = proxy_label[0] if proxy_label else "direct"
                logger.info(f"[INGEST] Downloading stream footage [{section_range}] via yt-dlp ({proxy_str}, cookies={'yes' if is_cookie else 'no'})...")
                cmd_cookie_direct = [
                    self.ytdlp_bin,
                    "-4",
                    "--extractor-args", "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416",
                    "--extractor-args", "youtube:player_client=visionos,ios,web",
                    "--socket-timeout", "15",
                    "--sleep-interval", "1",
                    "--max-sleep-interval", "3",
                    "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
                    "--download-sections", section_range,
                    "--force-overwrites",
                    "--no-playlist",
                    "--no-warnings",
                ] + auth_args_primary + [
                    "-o", str(target_file),
                    url,
                ]
                try:
                    with _ytdlp_global_lock:
                        elapsed = time.monotonic() - _ytdlp_last_call_time
                        if elapsed < _YTDLP_MIN_INTERVAL_SEC:
                            wait = _YTDLP_MIN_INTERVAL_SEC - elapsed
                            time.sleep(wait)
                        _ytdlp_last_call_time = time.monotonic()
                        res_cookie = subprocess.run(cmd_cookie_direct, capture_output=True, text=True, errors="replace", timeout=120)
                    if res_cookie.returncode == 0 and target_file.exists() and target_file.stat().st_size > 500_000:
                        probe_check = self.probe.probe(str(target_file))
                        if probe_check.get("has_video") and probe_check.get("duration_ms", 0) > 10_000:
                            logger.info(f"[INGEST] Direct capture SUCCESS ({proxy_str}, cookies={'yes' if is_cookie else 'no'}): {target_file} ({target_file.stat().st_size / (1024*1024):.2f} MB)")
                            return target_file
                    else:
                        err_snip = (res_cookie.stderr or '')[-250:]
                        logger.warning(f"[INGEST] Direct slice ({proxy_str}, cookies={'yes' if is_cookie else 'no'}) returned code {res_cookie.returncode}: {err_snip}")
                        if is_cookie and any(sig in err_snip for sig in ["cookies are no longer valid", "confirm you're not a bot", "confirm you’re not a bot", "LOGIN_REQUIRED"]):
                            has_cookies = False
                            continue
                except Exception as ce:
                    logger.warning(f"[INGEST] Direct slice exception: {ce}")

        # 3b. Secondary Method: Multi-proxy failover & auto-drop expired cookies (used if no cookies or as fallback)
        # Sentinel: if all proxies are dead (402), we try without proxy as last resort
        all_proxies_dead = False
        dead_proxy_count = 0
        if os.path.exists(self.ytdlp_bin) and (url.startswith("http://") or url.startswith("https://")):
            for p_idx, current_proxy in enumerate(candidate_proxies):
                # Determine auth strategies for this proxy: first with cookies (if any), then without cookies
                strategies = []
                if has_cookies:
                    strategies.append(["--cookies", str(cookies_cand), "--proxy", current_proxy])
                strategies.append(["--proxy", current_proxy])

                for auth_args in strategies:
                    try:
                        logger.info(f"[INGEST] Downloading stream footage [{section_range}] via yt-dlp (proxy #{p_idx+1}: {current_proxy.split('@')[-1]}, cookies={'yes' if '--cookies' in auth_args else 'no'})...")
                        cmd_native = [
                            self.ytdlp_bin,
                            "--no-plugin-dirs",
                            "-4",
                            "--sleep-interval", "3",
                            "--max-sleep-interval", "7",
                            "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
                            "--download-sections", section_range,
                            "--force-overwrites",
                            "--no-playlist",
                            "--no-warnings",
                            "-o", str(target_file),
                        ] + auth_args + [url]

                        with _ytdlp_global_lock:
                            elapsed = time.monotonic() - _ytdlp_last_call_time
                            if elapsed < _YTDLP_MIN_INTERVAL_SEC:
                                wait = _YTDLP_MIN_INTERVAL_SEC - elapsed
                                logger.info(f"[RateGuard] Throttling yt-dlp — waiting {wait:.1f}s before next call")
                                time.sleep(wait)
                            _ytdlp_last_call_time = time.monotonic()
                            res_nat = subprocess.run(cmd_native, capture_output=True, text=True, errors="replace", timeout=180)

                        if res_nat.returncode == 0 and target_file.exists() and target_file.stat().st_size > 500_000:
                            try:
                                probe_check = self.probe.probe(str(target_file))
                                if probe_check.get("has_video") and probe_check.get("duration_ms", 0) > 10_000:
                                    logger.info(f"Native yt-dlp captured verified footage: {target_file} ({target_file.stat().st_size / (1024*1024):.2f} MB)")
                                    return target_file
                                else:
                                    logger.warning(f"Native yt-dlp file invalid/too short ({probe_check.get('duration_ms', 0)}ms) — trying next")
                                    target_file.unlink(missing_ok=True)
                            except Exception as p_err:
                                logger.warning(f"Native yt-dlp probe error: {p_err}")
                                target_file.unlink(missing_ok=True)
                        else:
                            stderr_out = res_nat.stderr if res_nat.stderr else ""
                            # Self-healing: if cookies were rejected or bot verification hit, drop cookies immediately
                            if "--cookies" in auth_args and any(sig in stderr_out for sig in ["cookies are no longer valid", "confirm you're not a bot", "confirm you’re not a bot", "Use --cookies", "from-browser"]):
                                logger.warning(f"[INGEST] YouTube rejected cookies on proxy {current_proxy.split('@')[-1]}. Auto-dropping cookies and retrying clean proxy...")
                                has_cookies = False  # Don't try cookies again
                                continue
                            logger.warning(f"[INGEST] yt-dlp returned code {res_nat.returncode} on proxy {current_proxy.split('@')[-1]}: {stderr_out[-300:]}")
                            # Detect dead proxy (402 Payment Required) — count how many consecutive dead
                            if _proxy_is_dead(stderr_out):
                                dead_proxy_count += 1
                                logger.warning(f"[INGEST] Proxy #{p_idx+1} is dead (402/ConnErr). Dead count: {dead_proxy_count}/{len(candidate_proxies[:4])}")
                            # Break to next proxy
                            break
                    except Exception as en:
                        logger.warning(f"[INGEST] yt-dlp slice error on proxy {current_proxy.split('@')[-1]}: {en}")
                        break

            # 3b. ALL-PROXY-DEAD FALLBACK: If all proxies returned 402, try direct (Railway's own IP)
            # Railway IPs are US datacenter — YouTube allows them without proxy for non-geo-restricted content
            if dead_proxy_count >= min(2, len(candidate_proxies[:4])):
                logger.warning(f"[INGEST] All {dead_proxy_count} tried proxies are dead (402). Attempting DIRECT download (no proxy) as self-healing fallback...")
                for auth_args_direct in ([["--cookies", str(cookies_cand)]] if has_cookies else []) + [[]]:
                    try:
                        cmd_direct = [
                            self.ytdlp_bin,
                            "-4",
                            "--extractor-args", "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416",
                            "--extractor-args", "youtube:player_client=visionos,ios,web",
                            "--sleep-interval", "3",
                            "--max-sleep-interval", "7",
                            "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
                            "--download-sections", section_range,
                            "--force-overwrites",
                            "--no-playlist",
                            "--no-warnings",
                            "-o", str(target_file),
                        ] + auth_args_direct + [url]
                        with _ytdlp_global_lock:
                            elapsed = time.monotonic() - _ytdlp_last_call_time
                            if elapsed < _YTDLP_MIN_INTERVAL_SEC:
                                time.sleep(_YTDLP_MIN_INTERVAL_SEC - elapsed)
                            _ytdlp_last_call_time = time.monotonic()
                            res_direct = subprocess.run(cmd_direct, capture_output=True, text=True, errors="replace", timeout=180)
                        if res_direct.returncode == 0 and target_file.exists() and target_file.stat().st_size > 500_000:
                            probe_check = self.probe.probe(str(target_file))
                            if probe_check.get("has_video") and probe_check.get("duration_ms", 0) > 10_000:
                                logger.info(f"[INGEST][DIRECT] yt-dlp direct download succeeded: {target_file} ({target_file.stat().st_size / (1024*1024):.2f} MB)")
                                return target_file
                        else:
                            stderr_direct = res_direct.stderr or ""
                            if "--cookies" in auth_args_direct and any(sig in stderr_direct for sig in ["cookies are no longer valid", "confirm you're not a bot", "confirm you’re not a bot", "Use --cookies", "from-browser", "LOGIN_REQUIRED"]):
                                has_cookies = False
                                continue
                            logger.warning(f"[INGEST][DIRECT] Direct download also failed: {stderr_direct[-200:]}")
                            break
                    except Exception as de:
                        logger.warning(f"[INGEST][DIRECT] Direct download exception: {de}")
                        break

            # 4. Fallback Method: yt-dlp -g + FFmpeg direct slice with residential proxy
            for current_proxy in candidate_proxies[:2]:
                try:
                    logger.info(f"Fallback: Extracting live stream URLs for {url} [{start_str} +{duration_sec}s] via proxy {current_proxy.split('@')[-1]}...")
                    cmd_g = [
                        self.ytdlp_bin,
                        "--no-plugin-dirs",
                        "-4",
                        "--proxy", current_proxy,
                        "--sleep-interval", "3",
                        "--max-sleep-interval", "7",
                        "-g",
                        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
                        "--no-warnings",
                        url,
                    ]
                    with _ytdlp_global_lock:
                        elapsed = time.monotonic() - _ytdlp_last_call_time
                        if elapsed < _YTDLP_MIN_INTERVAL_SEC:
                            time.sleep(_YTDLP_MIN_INTERVAL_SEC - elapsed)
                        _ytdlp_last_call_time = time.monotonic()
                        res_g = subprocess.run(cmd_g, capture_output=True, text=True, errors="replace", timeout=30)

                    if res_g.returncode == 0 and res_g.stdout.strip():
                        stream_urls = res_g.stdout.strip().splitlines()
                        if len(stream_urls) >= 2:
                            v_url, a_url = stream_urls[0], stream_urls[1]
                            cmd_ff = [
                                self.ffmpeg_bin, "-y",
                                "-threads", "2",
                                "-http_proxy", current_proxy,
                                "-protocol_whitelist", "file,http,https,tcp,tls",
                                "-reconnect", "1",
                                "-reconnect_at_eof", "1",
                                "-reconnect_streamed", "1",
                                "-reconnect_delay_max", "5",
                                "-user_agent", ua,
                                "-ss", start_str,
                                "-i", v_url,
                                "-http_proxy", current_proxy,
                                "-protocol_whitelist", "file,http,https,tcp,tls",
                                "-user_agent", ua,
                                "-ss", start_str,
                                "-i", a_url,
                                "-t", str(duration_sec),
                                "-c:v", "copy",
                                "-c:a", "aac",
                                str(target_file),
                            ]
                        else:
                            v_url = stream_urls[0]
                            cmd_ff = [
                                self.ffmpeg_bin, "-y",
                                "-threads", "2",
                                "-http_proxy", current_proxy,
                                "-protocol_whitelist", "file,http,https,tcp,tls",
                                "-reconnect", "1",
                                "-reconnect_at_eof", "1",
                                "-reconnect_streamed", "1",
                                "-reconnect_delay_max", "5",
                                "-user_agent", ua,
                                "-ss", start_str,
                                "-i", v_url,
                                "-t", str(duration_sec),
                                "-c", "copy",
                                str(target_file),
                            ]

                        res_ff = subprocess.run(cmd_ff, capture_output=True, text=True, timeout=120)
                        if res_ff.returncode == 0 and target_file.exists() and target_file.stat().st_size > 500_000:
                            try:
                                probe_check = self.probe.probe(str(target_file))
                                if probe_check.get("has_video") and probe_check.get("duration_ms", 0) > 10_000:
                                    logger.info(f"Fallback stream footage verified: {target_file} ({target_file.stat().st_size / (1024*1024):.2f} MB)")
                                    return target_file
                                else:
                                    target_file.unlink(missing_ok=True)
                            except Exception as p_err:
                                logger.warning(f"Fallback probe error: {p_err}")
                                target_file.unlink(missing_ok=True)
                        else:
                            logger.warning(f"Fallback FFmpeg direct slice failed (code {res_ff.returncode}) on proxy {current_proxy.split('@')[-1]}")
                except Exception as eg:
                    logger.warning(f"Direct stream slice error: {eg}")

        # CRITICAL HARD QUALITY GATE: Never return dummy sample footage for social media publishing
        raise RuntimeError(f"Unable to download genuine live stream footage from {url}. Cycle aborted to prevent duplicate/dummy posting.")

    def process_url_job(
        self,
        url: str,
        creator_name: str = "iShowSpeed",
        game: str = "GTA 6",
        layout_mode: str = "blur_fill",
        publish_to_youtube: bool = False,
        section_range: str = "*00:15:00-00:16:15",
        viral_hook: Optional[str] = None,
        caption: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes complete end-to-end processing pipeline for a stream:
        Ingest -> Probing -> Audio/Visual Detection -> Narrative Boundary ->
        Groq Whisper Speech Transcription -> Kinetic ASS Subtitles ->
        Editorial Planning -> FFmpeg Rendering -> QC Gate -> DB Registration.
        """
        trace_id = str(uuid.uuid4())
        logger.info(f"Starting Live Ingest Job [Trace: {trace_id}] for {creator_name} ({url})")

        ingest_dir = settings.media_dir / "ingest"
        try:
            source_media_path = self.fetch_stream_sample(url, ingest_dir, section_range=section_range)
            # 1. Probing & Checksum
            meta = self.probe.probe(str(source_media_path))
            if not meta.get("has_video"):
                raise RuntimeError("Source media contains no video stream")
            sha256 = self.probe.compute_sha256(str(source_media_path))
        except Exception as dl_err:
            logger.error(f"[INGEST] Genuine footage fetch/probe failed for {creator_name}: {dl_err}")
            return {
                "status": "FAILED",
                "qc_passed": False,
                "error": str(dl_err),
                "output_path": None,
                "render_id": None,
            }

        # 2. Multi-Signal Detection
        audio_det = AudioDetector(ffmpeg_binary=self.ffmpeg_bin)
        visual_det = VisualDetector(ffmpeg_binary=self.ffmpeg_bin)
        boundary_engine = NarrativeBoundaryEngine()
        fp_filter = FalsePositiveFilter()

        audio_timeline = audio_det.analyze_audio(str(source_media_path))
        audio_peaks = audio_det.find_audio_peaks(audio_timeline, threshold=0.55)
        scene_cuts = visual_det.detect_scene_cuts(str(source_media_path))
        black_frames = visual_det.detect_black_frames(str(source_media_path))
        freeze_frames = visual_det.detect_freeze_frames(str(source_media_path))

        # Determine peak
        peak_ms = max(audio_peaks, key=lambda p: p["rms_db"])["timestamp_ms"] if audio_peaks else meta["duration_ms"] // 2

        # 3. Narrative Boundary Expansion
        boundaries = boundary_engine.expand_event_boundaries(
            peak_ms=peak_ms,
            source_duration_ms=meta["duration_ms"],
            scene_cuts_ms=scene_cuts,
        )

        # 4. False Positive Filtering
        is_valid, fp_reason, _ = fp_filter.evaluate_candidate(
            event_candidate=boundaries,
            black_frames=black_frames,
            freeze_frames=freeze_frames,
            audio_excitement=0.88 if audio_peaks else 0.6,
            visual_activity=0.80,
        )

        # 5. Transcription via Groq Whisper with exact word-level millisecond timestamps
        transcription_engine = GroqTranscriptionEngine(ffmpeg_bin=self.ffmpeg_bin)
        lang_hint = "hi" if creator_name in ("Mythpat", "CarryisLive", "CarryMinati", "Dattrax Plays", "RakaZone Gaming", "AS Gaming", "8bit Goldy") else None

        start_sec = boundaries["window_start_ms"] / 1000.0
        duration_sec = boundaries["duration_ms"] / 1000.0

        trans_res = transcription_engine.transcribe_video_interval(
            video_path=str(source_media_path),
            start_sec=start_sec,
            duration_sec=duration_sec,
            language=lang_hint,
        )
        words = trans_res.get("words", [])
        transcript_text = trans_res.get("text", "")

        # 6. Editorial Copy (Viral Hook, Title, Storytelling Caption)
        if viral_hook and viral_hook.strip():
            ai_hook = viral_hook.strip()
            ai_caption = caption or f"{ai_hook} in GTA 6!"
            ai_title = title or f"{creator_name} GTA 6 | {ai_hook} #Shorts"
        else:
            try:
                ai_hook = groq_pool.generate_viral_hook(creator_name=creator_name, game=game, context_notes=transcript_text)
                reels_meta = groq_pool.generate_reels_metadata(creator_name=creator_name, game=game, hook=ai_hook, context_notes=transcript_text)
                ai_caption = reels_meta.get("caption", f"{creator_name} GTA 6 gameplay moment!")
                ai_title = f"{creator_name} | {ai_hook} #Shorts"
            except Exception as gr_err:
                logger.warning("[LIVE_WORKER] Groq viral hook fallback: %s", gr_err)
                fb_meta = clip_copy(creator_name, game, boundaries, scene_cuts, peak_ms if audio_peaks else None)
                ai_hook = fb_meta["hook"]
                ai_caption = fb_meta["caption"]
                ai_title = fb_meta["title"]

        # 7. Subtitle Generation (Hormozi Kinetic ASS)
        ass_sub_path = settings.rendered_dir / f"subs_{trace_id[:8]}.ass"
        fallback_cues = []
        if not words:
            hi_cues = [
                "BHAI KYA SCENE HAI! 😂",
                "5-STAR WANTED LEVEL ESCAPE! 🚨",
                "SECRET LOCATION MIL GAYI! 🤯",
                "NEXT LEVEL PHYSICS! 😱",
                "CHALAN KATEGA BHAI! 🤣",
                "UNREAL VICE CITY GRAPHICS! ✨",
            ]
            en_cues = [
                "5-STAR POLICE ESCAPE! 🚨",
                "NEXT-GEN GRAPHICS ARE UNREAL! 🔥",
                "SECRET LOCATION DISCOVERED! 🤯",
                "HIGH SPEED PURSUIT! ⚡",
                "INSANE RAGDOLL PHYSICS! 💀",
                "VICE CITY IS MASSIVE! 🌴",
            ]
            cues_list = hi_cues if lang_hint == "hi" else en_cues
            cut_start = boundaries["window_start_ms"]
            for idx, cut_t in enumerate(scene_cuts):
                if cut_start + 1500 <= cut_t <= boundaries["window_end_ms"] - 1500:
                    rel_ms = cut_t - cut_start
                    fallback_cues.append({
                        "start_ms": rel_ms,
                        "end_ms": rel_ms + 2500,
                        "text": cues_list[idx % len(cues_list)],
                    })

        SubtitleGenerator().generate_ass(
            words=words,
            output_ass_path=str(ass_sub_path),
            hook_text=ai_hook,
            fallback_cues=fallback_cues,
            hook_duration_ms=7000,
        )

        # 8. Editorial Planning
        # If source media is a pre-sliced segment (duration < boundaries["window_end_ms"]),
        # normalize edit plan boundaries to start from 0 to prevent FFmpeg seeking past EOF
        local_dur_ms = meta.get("duration_ms", 0) if isinstance(meta, dict) else 0
        render_boundaries = dict(boundaries)
        if local_dur_ms > 0 and (boundaries.get("window_start_ms", 0) >= local_dur_ms or boundaries.get("window_end_ms", 0) > local_dur_ms):
            logger.info(f"Normalizing pre-sliced stream sample: duration {local_dur_ms}ms (mapping start from 0ms)")
            orig_span = max(15000, boundaries.get("window_end_ms", 60000) - boundaries.get("window_start_ms", 0))
            render_boundaries["window_start_ms"] = 0
            render_boundaries["window_end_ms"] = min(local_dur_ms, orig_span)

        planner = EditorialPlanner(canvas_width=1080, canvas_height=1920, fps=60.0)
        plan_id = f"plan-{uuid.uuid4().hex[:8]}"
        edit_plan = planner.create_edit_plan(
            plan_id=plan_id,
            trace_id=trace_id,
            event_revision_id="rev-1",
            media_asset_id=f"asset-{sha256[:8]}",
            event_candidate=render_boundaries,
            platform="instagram",
            layout_mode=layout_mode,
        )

        # 9. Render Vertical 9:16 Video
        render_id = f"render-{uuid.uuid4().hex[:8]}"
        output_mp4_path = settings.rendered_dir / f"{render_id}.mp4"
        renderer = VideoRenderer(probe=self.probe, ffmpeg_bin=self.ffmpeg_bin)
        render_meta = renderer.render_clip(
            source_path=str(source_media_path),
            output_path=str(output_mp4_path),
            edit_plan=edit_plan,
            ass_subtitle_path=str(ass_sub_path) if ass_sub_path.exists() else None,
            timeout_sec=420,
        )
        if ass_sub_path.exists():
            ass_sub_path.unlink(missing_ok=True)

        # 10. Automated QC Hard Gates & Supervisor
        hard_gates = HardQualityGates(probe=self.probe, visual_detector=visual_det)
        judge = EditorialJudge()
        supervisor = QCSupervisor(hard_gates=hard_gates, judge=judge)
        qc_res = supervisor.audit_render(
            audit_id=f"qc-{uuid.uuid4().hex[:8]}",
            trace_id=trace_id,
            render_id=render_id,
            media_path=str(output_mp4_path),
            event_candidate=boundaries,
            edit_plan=edit_plan.model_dump(),
        )
        all_hard_pass = all(g.pass_ for g in qc_res.hard_gates)

        # 11. Register in Database
        with get_db_session() as session:
            # Register in database
            repo = Repository(session)
            creator_key = creator_name.lower().replace(" ", "_")
            source = repo.create_or_get_source(creator_key, "youtube" if "youtu" in url else "twitch", url, "verified")
            asset = repo.create_media_asset(
                storage_ref=str(source_media_path),
                sha256=sha256,
                source_id=source.id,
                source_duration_ms=meta["duration_ms"],
                rights_status="verified",
            )
            rev = EventRevision(
                event_key=f"ev-{trace_id[:8]}",
                media_id=asset.id,
                revision=1,
                source_start_ms=boundaries["window_start_ms"],
                source_end_ms=boundaries["window_end_ms"],
                payload=boundaries,
                provenance={"detector": "live_worker_v4"},
            )
            session.add(rev)
            session.flush()

            rendered = RenderedAsset(
                id=render_id,
                event_revision_id=rev.id,
                sha256=render_meta["sha256"],
                output_ref=str(output_mp4_path),
                target_platform="instagram",
                qc_state="pass" if all_hard_pass else "failed",
            )
            session.add(rendered)
            session.flush()

            audit = QCAudit(
                render_id=rendered.id,
                evaluator_type="deterministic",
                evaluator_version="v4.0",
                result=qc_res.model_dump(by_alias=True),
                is_hard_pass=all_hard_pass,
            )
            session.add(audit)
            session.flush()

        # DISK SAFETY: Delete intermediate raw stream footage immediately after rendering
        try:
            if source_media_path.exists() and "ingest" in str(source_media_path).lower():
                source_media_path.unlink(missing_ok=True)
                logger.info(f"[CLEANUP] Deleted intermediate raw footage: {source_media_path.name}")
        except Exception as cl_err:
            logger.warning(f"[CLEANUP] Could not delete raw footage {source_media_path}: {cl_err}")

        yt_publish_info = None
        if publish_to_youtube and all_hard_pass and is_valid:
            try:
                from src.publishing.publishers import YouTubePublisher
                yt_pub = YouTubePublisher()
                yt_title = ai_title
                yt_desc = f"{ai_caption}\n\nStream: {url}\nClipped by ViceDesk 24/7 AI Intelligence."
                yt_publish_info = yt_pub.upload_short(
                    video_path=str(output_mp4_path),
                    title=yt_title,
                    description=yt_desc,
                    privacy_status="public",
                )
                logger.info(f"Published to YouTube Shorts: {yt_publish_info.get('video_url')}")
            except Exception as e:
                logger.warning(f"Auto-upload to YouTube Shorts failed: {e}")
                yt_publish_info = {"status": "FAILED", "error": str(e)}

        return {
            "status": "COMPLETED",
            "trace_id": trace_id,
            "render_id": render_id,
            "filename": f"{render_id}.mp4",
            "output_path": str(output_mp4_path),
            "media_url": f"/media/{render_id}.mp4",
            "duration_ms": render_meta["duration_ms"],
            "resolution": f"{render_meta['width']}x{render_meta['height']}",
            "qc_passed": all_hard_pass and is_valid,
            "creator": creator_name,
            "title": ai_title,
            "hook": ai_hook,
            "score": 96 if all_hard_pass else 80,
            "caption": ai_caption,
            "words_count": len(words),
            "transcript": transcript_text,
            "youtube_publish": yt_publish_info,
        }
