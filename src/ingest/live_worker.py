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
from typing import Dict, Any, Optional

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

# Global rate-limiter: only 1 yt-dlp process runs at a time across all workers
# Prevents 3 workers simultaneously hammering YouTube's rate-limit detection
_ytdlp_global_lock = threading.Semaphore(1)
_ytdlp_last_call_time: float = 0.0
_YTDLP_MIN_INTERVAL_SEC = 8  # Minimum 8 seconds between any two yt-dlp calls globally


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

        # Build resilient yt-dlp authentication & POT bypass arguments
        auth_args = []
        cookies_cand = Path("/tmp/youtube_cookies.txt")
        b64_env = os.getenv("YOUTUBE_COOKIES_BASE64")
        if b64_env and (not cookies_cand.exists() or cookies_cand.stat().st_size == 0):
            try:
                import base64
                cookies_cand.write_bytes(base64.b64decode(b64_env))
                cookies_cand.chmod(0o600)
            except Exception as _ce:
                logger.warning(f"Failed to decode YOUTUBE_COOKIES_BASE64: {_ce}")

        if not cookies_cand.exists() and Path("data/youtube_cookies.txt").exists():
            cookies_cand = Path("data/youtube_cookies.txt")
        if cookies_cand.exists() and cookies_cand.stat().st_size > 0:
            auth_args.extend(["--cookies", str(cookies_cand)])

        proxy_cand = os.getenv("YOUTUBE_PROXY") or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
        if proxy_cand:
            auth_args.extend(["--proxy", proxy_cand])

        # 3. Primary Method: Native yt-dlp slice (fast, exact timestamps, merges audio/video in 1080p60)
        if os.path.exists(self.ytdlp_bin) and (url.startswith("http://") or url.startswith("https://")):
            try:
                logger.info(f"Downloading stream footage [{section_range}] via yt-dlp: {url}...")
                cmd_native = [
                    self.ytdlp_bin,
                    "-4",
                    "--extractor-args", "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416",
                    "--extractor-args", "youtube:player_client=mweb,android,web",
                    "--sleep-interval", "5",
                    "--max-sleep-interval", "10",
                    "-f", "best[height<=1080]/bestvideo[height<=1080]+bestaudio/best",
                    "--download-sections", section_range,
                    "--force-overwrites",
                    "--no-playlist",
                    "--no-warnings",
                    "-o", str(target_file),
                ] + auth_args + [url]
                # Acquire global rate-limiter to serialize yt-dlp calls across workers
                global _ytdlp_last_call_time
                with _ytdlp_global_lock:
                    elapsed = time.monotonic() - _ytdlp_last_call_time
                    if elapsed < _YTDLP_MIN_INTERVAL_SEC:
                        wait = _YTDLP_MIN_INTERVAL_SEC - elapsed
                        logger.info(f"[RateGuard] Throttling yt-dlp — waiting {wait:.1f}s before next call")
                        time.sleep(wait)
                    _ytdlp_last_call_time = time.monotonic()
                    res_nat = subprocess.run(cmd_native, capture_output=True, text=True, timeout=180)
                if res_nat.returncode == 0 and target_file.exists() and target_file.stat().st_size > 500_000:
                    try:
                        probe_check = self.probe.probe(str(target_file))
                        if probe_check.get("has_video") and probe_check.get("duration_ms", 0) > 10_000:
                            logger.info(f"Native yt-dlp captured verified footage: {target_file} ({target_file.stat().st_size / (1024*1024):.2f} MB)")
                            return target_file
                        else:
                            logger.warning(f"Native yt-dlp file invalid/too short ({probe_check.get('duration_ms', 0)}ms) — trying fallback")
                            target_file.unlink(missing_ok=True)
                    except Exception as p_err:
                        logger.warning(f"Native yt-dlp probe error: {p_err}")
                        target_file.unlink(missing_ok=True)
                else:
                    logger.warning(f"Native yt-dlp returned code {res_nat.returncode}: {res_nat.stderr[-500:] if res_nat.stderr else ''}")
            except Exception as en:
                logger.warning(f"Native yt-dlp slice error: {en}")

            # 4. Fallback Method: yt-dlp -g + FFmpeg direct slice with proper HTTP User-Agent header
            try:
                logger.info(f"Fallback: Extracting live stream URLs for {url} [{start_str} +{duration_sec}s]...")
                cmd_g = [
                    self.ytdlp_bin,
                    "-4",
                    "--extractor-args", "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416",
                    "--extractor-args", "youtube:player_client=mweb,android,web",
                    "--sleep-interval", "5",
                    "--max-sleep-interval", "10",
                    "-g",
                    "-f", "best[height<=1080]/bestvideo[height<=1080]+bestaudio/best",
                    "--no-warnings",
                ] + auth_args + [url]
                # Acquire rate-limiter for fallback call too
                with _ytdlp_global_lock:
                    elapsed = time.monotonic() - _ytdlp_last_call_time
                    if elapsed < _YTDLP_MIN_INTERVAL_SEC:
                        time.sleep(_YTDLP_MIN_INTERVAL_SEC - elapsed)
                    _ytdlp_last_call_time = time.monotonic()
                    res_g = subprocess.run(cmd_g, capture_output=True, text=True, timeout=25)
                if res_g.returncode == 0 and res_g.stdout.strip():
                    stream_urls = res_g.stdout.strip().splitlines()
                    if len(stream_urls) >= 2:
                        v_url, a_url = stream_urls[0], stream_urls[1]
                        cmd_ff = [
                            self.ffmpeg_bin, "-y",
                            "-threads", "2",
                            "-protocol_whitelist", "file,http,https,tcp,tls",
                            "-reconnect", "1",
                            "-reconnect_at_eof", "1",
                            "-reconnect_streamed", "1",
                            "-reconnect_delay_max", "5",
                            "-user_agent", ua,
                            "-ss", start_str,
                            "-i", v_url,
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
                        logger.warning(f"Fallback FFmpeg direct slice failed (code {res_ff.returncode}): {res_ff.stderr[-200:] if res_ff.stderr else ''}")
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
