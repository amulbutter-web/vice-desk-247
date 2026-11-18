"""
Viral Trend & Moment Scout Engine (A04_SCOUT / Trend Hunter).
Autonomously discovers, catalogs, and targets the most viral in-game moments
across live GTA 6 streams (e.g. Strip Club / Malibu visits, 5-Star military chases,
ocean/swamp alligator attacks, Lucia & Jason drama, wild Florida Man encounters).
"""
import os
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from src.core.groq_pool import GroqPool

logger = logging.getLogger("trend_scout")


@dataclass
class ViralHotspot:
    id: str
    name: str
    category: str
    keywords: List[str]
    groq_context: str
    default_hooks: List[str]
    priority: int = 5


# Curated live intelligence of high-heat GTA 6 locations & viral scenarios
GTA6_VIRAL_HOTSPOTS: List[ViralHotspot] = [
    ViralHotspot(
        id="strip_club_nightlife",
        name="Vice City Strip Club & Malibu Club",
        category="nightlife",
        keywords=["strip club", "malibu", "club", "dance", "nightclub", "shots", "bar"],
        groq_context="Streamer discovers and enters the Vice City Strip Club or Malibu Club with hilarious and shocked reactions.",
        default_hooks=[
            "CARRYMINATI IN STRIP CLUB GTA 6 💀🔞",
            "HE FOUND THE STRIP CLUB IN GTA 6 😭😂",
            "GTA 6 STRIP CLUB GRAPHICS ARE INSANE 🤯",
            "BHAI KAHAN PAHUCH GAYE YE?! 💀",
        ],
        priority=10,
    ),
    ViralHotspot(
        id="police_5star_chaos",
        name="5-Star Military Wanted Level Chase",
        category="action",
        keywords=["cops", "5 star", "police", "swat", "tank", "wanted", "chase", "helicopter"],
        groq_context="Streamer triggers maximum 5-star police response with military tanks, attack helicopters, and crazy shootouts.",
        default_hooks=[
            "5-STAR WANTED LEVEL IN GTA 6 🚨🔥",
            "GTA 6 COPS ARE MERCILESS 😱💀",
            "FIRST MILITARY TANK IN GTA 6 🤯",
            "HE SURVIVED 5 STARS IN VICE CITY 🚔",
        ],
        priority=9,
    ),
    ViralHotspot(
        id="beach_ocean_alligator",
        name="Ocean Water Physics & Florida Alligators",
        category="physics",
        keywords=["beach", "water", "alligator", "ocean", "swim", "crocodile", "swamp"],
        groq_context="Streamer tests hyper-realistic ocean water physics, crowded Vice City beaches, or gets ambushed by an alligator in the Florida Everglades.",
        default_hooks=[
            "GTA 6 WATER PHYSICS WILL SHOCK YOU 🌊",
            "ALLIGATOR ATTACK IN GTA 6 🐊💀",
            "VICE CITY BEACH IN 4K IS CRAZY 🏖️",
            "FLORIDA MAN JUMPSCARE IN GTA 6 😂",
        ],
        priority=9,
    ),
    ViralHotspot(
        id="secret_map_locations",
        name="Hidden Vice City Secrets & Map Exploration",
        category="map_exploration",
        keywords=["secret", "map", "hidden", "yacht", "military base", "swamp", "island", "underwater", "shipwreck"],
        groq_context="Streamer discovers hidden secret areas on the GTA 6 map, secret islands, sunken shipwrecks, or infiltrates restricted naval military bases.",
        default_hooks=[
            "SECRET GTA 6 MAP LOCATION FOUND 🗺️😱",
            "THEY HID THIS ON THE GTA 6 MAP 🤯",
            "UNDERWATER SHIPWRECK IN GTA 6 🌊🚢",
            "RESTRICTED MILITARY BASE INFILTRATION 🚨",
        ],
        priority=10,
    ),
    ViralHotspot(
        id="nextgen_physics_destruction",
        name="Next-Gen Physics & Vehicle Destruction",
        category="physics",
        keywords=["physics", "crash", "destruction", "tire", "glass", "engine", "damage", "deformation", "hurricane"],
        groq_context="Testing shocking next-gen physics in GTA 6: tire blowouts, rim sparks, engine fires, volumetric weather, and hyper-realistic crash deformation.",
        default_hooks=[
            "GTA 6 PHYSICS WILL BLOW YOUR MIND 🤯💥",
            "REALEST CAR CRASH PHYSICS EVER 😱🚗",
            "VOLUMETRIC HURRICANE IN GTA 6 🌪️⛈️",
            "TIRE BLOWOUT RIM PHYSICS IN 4K 💨🔥",
        ],
        priority=10,
    ),
    ViralHotspot(
        id="supercar_top_speed",
        name="Fastest Supercar Vice City Speed Test",
        category="driving",
        keywords=["supercar", "ferrari", "lamborghini", "speed", "highway", "drift", "nitro"],
        groq_context="Streamer steals an exotic high-end supercar and maxes out top speed across Vice City highway bridges.",
        default_hooks=[
            "FASTEST SUPERCAR IN GTA 6 🏎️💨",
            "GTA 6 CAR SOUNDS ARE UNREAL 🔊",
            "DRIFTING ACROSS VICE CITY HIGHWAY 🤯",
            "TOP SPEED CRASH IN GTA 6 💀",
        ],
        priority=8,
    ),
    ViralHotspot(
        id="florida_man_crazy_npc",
        name="Hilarious Florida Man NPC AI Interactions",
        category="comedy",
        keywords=["florida man", "npc", "crazy", "fight", "leonida", "hilarious", "weird"],
        groq_context="Unpredictable hilarious interaction with crazy naked Florida Man NPCs or wild street fights in Leonida.",
        default_hooks=[
            "GTA 6 NPCS HAVE NO CHILL 😭😂",
            "AVERAGE FLORIDA MAN IN GTA 6 💀",
            "THIS NPC INTERACTION IS UNREAL 🤣",
            "BRO GOT ROASTED BY A GTA 6 NPC 💀",
        ],
        priority=9,
    ),
]


class TrendScoutEngine:
    """
    Orchestrates continuous stream discovery across multiple hours of live gameplay.
    Instead of checking static minutes, it computes dynamic offsets across the live timeline.
    """

    def __init__(self, groq_pool: Optional[GroqPool] = None):
        self.groq_pool = groq_pool or GroqPool()
        self.hotspots = sorted(GTA6_VIRAL_HOTSPOTS, key=lambda h: h.priority, reverse=True)
        self.launch_utc = datetime(2026, 11, 18, 11, 0, 0, tzinfo=timezone.utc)  # 4:30 PM IST

    def get_dynamic_section_ranges(self, current_hour_offset: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Generates progressive, multi-hour time windows matching real gameplay progression.
        """
        now = datetime.now(timezone.utc)
        elapsed_hours = max(1.0, (now - self.launch_utc).total_seconds() / 3600.0) if current_hour_offset is None else current_hour_offset

        ranges = [
            # 1. Strip Club / Nightlife (typically visited ~1h to 2h into free-roam)
            {
                "section": "*01:10:00-01:10:35",
                "hotspot": self.hotspots[0],  # strip_club_nightlife
                "label": "Strip Club & Nightlife",
            },
            # 2. 5-Star Police Chase / Chaos (~1h 45m in)
            {
                "section": "*01:45:00-01:45:35",
                "hotspot": self.hotspots[1],  # police_5star_chaos
                "label": "5-Star Military Chase",
            },
            # 3. Beach & Alligators (~2h 15m in)
            {
                "section": "*02:15:00-02:15:35",
                "hotspot": self.hotspots[2],  # beach_ocean_alligator
                "label": "Beach Physics & Alligators",
            },
            # 4. Supercar Highway Speed (~3h in)
            {
                "section": "*03:00:00-03:00:35",
                "hotspot": self.hotspots[4],  # supercar_top_speed
                "label": "Supercar Top Speed",
            },
            # 5. Florida Man Crazy NPCs (~3h 40m in)
            {
                "section": "*03:40:00-03:40:35",
                "hotspot": self.hotspots[5],  # florida_man_crazy_npc
                "label": "Florida Man NPC Encounters",
            },
            # 6. Current Live Edge (most recent 30-second window)
            {
                "section": f"*0{int(elapsed_hours):01d}:20:00-0{int(elapsed_hours):01d}:20:35",
                "hotspot": self.hotspots[0],
                "label": "Recent Live Edge",
            },
        ]
        return ranges

    def craft_viral_metadata(self, creator_name: str, hotspot: ViralHotspot, lang: str = "en") -> Dict[str, str]:
        """
        Uses Groq A06_HOOK and A08_COPYWRITER to craft bilingual, scroll-stopping hooks.
        """
        try:
            hook = self.groq_pool.generate_viral_hook(
                creator_name=creator_name,
                game="GTA 6",
                context_notes=hotspot.groq_context,
                agent_role="A06_HOOK",
            )
        except Exception:
            hook = hotspot.default_hooks[0]

        try:
            meta = self.groq_pool.generate_reels_metadata(
                creator_name=creator_name,
                game="GTA 6",
                hook=hook,
            )
            title = meta.get("title", f"{creator_name} - {hook}")
            caption = meta.get("caption", f"Watch {creator_name} experience {hotspot.name} in GTA 6!")
        except Exception:
            title = f"{creator_name} {hotspot.name}! 🔥 #GTA6 #Shorts"
            caption = f"{creator_name} exploring {hotspot.name} in GTA 6 live! #GTA6 #ViceCity #Reels"

        return {
            "hook": hook,
            "title": title,
            "caption": caption,
            "hotspot_id": hotspot.id,
            "hotspot_name": hotspot.name,
        }
