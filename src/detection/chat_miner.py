"""
Autonomous Live Chat Velocity & Breakthrough Scene Miner.
Analyzes YouTube live chat message density, reaction spikes, and keyword triggers
to proactively detect viral 'First-Time in GTA 6' moments frame-by-frame across
all multi-hour livestreams without requiring human intervention.
"""
import re
import json
import logging
import threading
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from src.detection.first_time_ledger import FirstTimeLedger

logger = logging.getLogger("chat_miner")

# Viral trigger keywords mapped to event categories and priority scores
VIRAL_CHAT_TRIGGERS = {
    "strip club": {"category": "STRIP_CLUB_NIGHTLIFE", "priority": 10, "emoji": "🔞💀"},
    "tracker": {"category": "GPS_CAR_TRACKER", "priority": 10, "emoji": "🚨🤯"},
    "tire": {"category": "TIRE_BLOWOUT_PHYSICS", "priority": 10, "emoji": "😱💨"},
    "wheel": {"category": "TIRE_BLOWOUT_PHYSICS", "priority": 10, "emoji": "😱💨"},
    "alligator": {"category": "ALLIGATOR_ATTACK", "priority": 9, "emoji": "🐊💀"},
    "croc": {"category": "ALLIGATOR_ATTACK", "priority": 9, "emoji": "🐊💀"},
    "facial": {"category": "POLICE_FACIAL_RECOGNITION", "priority": 9, "emoji": "📸🚔"},
    "cctv": {"category": "POLICE_FACIAL_RECOGNITION", "priority": 9, "emoji": "📸🚔"},
    "camera": {"category": "POLICE_FACIAL_RECOGNITION", "priority": 8, "emoji": "📸🚔"},
    "glitch": {"category": "FIRST_LAUNCH_GLITCH", "priority": 9, "emoji": "💀🤣"},
    "bug": {"category": "FIRST_LAUNCH_GLITCH", "priority": 8, "emoji": "💀🤣"},
    "jet": {"category": "AIRPORT_JET_HEIST", "priority": 8, "emoji": "✈️🔥"},
    "airport": {"category": "AIRPORT_JET_HEIST", "priority": 8, "emoji": "✈️🔥"},
    "supercar": {"category": "SUPERCAR_TOP_SPEED", "priority": 8, "emoji": "🏎️🔊"},
    "sound": {"category": "SUPERCAR_TOP_SPEED", "priority": 7, "emoji": "🏎️🔊"},
    "swat": {"category": "5_STAR_POLICE_CHASE", "priority": 10, "emoji": "🚁🚨"},
    "5 star": {"category": "5_STAR_POLICE_CHASE", "priority": 10, "emoji": "🚁🚨"},
    "shark": {"category": "OCEAN_SHARK_ENCOUNTER", "priority": 9, "emoji": "🦈🌊"},
    "train": {"category": "TRAIN_DERAILMENT", "priority": 9, "emoji": "🚆💥"},
    "robbery": {"category": "STORE_ROBBERY", "priority": 9, "emoji": "🔫💀"},
    "gun store": {"category": "STORE_ROBBERY", "priority": 9, "emoji": "🔫💀"},
    "hydraulics": {"category": "CAR_HYDRAULICS", "priority": 8, "emoji": "🔥🚗"},
    "nightclub": {"category": "NIGHTCLUB_VIP", "priority": 8, "emoji": "🎧🔥"},
    "storm": {"category": "HURRICANE_WEATHER", "priority": 9, "emoji": "🌪️⛈️"},
    "hurricane": {"category": "HURRICANE_WEATHER", "priority": 9, "emoji": "🌪️⛈️"},
    "skydive": {"category": "SKYSCRAPER_BASEJUMP", "priority": 8, "emoji": "🪂🌇"},
    "penthouse": {"category": "LUXURY_PENTHOUSE", "priority": 8, "emoji": "🏨💸"},
}


class ChatVelocityMiner:
    """
    Monitors live chat streams and historical chat logs for peak velocity and
    keyword clusters, automatically converting viral spikes into queued FirstTimeEvent records.
    """

    def __init__(self, ledger: Optional[FirstTimeLedger] = None):
        self.ledger = ledger or FirstTimeLedger()
        self.active_listeners: Dict[str, bool] = {}

    def analyze_chat_events(
        self,
        chat_messages: List[Dict[str, Any]],
        creator_name: str,
        stream_url: str,
        bucket_size_sec: int = 15,
        velocity_threshold: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Groups chat messages into time buckets, detects spikes and keywords,
        and registers breakthrough events into the ledger.
        Each message dict: {"offset_sec": int, "text": str, "author": str}
        """
        if not chat_messages:
            return []

        # 1. Bucket messages by time offset
        buckets: Dict[int, List[Dict[str, Any]]] = {}
        for msg in chat_messages:
            offset = int(msg.get("offset_sec", 0))
            bucket_idx = (offset // bucket_size_sec) * bucket_size_sec
            buckets.setdefault(bucket_idx, []).append(msg)

        discovered_events = []

        for bucket_sec, msgs in sorted(buckets.items()):
            msg_count = len(msgs)
            combined_text = " ".join(m.get("text", "") for m in msgs).lower()

            # Check velocity spike and trigger keyword match
            triggered_kw = None
            trigger_info = None

            for kw, info in VIRAL_CHAT_TRIGGERS.items():
                if kw in combined_text:
                    triggered_kw = kw
                    trigger_info = info
                    break

            # If velocity >= threshold OR high-priority trigger keyword found
            if trigger_info or msg_count >= velocity_threshold:
                cat = trigger_info["category"] if trigger_info else "CHAT_VELOCITY_SPIKE"
                priority = trigger_info["priority"] if trigger_info else 7
                emoji = trigger_info["emoji"] if trigger_info else "🔥⚡"

                start_sec = max(0, bucket_sec - 10)
                end_sec = bucket_sec + 25

                # Format time HH:MM:SS
                def fmt_time(s: int) -> str:
                    h = s // 3600
                    m = (s % 3600) // 60
                    sec = s % 60
                    return f"{h:02d}:{m:02d}:{sec:02d}"

                offset_str = fmt_time(bucket_sec)
                section_range = f"*{fmt_time(start_sec)}-{fmt_time(end_sec)}"

                kw_display = triggered_kw.title() if triggered_kw else "Viral Reaction"
                headline = f"{creator_name} Discovers {kw_display} In GTA 6 ({msg_count} Chat Spikes/Sec)"
                hook = f"{creator_name.upper()} GTA 6 {kw_display.upper()} REACTION {emoji}"

                event_dict = {
                    "creator": creator_name,
                    "event_category": cat,
                    "headline": headline,
                    "stream_url": stream_url,
                    "stream_timestamp_offset": offset_str,
                    "section_range": section_range,
                    "viral_hook": hook,
                    "priority": priority,
                    "metadata_json": {
                        "trigger_keyword": triggered_kw,
                        "chat_density": msg_count,
                        "discovered_at": datetime.now(timezone.utc).isoformat(),
                        "tags": [creator_name, "GTA6", cat, "ViralMoment", "LiveChatSpike"],
                        "caption": f"Chat went completely crazy when {creator_name} encountered this in GTA 6! 🔥🚨 #GTA6 #{creator_name} #Gaming",
                    },
                    "status": "SCHEDULED",
                }

                # Register in database via ledger
                event_id = self.ledger.register_discovered_event(event_dict)
                if event_id:
                    event_dict["id"] = event_id
                    discovered_events.append(event_dict)
                    logger.info(f"[CHAT_MINER] Auto-discovered & Scheduled: {headline} at {offset_str}")

        return discovered_events


# Singleton miner instance
chat_miner_instance = ChatVelocityMiner()
