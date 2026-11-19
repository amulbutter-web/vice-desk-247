"""
Curated Catalog & Database Ledger for Historic 'First-Time in GTA 6' Moments.
Tracks first breakthroughs (first alligator encounter, first jet stolen, first 5-star chase,
first supercar top-speed test, first strip club visit, etc.) to ensure high-interest
historic moments are prioritized, published once, and never duplicated.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from src.db.database import get_db_session, init_db
from src.db.models import FirstTimeEvent

logger = logging.getLogger("first_time_ledger")

# Curated catalog of historic First-Time GTA 6 Launch Breakthroughs across all streams
SEEDED_FIRST_TIME_EVENTS = [
    {
        "creator": "Typical Gamer",
        "event_category": "CAR_HYDRAULICS",
        "headline": "Typical Gamer Finds Custom Lowrider With Working Hydraulics In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=3QjXNSf6keg",
        "stream_timestamp_offset": "03:05:00",
        "section_range": "*03:05:00-03:06:10",
        "viral_hook": "GTA 6 CAR HYDRAULICS & PHYSICS UNREAL 🔥🚗",
        "priority": 50,
        "already_published": True,
        "metadata_json": {
            "tags": ["TypicalGamer", "GTA6Physics", "Lowrider", "GTA6Cars", "GamingReels"],
            "caption": "Typical Gamer found a custom lowrider with working independent hydraulics in Vice City! The suspension bounces, the rims throw real sparks on the asphalt, and the physics response is 100% true to life! 🤯💨\n\nIs GTA 6 vehicle customization already better than GTA 5? Drop your thoughts below! 👇\n\n#GTA6 #TypicalGamer #GTA6Physics #Lowrider #GTA6Cars #GamingReels",
        },
    },
    {
        "creator": "Destin",
        "event_category": "HURRICANE_WEATHER",
        "headline": "Destin Witnesses Tropical Hurricane & Volumetric Rain Storm In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=SJtQRxbFvFg",
        "stream_timestamp_offset": "02:50:15",
        "section_range": "*02:50:15-02:51:25",
        "viral_hook": "GTA 6 HURRICANE WEATHER ENGINE IS UNREAL 🌪️⛈️",
        "priority": 48,
        "already_published": True,
        "metadata_json": {
            "tags": ["Destin", "Hurricane", "DynamicWeather", "GTA6Graphics", "ViceCity"],
            "caption": "Destin got caught in a category 4 tropical hurricane hitting Vice City! Volumetric rain, swaying palm trees, street puddles reflecting neon lights, and cars sliding in high winds! ⛈️🌴\n\nDid Rockstar just create the most realistic storm physics in history? Comment your thoughts! 👇\n\n#GTA6 #Destin #GTA6Graphics #Hurricane #ViceCity #GamingReels",
        },
    },
    {
        "creator": "Mythpat",
        "event_category": "5_STAR_POLICE_CHASE",
        "headline": "Mythpat 5-Star Police Chase With SWAT Helicopters & Spike Strips",
        "stream_url": "https://www.youtube.com/watch?v=LMbea5SozeM",
        "stream_timestamp_offset": "02:18:20",
        "section_range": "*02:18:20-02:19:30",
        "viral_hook": "MYTHPAT 5-STAR SWAT HELICOPTER ESCAPE 🚁🚨",
        "priority": 98,
        "metadata_json": {
            "tags": ["Mythpat", "5StarWanted", "SWAT", "PoliceChase", "ViceCity"],
            "caption": "Mythpat accidentally triggered a 5-star wanted level in downtown Vice City! Tactical police units deployed armored roadblocks, spike strips, and twin attack choppers in the most intense chase ever recorded! 🚁💥\n\nक्या आप ऐसी 5-स्टार पुलिस चेस से 1 मिनट भी बच पाते? कमेंट्स में बताओ! 👇\n\n#GTA6 #Mythpat #5StarWanted #PoliceChase #ViceCity #GamingReels",
        },
    },
    {
        "creator": "CarryisLive",
        "event_category": "STORE_ROBBERY",
        "headline": "CarryMinati Robs Gun Store In GTA 6 - Clerk Reacts Realistically",
        "stream_url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "stream_timestamp_offset": "02:35:00",
        "section_range": "*02:35:00-02:36:10",
        "viral_hook": "CARRYMINATI GUN STORE ROBBERY GONE WRONG 🔫💀",
        "priority": 96,
        "metadata_json": {
            "tags": ["CarryMinati", "GunStore", "Robbery", "ViceCity", "CarryisLive"],
            "caption": "CarryMinati tried to hold up an Ammu-Nation style gun store in Vice City, but the store owner pulled a combat shotgun from under the counter and blasted him! True Florida energy! 💀😂\n\nCarry भाई के साथ ऐसा किसने एक्सपेक्ट किया था? कमेंट्स में बताओ! 👇\n\n#GTA6 #CarryMinati #CarryisLive #ViceCity #GTA6Gameplay #GamingReels",
        },
    },
    {
        "creator": "TGG",
        "event_category": "OCEAN_SHARK_ENCOUNTER",
        "headline": "TGG Goes Deep Sea Scuba Diving & Gets Attacked By Hammerhead Shark",
        "stream_url": "https://www.youtube.com/watch?v=xMXp80Cntxw",
        "stream_timestamp_offset": "03:42:00",
        "section_range": "*03:42:00-03:43:10",
        "viral_hook": "HAMMERHEAD SHARK ATTACK IN GTA 6 🦈🌊",
        "priority": 94,
        "metadata_json": {
            "tags": ["TGG", "SharkAttack", "OceanPhysics", "GTA6Water", "Gaming"],
            "caption": "Undersea wildlife in GTA 6 is terrifying! Watch this hammerhead shark ambush in deep waters while scuba diving off Vice City reef! 🦈🌊\n\nWould you explore GTA 6 ocean depths alone? Drop a comment! 👇\n\n#GTA6 #TGG #SharkAttack #GTA6Water #OceanPhysics #GamingReels",
        },
    },
    {
        "creator": "AS Gaming",
        "event_category": "SUPERCAR_TOP_SPEED",
        "headline": "First Fastest Exotic Supercar Highway Speed Test In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=u1OGXGfOEI0",
        "stream_timestamp_offset": "03:44:45",
        "section_range": "*03:44:45-03:45:55",
        "viral_hook": "FASTEST SUPERCAR IN GTA 6 (UNREAL SOUND) 🏎️🔊",
        "priority": 92,
        "metadata_json": {
            "tags": ["ASGaming", "Supercar", "ExhaustSound", "ViceCityHighway", "GTA6Cars"],
            "caption": "AS Gaming pushed Vice City's fastest hypercar to its absolute limit on the coastal freeway! The engine acoustics, doppler effect, and motion blur feel straight out of real life! 🏎️💨\n\nक्या GTA 6 का कार साउंड Forza Horizon से भी बेहतर है? कमेंट्स में अपनी राय दो! 👇\n\n#GTA6 #ASGaming #Supercar #ViceCity #GTA6Cars #GamingReels",
        },
    },
    {
        "creator": "TGG",
        "event_category": "POLICE_FACIAL_RECOGNITION",
        "headline": "Police Use Store CCTV & Facial Recognition In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=xMXp80Cntxw",
        "stream_timestamp_offset": "02:14:15",
        "section_range": "*02:14:15-02:15:25",
        "viral_hook": "GTA 6 HAS POLICE FACIAL RECOGNITION 📸🚔",
        "priority": 90,
        "metadata_json": {
            "tags": ["TGG", "CCTV", "FacialRecognition", "NextGenGaming", "GTA6"],
            "caption": "Rockstar Games added real facial recognition to store security cameras! If you commit a crime and walk past a CCTV camera, the cops instantly identify you and trigger a manhunt! 📸👮‍♂️\n\nIs this next-gen AI mechanic too realistic or pure genius? Let us know below! 👇\n\n#GTA6 #TGG #GTA6Details #GTA6AI #NextGenGaming #GamingReels",
        },
    },
    {
        "creator": "Kreek",
        "event_category": "AIRPORT_JET_HEIST",
        "headline": "First Attempt To Infiltrate Vice City Airport & Steal Jet",
        "stream_url": "https://www.youtube.com/watch?v=dy-oCN2NxfA",
        "stream_timestamp_offset": "03:19:45",
        "section_range": "*03:19:45-03:20:55",
        "viral_hook": "STEALING A JET IN GTA 6 (IMPOSSIBLE) ✈️🔥",
        "priority": 88,
        "metadata_json": {
            "tags": ["Kreek", "GTA6Airport", "StealJet", "AirDefense", "GTA6"],
            "caption": "Can you steal a commercial jet or military aircraft in GTA 6? Watch what happens when you breach the runway security perimeter at Vice City International! ✈️🤯\n\nक्या GTA 6 में प्लेन चुराना आसान है या इम्पॉसिबल? कमेंट्स में बताओ! 👇\n\n#GTA6 #Kreek #AirportHeist #ViceCity #StealJet #GamingReels",
        },
    },
    {
        "creator": "8bit Goldy",
        "event_category": "NIGHTCLUB_VIP",
        "headline": "8bit Goldy Enters Vice City Underground Nightclub In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=NdR6owrFWvA",
        "stream_timestamp_offset": "02:08:00",
        "section_range": "*02:08:00-02:09:10",
        "viral_hook": "GTA 6 UNDERGROUND NIGHTCLUB VIBES 🎧🔥",
        "priority": 86,
        "metadata_json": {
            "tags": ["8bitGoldy", "Nightclub", "ViceCityMusic", "GTA6Vibes", "Gaming"],
            "caption": "8bit Goldy discovered the underground neon nightclub in Vice City! Real club acoustics, bass reverberation, and dynamic lighting that matches the live DJ! 🎧✨\n\nक्या Vice City की नाइटलाइफ़ GTA 4 और 5 से आगे निकल गई? कमेंट में बताओ! 👇\n\n#GTA6 #8bitGoldy #Nightclub #ViceCity #GTA6Vibes #GamingReels",
        },
    },
    {
        "creator": "RakaZone Gaming",
        "event_category": "NPC_RAGDOLL_PHYSICS",
        "headline": "RakaZone Punches Florida Man NPC - Ragdoll Physics Are Unreal",
        "stream_url": "https://www.youtube.com/watch?v=GCkc4t1ZWYs",
        "stream_timestamp_offset": "01:45:15",
        "section_range": "*01:45:15-01:46:25",
        "viral_hook": "GTA 6 RAGDOLL PHYSICS ARE NEXT LEVEL 🥊💀",
        "priority": 84,
        "metadata_json": {
            "tags": ["RakaZone", "NPCFight", "Ragdoll", "FloridaMan", "GTA6"],
            "caption": "RakaZone got into a fistfight with a chaotic Florida man outside a diner! The physics, facial muscle twitches, and ragdoll weight are mind-blowing! 🥊🤣\n\nGTA 6 के hand-to-hand combat को 10 में से कितने नंबर दोगे? कमेंट करो! 👇\n\n#GTA6 #RakaZone #FloridaMan #RagdollPhysics #GTA6Combat #GamingReels",
        },
    },
    {
        "creator": "Dattrax Plays",
        "event_category": "YACHT_HEIST",
        "headline": "Dattrax Steals Multimillion Dollar Yacht & Escapes On Jet Ski",
        "stream_url": "https://www.youtube.com/watch?v=isL0EoUff1A",
        "stream_timestamp_offset": "03:30:00",
        "section_range": "*03:30:00-03:31:10",
        "viral_hook": "STEALING A BILLIONAIRE YACHT IN GTA 6 🛥️💨",
        "priority": 82,
        "metadata_json": {
            "tags": ["Dattrax", "YachtTheft", "JetSki", "WaterPhysics", "GTA6"],
            "caption": "Dattrax boarded a luxury super-yacht off Starfish Island and led the Coast Guard on a high-speed jet ski chase across the bay! 🛥️🌊\n\nक्या आपको लगता है GTA 6 का वॉटर ग्राफिक्स अब तक का सबसे बेस्ट है? कमेंट करो! 👇\n\n#GTA6 #Dattrax #YachtHeist #WaterPhysics #ViceCity #GamingReels",
        },
    },
    {
        "creator": "Dattrax Plays",
        "event_category": "ALLIGATOR_ATTACK",
        "headline": "First Florida Alligator Ambush In GTA 6 Everglades",
        "stream_url": "https://www.youtube.com/watch?v=isL0EoUff1A",
        "stream_timestamp_offset": "02:55:00",
        "section_range": "*02:55:00-02:56:10",
        "viral_hook": "FIRST ALLIGATOR ATTACK IN GTA 6 🐊💀",
        "priority": 80,
        "metadata_json": {
            "tags": ["Dattrax", "Alligator", "GTA6Wildlife", "Everglades", "FloridaMan"],
            "caption": "Dattrax ventured deep into the murky Florida Everglades at twilight, only for a massive 12-foot alligator to lunge from the swamp and drag his character under! The water physics and predator AI are terrifying! 🐊🌊\n\nGTA 6 के इस नए swamp wildlife से कौन-कौन डरेगा? कमेंट में बताओ! 👇\n\n#GTA6 #Dattrax #GTA6Wildlife #Everglades #ViceCity #GamingReels",
        },
    },
    {
        "creator": "Ducky Reloaded",
        "event_category": "FIRST_LAUNCH_GLITCH",
        "headline": "First Hilarious Day-1 Physics Glitch Discovered In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=XuYm5c0Xfs4",
        "stream_timestamp_offset": "02:40:00",
        "section_range": "*02:40:00-02:41:05",
        "viral_hook": "FIRST OFFICIAL GTA 6 GLITCH DISCOVERED 💀🤣",
        "priority": 78,
        "metadata_json": {
            "tags": ["DuckyReloaded", "GTA6Glitch", "FirstGlitch", "GTA6Funny", "Gaming"],
            "caption": "Day 1 in GTA 6 and the ragdoll collision physics went completely wild! A simple motorcycle hop launched the character into low orbit! Rockstar didn't see this coming! 🤣🚀\n\nShould Rockstar patch this glitch or leave it in for the laughs? Tell us in the comments! 👇\n\n#GTA6 #GTA6Glitch #FunnyGaming #GamingMoments #GTA6Launch #GamingReels",
        },
    },
    {
        "creator": "CarryisLive",
        "event_category": "STRIP_CLUB_NIGHTLIFE",
        "headline": "CarryMinati VIP Private Room Strip Club Experience In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "stream_timestamp_offset": "01:13:30",
        "section_range": "*01:13:20-01:14:25",
        "viral_hook": "CARRYMINATI STRIP CLUB VIP SCAM IN GTA 6 😭💸",
        "priority": 76,
        "metadata_json": {
            "tags": ["CarryMinati", "StripClub", "GTA6", "CarryisLive", "ViceCity"],
            "caption": "CarryMinati entered the Vice City strip club VIP room expecting something crazy, but the bouncers and dancer completely scammed his in-game cash! His live reaction is absolute comedy gold! 💀😂\n\nक्या Rockstar Games ने इस सीन में Carry भाई का सच में काट दिया? कमेंट्स में बताओ! 👇\n\n#GTA6 #CarryMinati #CarryisLive #ViceCity #GTA6Gameplay #GamingReels",
        },
    },
    {
        "creator": "CarryisLive",
        "event_category": "5_STAR_POLICE_CHASE",
        "headline": "CarryMinati Truck Rampage On Beach & 5-Star Police Shootout Until Wasted",
        "stream_url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "stream_timestamp_offset": "07:44:00",
        "section_range": "*07:44:00-07:45:15",
        "viral_hook": "CARRYMINATI 5-STAR BEACH RAMPAGE IN GTA 6 💀🚨",
        "priority": 74,
        "metadata_json": {
            "tags": ["CarryMinati", "5StarPolice", "BeachRampage", "CarryisLive", "GTA6Wasted", "ViceCity"],
            "caption": "CarryMinati stole a massive wrecking truck, blasted through Vice City beach crowd, fought off 5-star SWAT with a hijacked cruiser, until meeting his hilarious end! Full 75s unedited madness! 💀🔥\n\nCarry भाई का ये वाला मोमेंट सबसे बेस्ट था या स्ट्रिप क्लब वाला? कमेंट्स में बताओ! 👇\n\n#GTA6 #CarryMinati #CarryisLive #BeachRampage #GTA6Gameplay #GamingReels",
        },
    },
    {
        "creator": "Mythpat",
        "event_category": "GPS_CAR_TRACKER",
        "headline": "Mythpat Discovers Secret Underground Passages & GPS Mechanics In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=LMbea5SozeM",
        "stream_timestamp_offset": "01:28:15",
        "section_range": "*01:28:15-01:29:20",
        "viral_hook": "MASSIVE SECRET MAP FOUND IN GTA 6 🗺️🤯",
        "priority": 72,
        "metadata_json": {
            "tags": ["Mythpat", "GTA6", "GPSTracker", "CarTheft", "IndianGamer"],
            "caption": "Mythpat stole an unmarked sedan in Vice City, only to discover the vehicle had a live tracking beacon sending his location directly to the tactical police unit! The detail in GTA 6's map and vehicle electronics is next level! 🚨🚗\n\nक्या आपने GTA 6 में ऐसा कोई सीक्रेट फीचर देखा? कमेंट्स में अपनी राय दो! 👇\n\n#GTA6 #Mythpat #GTA6Secrets #GTA6Map #GamingReels #ViceCity",
        },
    },
    {
        "creator": "Typical Gamer",
        "event_category": "TIRE_BLOWOUT_PHYSICS",
        "headline": "First Car Tire Detachment & Rim Grinding Physics In GTA 6",
        "stream_url": "https://www.youtube.com/watch?v=3QjXNSf6keg",
        "stream_timestamp_offset": "01:52:00",
        "section_range": "*01:52:00-01:53:10",
        "viral_hook": "FIRST TIME A TIRE POPPED OFF IN GTA 6 😱💨",
        "priority": 70,
        "metadata_json": {
            "tags": ["TypicalGamer", "GTA6Physics", "TireDetached", "CarCrash", "GTA6"],
            "caption": "GTA 6 tire physics are unbelievable! When Typical Gamer hit the curb at 120mph, the tire detached completely and the rim started grinding and showering sparks on the concrete! 🤯🔥\n\nWhat do you think about GTA 6 vehicle damage physics? Let us know! 👇\n\n#GTA6 #TypicalGamer #GTA6Physics #CarCrash #GamingReels",
        },
    },
]


class FirstTimeLedger:
    """
    Manages the 'First Time in GTA 6' event database table.
    Ensures all historic discoveries are recorded, prioritized, and tracked through publishing.
    """
    def __init__(self):
        init_db()

    def seed_initial_catalog(self) -> int:
        """Seeds initial historic breakthroughs if table is empty or missing newly curated items."""
        count = 0
        with get_db_session() as session:
            existing_events = {
                e.headline: e for e in session.query(FirstTimeEvent).all()
            }
            for item in SEEDED_FIRST_TIME_EVENTS:
                if item["headline"] in existing_events:
                    ev = existing_events[item["headline"]]
                    if item.get("priority", 0) != ev.priority:
                        ev.priority = item["priority"]
                    if item.get("already_published"):
                        ev.status = "PUBLISHED"
                    elif ev.status == "FAILED":
                        ev.status = "SCHEDULED"
                else:
                    status = "PUBLISHED" if item.get("already_published") else "SCHEDULED"
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
                        status=status,
                    )
                    session.add(ev)
                    count += 1
            if count > 0:
                logger.info(f"[FIRST_TIME_LEDGER] Seeded/Updated {count} historic GTA 6 events into database.")
        return count

    def register_discovered_event(self, event_dict: Dict[str, Any]) -> Optional[str]:
        """
        Registers an autonomously discovered breakthrough event into the database
        with duplicate checking. Returns event_id if inserted, None if duplicate.
        """
        with get_db_session() as session:
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
                    "viral_hook": e.viral_hook,
                    "priority": e.priority,
                    "status": e.status,
                    "rendered_clip_path": e.rendered_clip_path,
                    "metadata": e.metadata_json,
                    "created_at": e.created_at_utc.isoformat() if e.created_at_utc else None,
                }
                for e in events
            ]

    def get_next_scheduled_event(self) -> Optional[Dict[str, Any]]:
        """Pulls the highest-priority SCHEDULED event from the database.
        Automatically retries high-priority curated events if any transient failures occurred."""
        with get_db_session() as session:
            ev = session.query(FirstTimeEvent).filter_by(status="SCHEDULED").order_by(FirstTimeEvent.priority.desc(), FirstTimeEvent.created_at_utc.asc()).first()
            if not ev:
                # Automatic recovery: retry curated events (priority >= 70) that failed due to previous network blocks
                ev = session.query(FirstTimeEvent).filter(
                    FirstTimeEvent.status == "FAILED",
                    FirstTimeEvent.priority >= 70
                ).order_by(FirstTimeEvent.priority.desc(), FirstTimeEvent.created_at_utc.asc()).first()
                if ev:
                    logger.info(f"[FIRST_TIME_LEDGER] Retrying curated event after transient failure: {ev.headline}")
                    ev.status = "SCHEDULED"
                    session.flush()

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
