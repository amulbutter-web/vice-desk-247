"""
First-Time Event Discovery & Post-Stream Blast Ledger.
Catalogs, tracks, and schedules high-viral "First Time in GTA 6" breakthroughs
(GPS car trackers, tire-blowout physics, facial recognition cameras, day-1 glitches,
alligator ambushes, and strip club reactions) directly in SQLite/PostgreSQL.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from src.db.database import get_db_session, init_db
from src.db.models import FirstTimeEvent

logger = logging.getLogger("first_time_ledger")

# Curated catalog of historic First-Time GTA 6 Launch Breakthroughs
SEEDED_FIRST_TIME_EVENTS = [
    {
        "creator": "Mythpat",
        "event_category": "GPS_CAR_TRACKER",
        "headline": "Mythpat's Stolen Car Has A Hidden GPS Tracker In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=LMbea5SozeM",
        "stream_timestamp_offset": "01:28:40",
        "section_range": "*01:28:30-01:29:05",
        "viral_hook": "MYTHPAT CAR HAS A GPS TRACKER IN GTA 6 🚨🤯",
        "priority": 10,
        "metadata_json": {
            "tags": ["Mythpat", "GTA6", "GPSTracker", "CarTheft", "IndianGamer"],
            "caption": "Mythpat stole a car and it literally had a police GPS tracker! Realest mechanic ever! 😱🚗 #GTA6 #Mythpat #Gaming",
        },
    },
    {
        "creator": "Typical Gamer",
        "event_category": "TIRE_BLOWOUT_PHYSICS",
        "headline": "First Car Tire Detachment & Rim Grinding Physics In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=3QjXNSf6keg",
        "stream_timestamp_offset": "01:52:15",
        "section_range": "*01:52:15-01:52:50",
        "viral_hook": "FIRST TIME A TIRE POPPED OFF IN GTA 6 😱💨",
        "priority": 10,
        "metadata_json": {
            "tags": ["GTA6Physics", "TireDetached", "CarCrash", "GTA6"],
            "caption": "GTA 6 tire physics are unbelievable! The rim literally shattered and sparks flew! 🤯🔥 #GTA6 #GTA6Physics #Viral",
        },
    },
    {
        "creator": "TGG",
        "event_category": "POLICE_FACIAL_RECOGNITION",
        "headline": "Police Use Store CCTV & Facial Recognition In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=xMXp80Cntxw",
        "stream_timestamp_offset": "02:14:30",
        "section_range": "*02:14:30-02:15:05",
        "viral_hook": "GTA 6 HAS POLICE FACIAL RECOGNITION 📸🚔",
        "priority": 9,
        "metadata_json": {
            "tags": ["GTA6Details", "CCTV", "FacialRecognition", "NextGenGaming"],
            "caption": "You literally cannot walk past cameras in GTA 6 without cops scanning your face! Next-gen AI is terrifying! 📸👮 #GTA6 #GTA6Details",
        },
    },
    {
        "creator": "CarryisLive",
        "event_category": "STRIP_CLUB_NIGHTLIFE",
        "headline": "CarryMinati Discovers Vice City Strip Club In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "stream_timestamp_offset": "01:12:00",
        "section_range": "*01:12:00-01:12:35",
        "viral_hook": "CARRYMINATI IN STRIP CLUB GTA 6 💀🔞",
        "priority": 10,
        "metadata_json": {
            "tags": ["CarryMinati", "StripClub", "GTA6", "CarryisLive", "ViceCity"],
            "caption": "CarryMinati roaming Vice City and found the strip club! Peak streamer reaction! 💀😂 #GTA6 #CarryMinati #GamingReels",
        },
    },
    {
        "creator": "Ducky Reloaded",
        "event_category": "FIRST_LAUNCH_GLITCH",
        "headline": "First Hilarious Day-1 Physics Glitch Discovered In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=XuYm5c0Xfs4",
        "stream_timestamp_offset": "02:40:10",
        "section_range": "*02:40:10-02:40:45",
        "viral_hook": "FIRST OFFICIAL GTA 6 GLITCH DISCOVERED 💀🤣",
        "priority": 9,
        "metadata_json": {
            "tags": ["GTA6Glitch", "FirstGlitch", "GTA6Funny", "Gaming"],
            "caption": "Day 1 GTA 6 physics glitch already! Rockstar forgot to patch this one! 🤣💀 #GTA6Glitch #GTA6 #GamingMoments",
        },
    },
    {
        "creator": "Dattrax Plays",
        "event_category": "ALLIGATOR_ATTACK",
        "headline": "First Florida Alligator Ambush In GTA 6 Everglades",
        "stream_url": "https://www.youtube.com/watch?v=isL0EoUff1A",
        "stream_timestamp_offset": "02:55:20",
        "section_range": "*02:55:20-02:55:55",
        "viral_hook": "FIRST ALLIGATOR ATTACK IN GTA 6 🐊💀",
        "priority": 9,
        "metadata_json": {
            "tags": ["Alligator", "GTA6Wildlife", "Everglades", "FloridaMan"],
            "caption": "Florida alligators in GTA 6 will drag you under the water! Don't go near the swamp! 🐊😱 #GTA6 #GTA6Alligator #Gaming",
        },
    },
    {
        "creator": "Kreek",
        "event_category": "AIRPORT_JET_HEIST",
        "headline": "First Attempt To Infiltrate Vice City Airport & Steal Jet",
        "stream_url": "https://www.youtube.com/watch?v=dy-oCN2NxfA",
        "stream_timestamp_offset": "03:20:00",
        "section_range": "*03:20:00-03:20:35",
        "viral_hook": "STEALING A JET IN GTA 6 (IMPOSSIBLE) ✈️🔥",
        "priority": 8,
        "metadata_json": {
            "tags": ["GTA6Airport", "StealJet", "AirDefense", "GTA6"],
            "caption": "Can you steal a commercial jet or military jet in GTA 6? Watch what happens at Vice City Airport! ✈️🤯 #GTA6 #GTA6Launch",
        },
    },
    {
        "creator": "AS Gaming",
        "event_category": "SUPERCAR_TOP_SPEED",
        "headline": "First Fastest Exotic Supercar Highway Speed Test In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=u1OGXGfOEI0",
        "stream_timestamp_offset": "03:45:00",
        "section_range": "*03:45:00-03:45:35",
        "viral_hook": "FASTEST SUPERCAR IN GTA 6 (UNREAL SOUND) 🏎️🔊",
        "priority": 8,
        "metadata_json": {
            "tags": ["Supercar", "ExhaustSound", "ViceCityHighway", "GTA6Cars"],
            "caption": "GTA 6 supercar engine sound and exhaust backfires are 100% real life! Top speed run across Vice City! 🏎️💨 #GTA6 #Supercar #Gaming",
        },
    },
]


class FirstTimeLedger:
    """
    Manages the 'First Time in GTA 6' event database table.
    Ensures frame-by-frame persistent storage and manages post-stream publishing.
    """

    def __init__(self):
        init_db()

    def seed_initial_catalog(self) -> int:
        """Seeds initial historic breakthroughs if table is empty."""
        count = 0
        with get_db_session() as session:
            existing = session.query(FirstTimeEvent).count()
            if existing == 0:
                for item in SEEDED_FIRST_TIME_EVENTS:
                    ev = FirstTimeEvent(
                        creator=item["creator"],
                        event_category=item["event_category"],
                        headline=item["headline"],
                        stream_url=item["stream_url"],
                        stream_timestamp_offset=item["stream_timestamp_offset"],
                        section_range=item["section_range"],
                        viral_hook=item["viral_hook"],
                        priority=item.get("priority", 10),
                        metadata_json=item.get("metadata_json", {}),
                        status="SCHEDULED",
                    )
                    session.add(ev)
                    count += 1
                logger.info(f"[FIRST_TIME_LEDGER] Seeded {count} historic GTA 6 events into database.")
        return count

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Returns all cataloged first-time events with current status."""
        with get_db_session() as session:
            events = session.query(FirstTimeEvent).order_by(FirstTimeEvent.priority.desc(), FirstTimeEvent.created_at_utc.asc()).all()
            return [
                {
                    "id": e.id,
                    "creator": e.creator,
                    "category": e.event_category,
                    "headline": e.headline,
                    "stream_url": e.stream_url,
                    "stream_offset": e.stream_timestamp_offset,
                    "section_range": e.section_range,
                    "status": e.status,
                    "viral_hook": e.viral_hook,
                    "rendered_clip_path": e.rendered_clip_path,
                    "priority": e.priority,
                    "created_at": e.created_at_utc.isoformat() if e.created_at_utc else None,
                }
                for e in events
            ]

    def get_next_scheduled_event(self) -> Optional[Dict[str, Any]]:
        """Pulls the highest-priority SCHEDULED event from the database."""
        with get_db_session() as session:
            ev = session.query(FirstTimeEvent).filter_by(status="SCHEDULED").order_by(FirstTimeEvent.priority.desc()).first()
            if ev:
                return {
                    "id": ev.id,
                    "creator": ev.creator,
                    "category": ev.event_category,
                    "headline": ev.headline,
                    "stream_url": ev.stream_url,
                    "stream_offset": ev.stream_timestamp_offset,
                    "section_range": ev.section_range,
                    "viral_hook": ev.viral_hook,
                    "metadata": ev.metadata_json or {},
                }
        return None

    def update_event_status(self, event_id: str, status: str, clip_path: Optional[str] = None):
        """Updates event status in database (e.g. RENDERED, PUBLISHED)."""
        with get_db_session() as session:
            ev = session.query(FirstTimeEvent).filter_by(id=event_id).first()
            if ev:
                ev.status = status
                if clip_path:
                    ev.rendered_clip_path = clip_path
                logger.info(f"[FIRST_TIME_LEDGER] Event {event_id} status updated to {status}")
