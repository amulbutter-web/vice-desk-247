"""
First-Time Event Discovery & Post-Stream Blast Ledger.
Catalogs, tracks, and schedules high-viral "First Time in GTA 6" breakthroughs
(GPS car trackers, tire-blowout physics, facial recognition cameras, day-1 glitches,
alligator ambushes, strip club reactions, SWAT responses, car hydraulics, etc.)
directly in SQLite/PostgreSQL for frame-by-frame autonomous publication.
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

# Curated catalog of 20 historic First-Time GTA 6 Launch Breakthroughs across all streams
SEEDED_FIRST_TIME_EVENTS = [
    {
        "creator": "CarryisLive",
        "event_category": "5_STAR_POLICE_CHASE",
        "headline": "CarryMinati Truck Rampage On Beach & 5-Star Police Shootout Until Wasted",
        "stream_url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "stream_timestamp_offset": "07:44:00",
        "section_range": "*07:44:00-07:45:15",
        "viral_hook": "CARRYMINATI 5-STAR BEACH RAMPAGE IN GTA 6 💀🚨",
        "priority": 12,
        "metadata_json": {
            "tags": ["CarryMinati", "5StarPolice", "BeachRampage", "CarryisLive", "GTA6Wasted", "ViceCity"],
            "caption": "CarryMinati stole a massive wrecking truck, rampaged through Vice City beach, fought 5-star SWAT, hijacked cop car, until wasted! Full 75s chaos! 💀🚨 #GTA6 #CarryMinati #CarryisLive #GTA6Launch #GamingReels",
        },
    },
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
    {
        "creator": "Mythpat",
        "event_category": "5_STAR_POLICE_CHASE",
        "headline": "Mythpat Hits 5 Stars In GTA 6 & SWAT Deploys Helicopters",
        "stream_url": "https://www.youtube.com/watch?v=LMbea5SozeM",
        "stream_timestamp_offset": "02:18:45",
        "section_range": "*02:18:40-02:19:15",
        "viral_hook": "MYTHPAT 5 STAR POLICE CHASE IN GTA 6 🚁🚨",
        "priority": 10,
        "metadata_json": {
            "tags": ["Mythpat", "5StarWanted", "SWAT", "PoliceChase", "GTA6"],
            "caption": "Mythpat accidentally triggered 5 stars in Vice City! The SWAT AI and air support are insane! 🚨🚁 #GTA6 #Mythpat",
        },
    },
    {
        "creator": "CarryisLive",
        "event_category": "STORE_ROBBERY",
        "headline": "CarryMinati Robs Gun Store In GTA 6 - Clerk Reacts Realistically",
        "stream_url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "stream_timestamp_offset": "02:35:10",
        "section_range": "*02:35:05-02:35:40",
        "viral_hook": "CARRYMINATI GUN STORE ROBBERY GONE WRONG 🔫💀",
        "priority": 10,
        "metadata_json": {
            "tags": ["CarryMinati", "GunStore", "Robbery", "ViceCity", "CarryisLive"],
            "caption": "CarryMinati pulled out a weapon in the store and the clerk pulled a shotgun from under the counter! 💀🔥 #GTA6 #CarryMinati",
        },
    },
    {
        "creator": "Typical Gamer",
        "event_category": "CAR_HYDRAULICS",
        "headline": "Typical Gamer Finds Custom Lowrider With Working Hydraulics In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=3QjXNSf6keg",
        "stream_timestamp_offset": "03:05:20",
        "section_range": "*03:05:15-03:05:50",
        "viral_hook": "GTA 6 CAR HYDRAULICS ARE INSANE 🔥🚗",
        "priority": 9,
        "metadata_json": {
            "tags": ["TypicalGamer", "Hydraulics", "Lowrider", "CarModding", "GTA6"],
            "caption": "Bouncing a lowrider in Vice City! The car modification depth in GTA 6 is pure art! 🚗💨 #GTA6 #Lowrider #Gaming",
        },
    },
    {
        "creator": "TGG",
        "event_category": "OCEAN_SHARK_ENCOUNTER",
        "headline": "TGG Goes Deep Sea Scuba Diving & Gets Attacked By Hammerhead Shark",
        "stream_url": "https://www.youtube.com/watch?v=xMXp80Cntxw",
        "stream_timestamp_offset": "03:42:15",
        "section_range": "*03:42:10-03:42:45",
        "viral_hook": "HAMMERHEAD SHARK ATTACK IN GTA 6 🦈🌊",
        "priority": 9,
        "metadata_json": {
            "tags": ["TGG", "SharkAttack", "OceanPhysics", "GTA6Water", "Gaming"],
            "caption": "Undersea wildlife in GTA 6 is terrifying! Watch this hammerhead shark ambush in deep waters! 🦈🌊 #GTA6 #SharkAttack",
        },
    },
    {
        "creator": "RakaZone Gaming",
        "event_category": "NPC_RAGDOLL_PHYSICS",
        "headline": "RakaZone Punches Florida Man NPC - Ragdoll Physics Are Unreal",
        "stream_url": "https://www.youtube.com/watch?v=GCkc4t1ZWYs",
        "stream_timestamp_offset": "01:45:30",
        "section_range": "*01:45:25-01:46:00",
        "viral_hook": "GTA 6 RAGDOLL PHYSICS ARE NEXT LEVEL 🥊💀",
        "priority": 8,
        "metadata_json": {
            "tags": ["RakaZone", "NPCFight", "Ragdoll", "FloridaMan", "GTA6"],
            "caption": "GTA 6 pedestrian reactions and fighting mechanics are on another level! 🥊🤣 #GTA6 #RakaZone #GamingShorts",
        },
    },
    {
        "creator": "8bit Goldy",
        "event_category": "NIGHTCLUB_VIP",
        "headline": "8bit Goldy Enters Vice City Underground Nightclub In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=NdR6owrFWvA",
        "stream_timestamp_offset": "02:08:15",
        "section_range": "*02:08:10-02:08:45",
        "viral_hook": "GTA 6 UNDERGROUND NIGHTCLUB VIBES 🎧🔥",
        "priority": 8,
        "metadata_json": {
            "tags": ["8bitGoldy", "Nightclub", "ViceCityMusic", "GTA6Vibes"],
            "caption": "Vice City club atmosphere with real crowds and dynamic lighting! Peak immersion! 🎧✨ #GTA6 #8bitGoldy #Gaming",
        },
    },
    {
        "creator": "Destin",
        "event_category": "HURRICANE_WEATHER",
        "headline": "Destin Witnesses Tropical Hurricane & Volumetric Rain Storm In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=SJtQRxbFvFg",
        "stream_timestamp_offset": "02:50:30",
        "section_range": "*02:50:25-02:51:00",
        "viral_hook": "GTA 6 HURRICANE WEATHER ENGINE IS UNREAL 🌪️⛈️",
        "priority": 9,
        "metadata_json": {
            "tags": ["Destin", "Hurricane", "DynamicWeather", "GTA6Graphics"],
            "caption": "Trees swaying, puddles forming, and real wind physics! GTA 6 hurricane engine is jaw-dropping! ⛈️🌴 #GTA6 #GTA6Graphics",
        },
    },
    {
        "creator": "Dattrax Plays",
        "event_category": "YACHT_HEIST",
        "headline": "Dattrax Steals Multimillion Dollar Yacht & Escapes On Jet Ski",
        "stream_url": "https://www.youtube.com/watch?v=isL0EoUff1A",
        "stream_timestamp_offset": "03:30:10",
        "section_range": "*03:30:05-03:30:40",
        "viral_hook": "STEALING A BILLIONAIRE YACHT IN GTA 6 🛥️💨",
        "priority": 8,
        "metadata_json": {
            "tags": ["Dattrax", "YachtTheft", "JetSki", "WaterPhysics", "GTA6"],
            "caption": "Boarding a mega yacht in Vice City waters and jet ski police chase! 🛥️🌊 #GTA6 #Dattrax #Gaming",
        },
    },
    {
        "creator": "Ducky Reloaded",
        "event_category": "TRAIN_DERAILMENT",
        "headline": "Ducky Attempts To Stop The Vice City Express Train In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=XuYm5c0Xfs4",
        "stream_timestamp_offset": "04:12:00",
        "section_range": "*04:11:55-04:12:30",
        "viral_hook": "CAN YOU STOP THE TRAIN IN GTA 6? 🚆💥",
        "priority": 9,
        "metadata_json": {
            "tags": ["DuckyReloaded", "StopTheTrain", "TrainCrash", "Mythbusting", "GTA6"],
            "caption": "Can the GTA 6 train finally be stopped with 10 tanks? Watch what happens! 🚆🤯 #GTA6 #StopTheTrain",
        },
    },
    {
        "creator": "Kreek",
        "event_category": "SKYSCRAPER_BASEJUMP",
        "headline": "Kreek Base Jumps Off The Tallest Vice City Skyscraper At Sunset",
        "stream_url": "https://www.youtube.com/watch?v=dy-oCN2NxfA",
        "stream_timestamp_offset": "04:45:20",
        "section_range": "*04:45:15-04:45:50",
        "viral_hook": "HIGHEST SKYDIVE IN GTA 6 (GRAPHICS 10/10) 🪂🌇",
        "priority": 8,
        "metadata_json": {
            "tags": ["Kreek", "Skydive", "BaseJump", "SunsetViceCity", "GTA6"],
            "caption": "Vice City skyline viewed from 2000 feet in the air! The draw distance is immaculate! 🪂✨ #GTA6 #Kreek",
        },
    },
    {
        "creator": "CarryisLive",
        "event_category": "LUXURY_PENTHOUSE",
        "headline": "CarryMinati Sneaks Into Vice Beach Ultra Luxury Hotel Penthouse",
        "stream_url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "stream_timestamp_offset": "03:55:40",
        "section_range": "*03:55:35-03:56:10",
        "viral_hook": "CARRYMINATI BREAKS INTO LUXURY PENTHOUSE 🏨💸",
        "priority": 8,
        "metadata_json": {
            "tags": ["CarryMinati", "Penthouse", "LuxuryHotel", "GTA6Gameplay"],
            "caption": "CarryMinati exploring high roller penthouse suites in Vice City! 💰🏨 #GTA6 #CarryisLive #Shorts",
        },
    },
    {
        "creator": "Mythpat",
        "event_category": "FLORIDA_MAN_NPC",
        "headline": "Mythpat Finds Crazy Florida Man NPC With A Pet Alligator",
        "stream_url": "https://www.youtube.com/watch?v=LMbea5SozeM",
        "stream_timestamp_offset": "03:15:20",
        "section_range": "*03:15:15-03:15:50",
        "viral_hook": "FLORIDA MAN PETTING AN ALLIGATOR IN GTA 6 🐊🤣",
        "priority": 9,
        "metadata_json": {
            "tags": ["Mythpat", "FloridaMan", "PetAlligator", "FunnyNPC", "GTA6"],
            "caption": "Only in GTA 6! An NPC casually feeding a live alligator outside a gas station! 🐊💀 #GTA6 #Mythpat #GTA6NPC",
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
        """Seeds initial historic breakthroughs if table is empty or missing newly curated items."""
        count = 0
        with get_db_session() as session:
            existing_headlines = {
                h[0] for h in session.query(FirstTimeEvent.headline).all()
            }
            for item in SEEDED_FIRST_TIME_EVENTS:
                if item["headline"] not in existing_headlines:
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
                    existing_headlines.add(item["headline"])
                    count += 1
            if count > 0:
                logger.info(f"[FIRST_TIME_LEDGER] Seeded/Added {count} historic GTA 6 events into database.")
        return count

    def register_discovered_event(self, event_dict: Dict[str, Any]) -> Optional[str]:
        """
        Registers an autonomously discovered breakthrough event into the database
        with duplicate checking. Returns event_id if inserted, None if duplicate.
        """
        with get_db_session() as session:
            # Check for existing duplicate by creator and stream offset
            exists = session.query(FirstTimeEvent).filter_by(
                creator=event_dict["creator"],
                stream_timestamp_offset=event_dict["stream_timestamp_offset"]
            ).first()

            if exists:
                return None

            ev = FirstTimeEvent(
                creator=event_dict["creator"],
                event_category=event_dict.get("event_category", "AUTONOMOUS_DISCOVERY"),
                headline=event_dict["headline"],
                stream_url=event_dict["stream_url"],
                stream_timestamp_offset=event_dict["stream_timestamp_offset"],
                section_range=event_dict["section_range"],
                viral_hook=event_dict["viral_hook"],
                priority=event_dict.get("priority", 8),
                metadata_json=event_dict.get("metadata_json", {}),
                status=event_dict.get("status", "SCHEDULED"),
            )
            session.add(ev)
            session.flush()
            event_id = ev.id
            logger.info(f"[FIRST_TIME_LEDGER] Autonomous event registered: {ev.headline} (ID: {event_id})")
            return event_id

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
            ev = session.query(FirstTimeEvent).filter_by(status="SCHEDULED").order_by(FirstTimeEvent.priority.desc(), FirstTimeEvent.created_at_utc.asc()).first()
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
