"""
24/7 Autonomous Background Stream Intelligence & Shorts Publisher.
Runs continuously inside the cloud production container without laptop dependency.
Periodically scouts streams, clips 1080p game moments in Blur-Fill 9:16 layout,
generates viral kinetic captions with 14-key Groq pool, and auto-publishes to YouTube Shorts.
"""
import time
import threading
import logging
from pathlib import Path
from typing import List, Dict, Any

from src.config import settings
from src.ingest.live_worker import LiveIngestWorker
from src.publishing.publishers import YouTubePublisher, PublishingError

logger = logging.getLogger("autonomous_worker")

CONTINUOUS_STREAMS = [
    {"creator": "TGG", "url": "https://www.youtube.com/watch?v=xMXp80Cntxw", "game": "GTA 6"},
    {"creator": "Mythpat", "url": "https://www.youtube.com/watch?v=LMbea5SozeM", "game": "GTA 6"},
    {"creator": "Typical Gamer", "url": "https://www.youtube.com/watch?v=3QjXNSf6keg", "game": "GTA 6"},
    {"creator": "Ducky Reloaded", "url": "https://www.youtube.com/watch?v=XuYm5c0Xfs4", "game": "GTA 6"},
    {"creator": "CarryisLive", "url": "https://www.youtube.com/watch?v=irNhWMG560k", "game": "GTA 6"},
    {"creator": "Dattrax Plays", "url": "https://www.youtube.com/watch?v=isL0EoUff1A", "game": "GTA 6"},
    {"creator": "RakaZone Gaming", "url": "https://www.youtube.com/watch?v=GCkc4t1ZWYs", "game": "GTA 6"},
    {"creator": "Kreek", "url": "https://www.youtube.com/watch?v=dy-oCN2NxfA", "game": "GTA 6"},
    {"creator": "AS Gaming", "url": "https://www.youtube.com/watch?v=u1OGXGfOEI0", "game": "GTA 6"},
    {"creator": "8bit Goldy", "url": "https://www.youtube.com/watch?v=NdR6owrFWvA", "game": "GTA 6"},
    {"creator": "Destin", "url": "https://www.youtube.com/watch?v=SJtQRxbFvFg", "game": "GTA 6"},
]


class AutonomousPublisherDaemon:
    def __init__(self, interval_sec: int = 180):
        self.interval_sec = interval_sec
        self.worker = LiveIngestWorker()
        self.publisher = YouTubePublisher()
        self.running = False
        self._thread: threading.Thread = None
        self.current_stream_idx = 0
        self.published_count = 0
        self.daily_quota_hit = False

    def start(self):
        """Starts the autonomous 24/7 background worker thread."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="247_Shorts_Worker")
        self._thread.start()
        logger.info("24/7 Autonomous Stream Intelligence & Shorts Publisher started in background.")

    def stop(self):
        self.running = False

    def _run_loop(self):
        logger.info("Entering 24/7 continuous autonomous processing loop...")
        # Brief delay on boot to allow network & DB initialization
        time.sleep(10)

        while self.running:
            if settings.emergency_kill_switch:
                logger.warning("Emergency kill switch active. Pausing autonomous loop.")
                time.sleep(30)
                continue

            stream = CONTINUOUS_STREAMS[self.current_stream_idx % len(CONTINUOUS_STREAMS)]
            self.current_stream_idx += 1
            creator = stream["creator"]
            url = stream["url"]
            game = stream["game"]

            logger.info(f"[24/7 AUTONOMOUS] Inspecting stream for {creator} ({url})")
            try:
                # 1. Process 1080p Blur-Fill Short
                res = self.worker.process_url_job(
                    url=url,
                    creator_name=creator,
                    game=game,
                    layout_mode="blur_fill",
                    section_range="*00:15:00-00:15:35",
                    publish_to_youtube=False,
                )

                render_id = res.get("render_id")
                video_path = res.get("output_path")
                hook = res.get("hook", "GTA 6 UNREAL MOMENT")
                title = res.get("title", f"{creator} - {hook}")
                caption = res.get("caption", "")

                logger.info(f"[24/7 AUTONOMOUS] Rendered {render_id} for {creator} | Hook: {hook}")

                # 2. Attempt YouTube Shorts Auto-Publish (with self-healing token refresh)
                if not self.daily_quota_hit:
                    try:
                        yt_title = f"{creator} GTA 6 LAUNCH! {hook} #Shorts"
                        yt_desc = f"{caption}\n\nStream: {url}\nAutomated 24/7 1080p by ViceDesk AI Intelligence."
                        
                        yt_res = self.publisher.upload_short(
                            video_path=video_path,
                            title=yt_title,
                            description=yt_desc,
                            privacy_status="public",
                            retry_on_401=True,
                        )
                        logger.info(f"[24/7 AUTONOMOUS] Successfully published Short: {yt_res.get('video_url')}")
                        self.published_count += 1
                    except PublishingError as pe:
                        err_str = str(pe)
                        if "uploadLimitExceeded" in err_str or "quotaExceeded" in err_str:
                            logger.warning(f"YouTube daily upload limit active. Clips will stay ready in dashboard: {pe}")
                            self.daily_quota_hit = True
                        else:
                            logger.warning(f"YouTube auto-publish attempt notice: {pe}")

            except Exception as e:
                logger.error(f"[24/7 AUTONOMOUS] Cycle error on {creator}: {e}", exc_info=True)

            # Sleep between streams
            logger.info(f"[24/7 AUTONOMOUS] Sleeping {self.interval_sec}s until next stream inspection...")
            time.sleep(self.interval_sec)


# Global singleton daemon instance
daemon_instance = AutonomousPublisherDaemon(interval_sec=300)  # 5-minute cadence
