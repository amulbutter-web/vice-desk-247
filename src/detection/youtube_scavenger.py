"""
YouTube Real-Time Scavenger & Discovery Engine (A04_SCAVENGER).
Powered by 2 Dedicated Groq Scout Brains (EXTRA_GROQ_SCOUT_KEY_1 & 2).
Autonomously searches across YouTube 24/7 for:
1. Newly started GTA 6 live streams (IShowSpeed, CarryisLive, Typical Gamer, etc.)
2. High-curiosity explorations (Vice City Airport, secret underground bunkers, hidden islands)
3. Crazy physics & 5-star police chases (tank warfare, tire blowout sparks, alligator ambushes)
4. Longer narrative clips (60s to 85s) that maximize watch-time and trigger the YouTube & Instagram algorithm.
"""
import os
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from src.detection.stream_scout_agent import StreamScoutAgent
from src.detection.first_time_ledger import FirstTimeLedger

logger = logging.getLogger("youtube_scavenger")

SEARCH_TOPICS = [
    {"query": "GTA 6 airport exploration", "category": "AIRPORT_EXPLORATION", "priority": 12},
    {"query": "GTA 6 gameplay live stream", "category": "LIVE_STREAM_HYPE", "priority": 11},
    {"query": "GTA 6 secret locations and hidden areas", "category": "SECRET_LOCATIONS", "priority": 10},
    {"query": "GTA 6 5 star wanted military police chase", "category": "5_STAR_POLICE", "priority": 10},
    {"query": "GTA 6 car tire blowout rim physics", "category": "VEHICLE_PHYSICS", "priority": 9},
    {"query": "GTA 6 funny moments glitches Florida man", "category": "FUNNY_GLITCHES", "priority": 9},
    {"query": "GTA 6 beach water physics alligator attack", "category": "BEACH_ALLIGATOR", "priority": 9},
    {"query": "IShowSpeed GTA 6 gameplay", "category": "SPEED_GAMEPLAY", "priority": 12},
    {"query": "CarryMinati GTA 6 Vice City", "category": "CARRY_VICE_CITY", "priority": 11},
]


class YouTubeScavenger:
    """
    Autonomous scavenger that mines YouTube for the most viral GTA 6 content,
    evaluates curiosity factor with Groq Scout Brain, and queues 60s-80s narrative arcs.
    """

    def __init__(self, ytdlp_bin: Optional[str] = None):
        self.ytdlp_bin = ytdlp_bin or shutil.which("yt-dlp") or "yt-dlp"
        self.scout_agent = StreamScoutAgent()
        self.ledger = FirstTimeLedger()
        self.last_scavenge_time: Optional[datetime] = None

    def search_topic(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Executes flat playlist search via yt-dlp to find videos without consuming Google API quota.
        """
        cmd = [
            self.ytdlp_bin,
            f"ytsearch{limit}:{query}",
            "--extractor-args", "youtube:player_client=default,visionos",
            "--dump-json",
            "--flat-playlist",
            "--no-warnings",
        ]
        results = []
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().splitlines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        video_id = data.get("id")
                        if video_id:
                            results.append({
                                "id": video_id,
                                "url": f"https://www.youtube.com/watch?v={video_id}",
                                "title": data.get("title", ""),
                                "uploader": data.get("uploader", "Unknown Streamer"),
                                "view_count": int(data.get("view_count") or 0),
                                "duration": int(data.get("duration") or 0),
                                "live_status": data.get("live_status"),
                            })
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"[SCAVENGER] Search error for '{query}': {e}")
        return results

    def scavenge_and_queue_viral_moments(self, max_new_events: int = 5) -> List[Dict[str, Any]]:
        """
        Runs comprehensive search across all top topics, evaluates virality,
        and registers top-scoring 60-80s narrative events into the FirstTimeLedger.
        """
        logger.info("[SCAVENGER] Commencing YouTube viral scavenging run...")
        queued = []

        for topic in SEARCH_TOPICS:
            query = topic["query"]
            category = topic["category"]
            base_prio = topic["priority"]

            items = self.search_topic(query, limit=4)
            for item in items:
                video_url = item["url"]
                title = item["title"]
                uploader = item["uploader"]
                views = item["view_count"]
                duration = item["duration"]

                # Exclude super long videos (> 6 hours) or super short (< 2 min)
                if duration and (duration < 120 or duration > 28800):
                    continue

                # Use Groq Scout Brain to evaluate virality and pick a 60-75s narrative section
                plan = self.scout_agent.generate_viral_plan_for_stream(
                    creator=uploader,
                    title=title,
                    lang="hi" if any(k in title.lower() for k in ["hindi", "carry", "mythpat", "bhai", "live"]) else "en"
                )

                offset_sec = plan.get("section_offset_sec", 120)
                # Ensure offset fits within video
                if duration and offset_sec + 75 > duration:
                    offset_sec = max(30, duration // 3)

                # Format 60-75s section range for full narrative arc
                start_m, start_s = divmod(offset_sec, 60)
                start_h, start_m = divmod(start_m, 60)
                end_m, end_s = divmod(offset_sec + 65, 60)  # 65-second sweet spot
                end_h, end_m = divmod(end_m, 60)

                section_range = f"*{start_h:02d}:{start_m:02d}:{start_s:02d}-{end_h:02d}:{end_m:02d}:{end_s:02d}"
                offset_str = f"{start_h:02d}:{start_m:02d}:{start_s:02d}"

                hook = plan.get("hook", f"{uploader.upper()} IN GTA 6 💀🔥")
                caption = plan.get("caption", f"Insane GTA 6 exploration with {uploader}!")

                # Register into FirstTimeLedger
                event_dict = {
                    "creator": uploader,
                    "event_category": category,
                    "headline": title[:100],
                    "stream_url": video_url,
                    "stream_timestamp_offset": offset_str,
                    "section_range": section_range,
                    "viral_hook": hook,
                    "priority": max(5, min(25, (base_prio // 2) + (3 if views > 100000 else 0))),
                    "metadata_json": {
                        "caption": caption,
                        "title": plan.get("title", f"{title} #Shorts #GTA6"),
                        "source_views": views,
                        "duration_sec": 65,
                    }
                }

                event_id = self.ledger.register_discovered_event(event_dict)
                if event_id:
                    logger.info(f"[SCAVENGER] ✅ Queued New Narrative Event: '{title}' ({section_range}) | Hook: {hook}")
                    queued.append(event_dict)
                    if len(queued) >= max_new_events:
                        break

            if len(queued) >= max_new_events:
                break

        self.last_scavenge_time = datetime.now(timezone.utc)
        logger.info(f"[SCAVENGER] Run complete. Queued {len(queued)} high-retention events into DB.")
        return queued
