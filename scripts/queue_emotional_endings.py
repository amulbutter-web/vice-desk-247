import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.detection.first_time_ledger import FirstTimeLedger

def queue_endings():
    ledger = FirstTimeLedger()

    events = [
        {
            "creator": "Promotion Zone",
            "event_category": "EMOTIONAL_STORY_ENDING",
            "headline": "GTA 6 Sad Ending: Jason Sacrifices Himself To Save Lucia",
            "stream_url": "https://www.youtube.com/watch?v=r9snEnWzBWA",
            "stream_timestamp_offset": "00:01:15",
            "section_range": "*00:01:15-00:02:20",
            "viral_hook": "JASON SACRIFICED HIMSELF 😭💔",
            "priority": 100,
            "metadata_json": {
                "caption": "Wait for the ending... Jason actually sacrificed himself for Lucia. 💔😭 Did you choose this ending? Comment below! 👇\n\n#GTA6 #GTA6Ending #JasonAndLucia #SadEnding #GamingReels #Shorts",
                "title": "GTA 6 Sad Ending: Jason Sacrifice #Shorts #GTA6",
                "lang": "hi",
                "source_views": 25425,
                "duration_sec": 65,
            }
        },
        {
            "creator": "Dan Allen Gaming",
            "event_category": "EMOTIONAL_STORY_ENDING",
            "headline": "GTA 6 Lucia Reveals The Truth To Jason Ending Confrontation",
            "stream_url": "https://www.youtube.com/watch?v=WtKDnL0Anco",
            "stream_timestamp_offset": "00:00:45",
            "section_range": "*00:00:45-00:01:50",
            "viral_hook": "LUCIA REVEALED THE TRUTH 😱",
            "priority": 99,
            "metadata_json": {
                "caption": "She kept this secret from him the whole time... 🤯 Watch his reaction when he finds out. Did you see this coming? Comment below! 👇\n\n#GTA6 #GTA6Ending #Lucia #Jason #ViceCity #StoryEnding #Shorts",
                "title": "Lucia Reveals Truth To Jason in GTA 6 #Shorts #GTA6",
                "lang": "en",
                "source_views": 400052,
                "duration_sec": 65,
            }
        },
        {
            "creator": "MELOO",
            "event_category": "EMOTIONAL_STORY_ENDING",
            "headline": "GTA 6 Secret Good Ending: Jason & Lucia Both Survive",
            "stream_url": "https://www.youtube.com/watch?v=DYDz_cIgoAw",
            "stream_timestamp_offset": "00:02:00",
            "section_range": "*00:02:00-00:03:05",
            "viral_hook": "THEY BOTH ACTUALLY SURVIVED?! 🤯",
            "priority": 99,
            "metadata_json": {
                "caption": "Most players got the sad ending, but watch how they both survive! 🚀🔥 Did you unlock this secret ending? Tell us in the comments! 👇\n\n#GTA6 #GTA6Ending #GoodEnding #JasonAndLucia #SecretEnding #GamingReels #Shorts",
                "title": "GTA 6 Secret Good Ending #Shorts #GTA6",
                "lang": "en",
                "source_views": 1853524,
                "duration_sec": 65,
            }
        }
    ]

    for ev in events:
        res = ledger.register_discovered_event(ev)
        print(f"Registered '{ev['headline']}': {res}")

if __name__ == "__main__":
    queue_endings()
