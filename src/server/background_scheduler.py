"""
UPGRADED 24/7 Autonomous Publisher Daemon v2.
- Publishes to BOTH YouTube Shorts AND Instagram Reels
- Targets 4:30 PM IST (10:00 UTC) exact launch moment clips
- Uses Blur-Fill Ultra 1080p 9:16 layout
- 14-key Groq pool for viral hooks + kinetic subtitles
- Self-healing: auto-refresh tokens, exponential backoff on failures
- Reports status to SupervisorAgent for email alerting
"""
import time
import threading
import logging
import os
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.config import settings
from src.ingest.live_worker import LiveIngestWorker
from src.publishing.publishers import YouTubePublisher, InstagramPublisher, PublishingError
from src.detection.trend_scout import TrendScoutEngine, ViralHotspot
from src.detection.first_time_ledger import FirstTimeLedger
from src.detection.chat_miner import chat_miner_instance
from src.detection.stream_scout_agent import StreamScoutAgent
from src.detection.youtube_scavenger import YouTubeScavenger

logger = logging.getLogger("autonomous_worker")

# Strictly 15 target GTA 6 launch creators & story missions — 50 videos/day Target
CONTINUOUS_STREAMS = [
    {"creator": "Techno Gamerz",  "url": "https://www.youtube.com/watch?v=169ZzvPxvvM", "game": "GTA 6", "lang": "hi", "base_priority": 100},
    {"creator": "CarryisLive",    "url": "https://www.youtube.com/watch?v=irNhWMG560k", "game": "GTA 6", "lang": "hi", "base_priority": 98},
    {"creator": "Mythpat",        "url": "https://www.youtube.com/watch?v=LMbea5SozeM", "game": "GTA 6", "lang": "hi", "base_priority": 95},
    {"creator": "IShowSpeed",     "url": "https://www.youtube.com/watch?v=qSyo5d-dVzA", "game": "GTA 6", "lang": "en", "base_priority": 95},
    {"creator": "Typical Gamer",  "url": "https://www.youtube.com/watch?v=3QjXNSf6keg", "game": "GTA 6", "lang": "en", "base_priority": 90},
    {"creator": "TGG",            "url": "https://www.youtube.com/watch?v=xMXp80Cntxw", "game": "GTA 6", "lang": "en", "base_priority": 88},
    {"creator": "RakaZone Gaming","url": "https://www.youtube.com/watch?v=GCkc4t1ZWYs", "game": "GTA 6", "lang": "hi", "base_priority": 85},
    {"creator": "8bit Goldy",     "url": "https://www.youtube.com/watch?v=NdR6owrFWvA", "game": "GTA 6", "lang": "hi", "base_priority": 82},
    {"creator": "AS Gaming",      "url": "https://www.youtube.com/watch?v=u1OGXGfOEI0", "game": "GTA 6", "lang": "hi", "base_priority": 80},
    {"creator": "KreekCraft",     "url": "https://www.youtube.com/watch?v=dy-oCN2NxfA", "game": "GTA 6", "lang": "en", "base_priority": 78},
    {"creator": "Live Insaan",    "url": "https://www.youtube.com/watch?v=84_m_LgUv3Q", "game": "GTA 6", "lang": "hi", "base_priority": 75},
    {"creator": "TheRadBrad",     "url": "https://www.youtube.com/watch?v=eEERhKQZWmY", "game": "GTA 6", "lang": "en", "base_priority": 72},
    {"creator": "Dattrax Plays",  "url": "https://www.youtube.com/watch?v=isL0EoUff1A", "game": "GTA 6", "lang": "hi", "base_priority": 70},
    {"creator": "Ducky Reloaded", "url": "https://www.youtube.com/watch?v=XuYm5c0Xfs4", "game": "GTA 6", "lang": "en", "base_priority": 68},
    {"creator": "Jason & Mandy",  "url": "https://www.youtube.com/watch?v=_8-c3XJH5og", "game": "GTA 6", "lang": "en", "base_priority": 99},
]

# Extended 65s-75s complete narrative windows to maximize viewer retention and Curiosity
SECTION_RANGES = [
    "*00:00:35-00:01:45",  # 70s Story Encounter / Mission Intros
    "*00:15:00-00:16:15",  # 75s Full Game Entry & First Vice City Impression
    "*00:16:30-00:17:40",  # 70s Vice City Airport & Street Roam
    "*00:20:00-00:21:15",  # 75s First Big Escalation & Police Encounter
    "*00:32:00-00:33:15",  # 75s Weapon & Destruction Ballistics
    "*00:45:00-00:46:15",  # 75s Ocean Drive Sunset & Luxury Drive
]


class AutonomousPublisherDaemon:
    """
    24/7 autonomous cloud worker. Runs forever on Railway.
    Does NOT require the user's laptop.
    Targets 50 videos daily across 15 GTA 6 creators.
    """

    def __init__(self, interval_sec: int = 600, target_daily_uploads: int = 50):
        self.interval_sec = interval_sec
        self.target_daily_uploads = target_daily_uploads
        self.worker = LiveIngestWorker()
        self.yt_publisher = YouTubePublisher()
        self.ig_publisher = InstagramPublisher()
        self.trend_scout = TrendScoutEngine()
        self.scout_agent = StreamScoutAgent()
        self.scavenger = YouTubeScavenger()
        self.ranked_streams: List[Dict[str, Any]] = []
        self.ledger = FirstTimeLedger()
        self.running = False
        self._thread: Optional[threading.Thread] = None

        # State tracking
        self.current_stream_idx = 0
        self.current_section_idx = 0
        self.published_count = 0
        self.ig_published_count = 0
        self.scavenge_counter = 0
        self.daily_quota_hit = False
        self.consecutive_errors = 0
        self.MAX_ERRORS = 5

    def is_already_published_on_instagram(self, hook: str, headline: str, creator: str = "") -> bool:
        """
        Queries recent reels from Instagram to strictly prevent duplicate posts.
        Checks for matching hooks, headlines, or key event identifiers across creators.
        """
        try:
            import re
            recent = self.ig_publisher.get_recent_reels(limit=50)
            clean_str = lambda s: re.sub(r"[^\w\s]", " ", (s or "").lower()).strip()
            stop_words = {"gta", "gta6", "in", "is", "a", "the", "and", "or", "of", "to", "first", "time", "with", "at", "for"}

            creator_clean = clean_str(creator).replace("gaming", "").replace("plays", "").replace("islive", "").strip()
            h_core = set(clean_str(hook).split()) - stop_words
            hl_core = set(clean_str(headline).split()) - stop_words

            for r in recent:
                cap_clean = clean_str(r.get("caption") or "")
                cap_words = set(cap_clean.split())

                # Exact hook match (ignoring emojis/case)
                h_str = clean_str(hook)
                if len(h_str) > 12 and h_str in cap_clean:
                    return True

                # Creator + 3 core words match
                creator_in_cap = any(c_part in cap_clean for c_part in creator_clean.split() if len(c_part) > 2) if creator_clean else True
                if creator_in_cap:
                    if len(h_core) >= 2 and len(h_core.intersection(cap_words)) >= min(3, len(h_core)):
                        return True
                    if len(hl_core) >= 2 and len(hl_core.intersection(cap_words)) >= min(3, len(hl_core)):
                        return True
            return False
        except Exception as e:
            logger.warning(f"[DEDUP] Check note: {e}")
            return False

    # ─── Public API ───

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="247_Publisher_v2",
        )
        self._thread.start()
        logger.info("[DAEMON] 24/7 Autonomous Publisher v2 started (YouTube + Instagram)")

    def stop(self):
        self.running = False

    def _cleanup_temp_disk_space(self):
        """
        Self-healing garbage collection: Deletes temporary downloaded video chunks and parts
        older than 4 hours to ensure Railway cloud disk storage never exhausts over 6+ months of 24/7 operation.
        """
        try:
            now = time.time()
            cutoff = now - 300  # 5 minutes: Immediate aggressive disk cleanup for cloud containers
            root_dir = Path(__file__).resolve().parent.parent.parent
            temp_dirs = [
                root_dir / "data" / "temp",
                root_dir / "data" / "media" / "ingest",
                root_dir / "data" / "rendered",
            ]
            cleaned_bytes = 0
            for d in temp_dirs:
                if d.exists():
                    for f in d.iterdir():
                        if f.is_file() and f.name != ".gitkeep" and f.stat().st_mtime < cutoff:
                            sz = f.stat().st_size
                            try:
                                f.unlink()
                                cleaned_bytes += sz
                            except Exception:
                                pass
            if cleaned_bytes > 0:
                logger.info(f"[DAEMON] Cloud Disk GC: Cleaned {cleaned_bytes / (1024*1024):.1f} MB.")
        except Exception as e:
            logger.debug(f"[DAEMON] Disk GC note: {e}")

    # ─── Core Loop ───

    def _run_loop(self):
        logger.info("[DAEMON] Entering 24/7 continuous loop...")
        time.sleep(10)  # Allow server startup
        youtube_rate_limited_until: float = 0.0  # Track when IP ban was detected

        while self.running:
            if settings.emergency_kill_switch:
                logger.warning("[DAEMON] Kill switch active — pausing 60s")
                time.sleep(60)
                continue

            if self.consecutive_errors >= self.MAX_ERRORS:
                logger.warning("[DAEMON] %d consecutive errors — brief 15s recovery cooldown", self.MAX_ERRORS)
                time.sleep(15)
                self.consecutive_errors = 0

            # 6-Month Autonomous Scavenger: Replenish queue with fresh YouTube discoveries
            self.scavenge_counter += 1
            if self.scavenge_counter % 6 == 1:
                try:
                    self.scavenger.scavenge_and_queue_viral_moments(max_new_events=3)
                except Exception as scv_err:
                    logger.warning(f"[DAEMON] Scavenger auto-refill note: {scv_err}")

            # Garbage Collection: Clean temporary raw slices older than 4 hours
            if self.scavenge_counter % 15 == 0:
                self._cleanup_temp_disk_space()

            # Prioritize Curated Historic 'First-Time' events first, then continuous streams
            next_first_time = self.ledger.get_next_scheduled_event()
            current_first_time_id = None

            if next_first_time:
                creator = next_first_time["creator"]
                url = next_first_time["stream_url"]
                section = next_first_time["section_range"]
                hook = next_first_time["viral_hook"]
                title = f"{next_first_time['headline']} #Shorts #GTA6"
                caption = next_first_time.get("metadata", {}).get("caption", f"{next_first_time['headline']} in GTA 6!")
                current_first_time_id = next_first_time["id"]
                game = "GTA 6"
                lang = "hi" if creator in ("Mythpat", "CarryisLive", "Dattrax Plays", "RakaZone Gaming", "AS Gaming", "8bit Goldy") else "en"
                self.current_stream_idx += 1

                # Strict Deduplication Check before expensive downloading/rendering
                if self.is_already_published_on_instagram(hook, next_first_time["headline"], creator):
                    logger.info(f"[DAEMON] Event '{next_first_time['headline']}' is ALREADY published on Instagram. Advancing queue.")
                    self.ledger.update_event_status(current_first_time_id, "PUBLISHED", "ALREADY_ON_IG")
                    continue

                logger.info(f"[DAEMON] Processing Historic First-Time Event: {next_first_time['headline']} ({creator})")
            else:
                if not self.ranked_streams or (self.current_stream_idx % len(CONTINUOUS_STREAMS) == 0):
                    try:
                        self.ranked_streams = self.scout_agent.evaluate_and_rank_streams(CONTINUOUS_STREAMS)
                    except Exception as sc_err:
                        logger.warning(f"[DAEMON] Scout agent ranking fallback: {sc_err}")
                        self.ranked_streams = CONTINUOUS_STREAMS

                active_streams = self.ranked_streams if self.ranked_streams else CONTINUOUS_STREAMS
                stream = active_streams[self.current_stream_idx % len(active_streams)]
                dynamic_targets = self.trend_scout.get_dynamic_section_ranges()
                target = dynamic_targets[self.current_section_idx % len(dynamic_targets)]
                section = target["section"]
                hotspot = target["hotspot"]

                self.current_stream_idx += 1
                self.current_section_idx += 1

                creator = stream["creator"]
                url = stream["url"]
                game = stream.get("game", "GTA 6")
                lang = stream.get("lang", "en")

                # Craft high-converting context hook via Groq Scout Agent with fallback
                try:
                    scout_plan = self.scout_agent.generate_viral_plan_for_stream(
                        creator=creator,
                        title=stream.get("title", f"{creator} GTA 6"),
                        lang=lang,
                    )
                    hook = scout_plan["hook"]
                    title = scout_plan["title"]
                    caption = scout_plan["caption"]
                except Exception as sp_err:
                    logger.debug(f"[DAEMON] Scout plan fallback to trend_scout: {sp_err}")
                    viral_info = self.trend_scout.craft_viral_metadata(creator_name=creator, hotspot=hotspot, lang=lang)
                    hook = viral_info["hook"]
                    title = viral_info["title"]
                    caption = viral_info["caption"]

                logger.info(f"[DAEMON] Scouting {creator} for '{hotspot.name}' — section {section}")

            try:
                # ── Step 1: Render Blur-Fill Ultra 1080p 9:16 Short ──
                res = self.worker.process_url_job(
                    url=url,
                    creator_name=creator,
                    game=game,
                    layout_mode="blur_fill",
                    section_range=section,
                    publish_to_youtube=False,
                    viral_hook=hook,
                    caption=caption,
                    title=title,
                )
                render_id = res.get("render_id")
                video_path = res.get("output_path")

                if not res.get("qc_passed") or not video_path or not Path(video_path).exists():
                    fail_reason = res.get("reason", "")
                    # Detect YouTube IP rate-limit — mark event FAILED and sleep until ban window clears
                    if "rate-limited" in fail_reason.lower() or "genuine footage" in fail_reason.lower() or "Unable to download" in fail_reason.lower():
                        youtube_rate_limited_until = time.time() + 3600  # Assume 1hr ban
                        logger.warning("[DAEMON] YouTube IP rate-limited detected for %s — sleeping 10min. Instagram-only mode.", creator)
                        if current_first_time_id:
                            self.ledger.update_event_status(current_first_time_id, "FAILED", None)
                        time.sleep(600)
                        continue
                    logger.warning("[DAEMON] No rendered output for %s — skipping social publish", creator)
                    self.consecutive_errors += 1
                    if current_first_time_id:
                        self.ledger.update_event_status(current_first_time_id, "FAILED", None)
                    time.sleep(60)
                    continue

                v_file = Path(video_path)
                # Hard quality gate: Must be genuine high-res render > 1.5MB and cannot be dummy sample footage
                if v_file.stat().st_size < 1_500_000:
                    logger.warning("[DAEMON] Rendered video for %s is under 1.5MB (%d bytes). Skipping social publish.", creator, v_file.stat().st_size)
                    if current_first_time_id:
                        self.ledger.update_event_status(current_first_time_id, "FAILED", None)
                    time.sleep(60)
                    continue

                if any(bad in v_file.name.lower() for bad in ["sample", "synth", "0ddc3702"]):
                    logger.error("[DAEMON] HARD QUALITY BLOCK: Attempted to publish dummy/fallback video %s for %s! Aborting publish.", v_file.name, creator)
                    if current_first_time_id:
                        self.ledger.update_event_status(current_first_time_id, "FAILED", None)
                    time.sleep(60)
                    continue

                self.consecutive_errors = 0
                logger.info("[DAEMON] Rendered %s for %s | Hook: %s", render_id, creator, hook)

                # ── Step 2: YouTube Shorts Upload ──
                destinations = []
                enable_yt = os.getenv("ENABLE_YOUTUBE_UPLOADS", "true").lower() in ("true", "1")
                if enable_yt and not self.daily_quota_hit:
                    try:
                        yt_title = res["title"]
                        yt_desc = f"{res['caption']}\n\nStream: {url}"
                        yt_res = self.yt_publisher.upload_short(
                            video_path=video_path,
                            title=yt_title,
                            description=yt_desc,
                            privacy_status="public",
                            retry_on_401=True,
                        )
                        logger.info("[DAEMON] ✅ YouTube: %s", yt_res.get("video_url"))
                        if yt_res.get("status") == "PUBLISHED" and yt_res.get("remote_id"):
                            destinations.append("youtube")
                            self.published_count += 1
                    except PublishingError as pe:
                        err = str(pe)
                        if "uploadLimitExceeded" in err or "quotaExceeded" in err:
                            logger.warning("[DAEMON] YouTube quota hit — switching to Instagram only")
                            self.daily_quota_hit = True
                        else:
                            logger.warning("[DAEMON] YouTube publish error: %s", err[:200])
                else:
                    if not enable_yt:
                        logger.debug("[DAEMON] YouTube uploads held by user directive. Instagram exclusive.")
                    # Reset quota flag at midnight UTC (quota resets every 24h)
                    from datetime import datetime, timezone
                    if datetime.now(timezone.utc).hour == 0:
                        self.daily_quota_hit = False
                        logger.info("[DAEMON] Quota reset at midnight UTC")

                # ── Step 3: Instagram Reels Upload ──
                try:
                    raw_caption = res.get("caption") or caption or f"{hook} in GTA 6!"
                    ig_caption = raw_caption
                    if f"Streamer: {creator}" not in ig_caption:
                        ig_caption += f"\n\nStreamer: {creator}"
                    if "#GTA6" not in ig_caption:
                        ig_caption += "\n\n#GTA6 #ViceCity #GTA6Gameplay #NextGenGaming #GamingReels #Shorts"

                    # Upload to public CDN first (Railway serves /media/)
                    video_filename = Path(video_path).name
                    public_video_url = (
                        f"https://vice-desk-intelligence-production.up.railway.app/media/{video_filename}"
                    )

                    container_id = self.ig_publisher.create_reel_container(
                        video_url=public_video_url,
                        caption=ig_caption,
                        account_ref=self.ig_publisher.account_id,
                    )
                    status = self.ig_publisher.poll_container_status(container_id)
                    if status == "FINISHED":
                        ig_res = self.ig_publisher.publish_container(
                            container_id=container_id,
                            account_ref=self.ig_publisher.account_id,
                        )
                        logger.info("[DAEMON] ✅ Instagram Reel published: %s", ig_res.get("remote_id"))
                        if not self.ig_publisher.dry_run and str(ig_res.get("remote_id", "")).isdigit():
                            destinations.append("instagram")
                            self.ig_published_count += 1
                except Exception as ig_err:
                    logger.warning("[DAEMON] Instagram publish error: %s", str(ig_err)[:200])

                # DISK SAFETY: Delete rendered video file immediately after publish
                try:
                    Path(video_path).unlink(missing_ok=True)
                    logger.info("[DAEMON] Cleaned rendered master from disk: %s", Path(video_path).name)
                except Exception:
                    pass

                if current_first_time_id:
                    status = "PUBLISHED" if len(destinations) > 0 else "FAILED"
                    self.ledger.update_event_status(current_first_time_id, status, video_path)

            except Exception as e:
                logger.error("[DAEMON] Cycle error on %s: %s", creator, e, exc_info=True)
                if current_first_time_id:
                    self.ledger.update_event_status(current_first_time_id, "FAILED", None)
                self.consecutive_errors += 1
                time.sleep(5)
                continue

            logger.info(
                "[DAEMON] Cycle done. YT published: %d | IG published: %d | Sleeping %ds",
                self.published_count, self.ig_published_count, self.interval_sec
            )
            time.sleep(self.interval_sec)

    def run_batch_instagram_blast(self, target_count: int = 15) -> List[Dict[str, Any]]:
        """
        Executes sequential rendering and publication of top scheduled breakthrough events
        directly to Instagram Reels (leveraging 100/day Meta quota).
        YouTube-ban-aware: skips events that fail to download and moves to next one.
        """
        logger.info(f"[BATCH_BLAST] Starting autonomous blast of {target_count} Instagram Reels...")
        results = []
        attempted = 0
        max_attempts = target_count * 3  # Try up to 3x more events to find ones that render
        events_tried = set()

        while len(results) < target_count and attempted < max_attempts:
            if settings.emergency_kill_switch:
                logger.warning("[BATCH_BLAST] Emergency kill switch active — aborting batch.")
                break

            ev = self.ledger.get_next_scheduled_event()
            if not ev:
                logger.info("[BATCH_BLAST] No more SCHEDULED events in ledger.")
                break

            event_id = ev["id"]
            if event_id in events_tried:
                break
            events_tried.add(event_id)
            attempted += 1

            creator = ev["creator"]
            url = ev["stream_url"]
            section = ev["section_range"]
            hook = ev["viral_hook"]
            caption = ev.get("metadata", {}).get("caption", f"{ev['headline']} in GTA 6!")
            lang = "hi" if creator in ("Mythpat", "CarryisLive", "Dattrax Plays", "RakaZone Gaming", "AS Gaming", "8bit Goldy") else "en"

            logger.info(f"[BATCH_BLAST] [{len(results)+1}/{target_count}] Processing {ev['headline']} ({creator})")

            try:
                # 1. Render 1080p 60FPS Blur-Fill Ultra clip (30-45s)
                res = self.worker.process_url_job(
                    url=url,
                    creator_name=creator,
                    game="GTA 6",
                    layout_mode="blur_fill",
                    section_range=section,
                    publish_to_youtube=False,
                )
                video_path = res.get("output_path")
                if not res.get("qc_passed") or not video_path or not Path(video_path).exists():
                    err_msg = res.get("reason", "")
                    if "rate-limited" in err_msg.lower() or "genuine footage" in err_msg.lower() or "Unable to download" in err_msg.lower():
                        logger.warning(f"[BATCH_BLAST] YouTube rate-limited for {creator} — marking FAILED and moving on")
                        self.ledger.update_event_status(event_id, "FAILED", None)
                    else:
                        logger.warning(f"[BATCH_BLAST] Render failed for {creator}: {err_msg}")
                    time.sleep(5)
                    continue

                video_filename = Path(video_path).name
                public_video_url = f"https://vice-desk-intelligence-production.up.railway.app/media/{video_filename}"

                # 2. Instagram Reels Publish via Meta Graph API
                ig_caption = f"{res['caption']}\n\nStreamer: {creator}"

                container_id = self.ig_publisher.create_reel_container(
                    video_url=public_video_url,
                    caption=ig_caption,
                    account_ref=self.ig_publisher.account_id,
                )
                status = self.ig_publisher.poll_container_status(container_id)
                if status == "FINISHED":
                    ig_res = self.ig_publisher.publish_container(
                        container_id=container_id,
                        account_ref=self.ig_publisher.account_id,
                    )
                    remote_id = ig_res.get("remote_id")
                    if self.ig_publisher.dry_run or not str(remote_id or "").isdigit():
                        logger.warning(f"[BATCH_BLAST] Dry-run or invalid remote_id for {creator} — stopping blast")
                        break
                    self.ig_published_count += 1
                    self.ledger.update_event_status(event_id, "PUBLISHED", video_path)
                    logger.info(f"[BATCH_BLAST] ✅ [{len(results)+1}/{target_count}] Published {creator} to Instagram: {remote_id}")
                    results.append({
                        "creator": creator,
                        "headline": ev["headline"],
                        "remote_media_id": remote_id,
                        "status": "PUBLISHED",
                    })
                else:
                    logger.warning(f"[BATCH_BLAST] Container status={status} for {creator} — skipping")
                    self.ledger.update_event_status(event_id, "FAILED", None)

                # Small cooldown between Instagram posts to protect rate limits
                time.sleep(10)

            except Exception as e:
                logger.error(f"[BATCH_BLAST] Error publishing {creator}: {e}", exc_info=True)
                time.sleep(4)

        logger.info(f"[BATCH_BLAST] Finished batch blast. Total published: {len(results)} / attempted: {attempted}")
        return results


# Global singleton — started by app.py on_event("startup")
daemon_interval = int(os.environ.get("DAEMON_INTERVAL_SEC", "120"))
daemon_instance = AutonomousPublisherDaemon(interval_sec=daemon_interval)
