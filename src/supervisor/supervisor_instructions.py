"""
ViceDesk Supervisor Directive & Core Operating Instructions.
Persistent operational mandate stored in the codebase and memory.
Codifies the supervisor's core autonomous rules:
1. STRICT GAME FOCUS: GTA 6 ONLY (Nothing else).
2. DAILY VOLUME TARGET: 50 videos per day minimum.
3. 15 DIVERSE GTA 6 CREATORS & CHANNELS:
   - Techno Gamerz
   - CarryisLive
   - Mythpat
   - IShowSpeed
   - Typical Gamer
   - TGG
   - RakaZone Gaming
   - 8bit Goldy
   - AS Gaming
   - KreekCraft
   - Live Insaan
   - TheRadBrad
   - Dattrax Plays
   - Ducky Reloaded
   - Jason & Mandy (GTA 6 Story Missions)
4. AUTONOMOUS TREND DISCOVERY:
   - Automatically monitors trending story missions (e.g. Mandy Pipework), Easter eggs, AI physics.
   - Never waits for human operator prompts.
5. ZERO-LEAK DISK POLICY:
   - Immediate unlinking (deletion) of raw downloaded footage after rendering.
   - Immediate unlinking (deletion) of rendered master files after cloud CDN upload and social publishing.
   - Local/cloud container storage footprint remains under 50 MB at all times.
6. CONTINUOUS SUPERVISORY WATCHDOG:
   - Auto-revives daemon if stalled.
   - Monitors Instagram Meta publishing limits (100/day limit, 50/day target).
"""
import os
import json
from typing import List, Dict, Any

SUPERVISOR_INSTRUCTIONS: Dict[str, Any] = {
    "version": "2.0.0",
    "directive": "AUTONOMOUS_CLOUD_SUPERVISOR",
    "primary_game": "GTA 6",
    "target_daily_uploads": 50,
    "max_daily_quota": 100,
    "creator_count": 15,
    "target_creators": [
        {"name": "Techno Gamerz",   "lang": "hi", "priority": 100, "sample_url": "https://www.youtube.com/watch?v=169ZzvPxvvM"},
        {"name": "CarryisLive",     "lang": "hi", "priority": 98,  "sample_url": "https://www.youtube.com/watch?v=irNhWMG560k"},
        {"name": "Mythpat",         "lang": "hi", "priority": 95,  "sample_url": "https://www.youtube.com/watch?v=LMbea5SozeM"},
        {"name": "IShowSpeed",      "lang": "en", "priority": 95,  "sample_url": "https://www.youtube.com/watch?v=qSyo5d-dVzA"},
        {"name": "Typical Gamer",   "lang": "en", "priority": 90,  "sample_url": "https://www.youtube.com/watch?v=3QjXNSf6keg"},
        {"name": "TGG",             "lang": "en", "priority": 88,  "sample_url": "https://www.youtube.com/watch?v=xMXp80Cntxw"},
        {"name": "RakaZone Gaming", "lang": "hi", "priority": 85,  "sample_url": "https://www.youtube.com/watch?v=GCkc4t1ZWYs"},
        {"name": "8bit Goldy",      "lang": "hi", "priority": 82,  "sample_url": "https://www.youtube.com/watch?v=NdR6owrFWvA"},
        {"name": "AS Gaming",       "lang": "hi", "priority": 80,  "sample_url": "https://www.youtube.com/watch?v=u1OGXGfOEI0"},
        {"name": "KreekCraft",      "lang": "en", "priority": 78,  "sample_url": "https://www.youtube.com/watch?v=dy-oCN2NxfA"},
        {"name": "Live Insaan",     "lang": "hi", "priority": 75,  "sample_url": "https://www.youtube.com/watch?v=84_m_LgUv3Q"},
        {"name": "TheRadBrad",      "lang": "en", "priority": 72,  "sample_url": "https://www.youtube.com/watch?v=eEERhKQZWmY"},
        {"name": "Dattrax Plays",   "lang": "hi", "priority": 70,  "sample_url": "https://www.youtube.com/watch?v=isL0EoUff1A"},
        {"name": "Ducky Reloaded",  "lang": "en", "priority": 68,  "sample_url": "https://www.youtube.com/watch?v=XuYm5c0Xfs4"},
        {"name": "Jason & Mandy",   "lang": "en", "priority": 99,  "sample_url": "https://www.youtube.com/watch?v=_8-c3XJH5og"},
    ],
    "editorial_standards": {
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "fps": 60,
        "style": "blur_fill",
        "subtitles": {
            "engine": "groq_whisper",
            "format": "ASS_kinetic",
            "style": "alex_hormozi_gold",
            "highlight_color": "#E6B325",
            "safe_bottom_margin_px": 420,
            "transliteration": "roman_hinglish",
        },
        "target_duration_sec": 70,
    },
    "storage_policy": {
        "auto_purge_raw_ingest": True,
        "auto_purge_rendered_after_publish": True,
        "max_storage_watermark_mb": 100,
    }
}
