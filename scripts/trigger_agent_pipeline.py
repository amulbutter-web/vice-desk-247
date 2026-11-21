"""
ViceDesk Hierarchical Multi-Agent Execution Trigger.
Engages Tier 1 (ChiefSupervisorAgent), Tier 2 Supervisors, and Tier 3 Specialist Agents
to autonomously ingest, render with kinetic subtitles, QC verify, and publish Reel #56 to Instagram Reels.
"""
import sys
import os
import time
import json
from pathlib import Path

# Workspace Root
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Load environment
env_file = ROOT_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip().strip('"')

from src.supervisor.hierarchy import ChiefSupervisorAgent
from src.detection.first_time_ledger import FirstTimeLedger

def trigger_super_agent_pipeline():
    print("=" * 65)
    print("🚀 ENGAGING SUPREME AGENT ORGANIZATIONAL PYRAMID FOR GTA 6 REEL #58")
    print("=" * 65)

    chief = ChiefSupervisorAgent()

    # The high-emotion viral moment requested by user: GTA 6 Sad Ending (Jason Sacrifice)
    event = {
        "id": "7864ba48-eb3f-4850-979e-95ca188fddaf",
        "creator": "Promotion Zone",
        "headline": "GTA 6 Sad Ending: Jason Sacrifices Himself To Save Lucia",
        "stream_url": "https://www.youtube.com/watch?v=r9snEnWzBWA",
        "section_range": "*00:01:15-00:02:20",
        "viral_hook": "JASON SACRIFICED HIMSELF 😭💔",
        "category": "EMOTIONAL_STORY_ENDING",
        "metadata": {
            "caption": """Wait for the ending... Jason actually sacrificed himself for Lucia. 💔😭 Did you choose this ending? Comment your reaction below! 👇

Streamer: Promotion Zone

#GTA6 #GTAVI #GTA6Ending #JasonAndLucia #SadEnding #GamingReels #ReelsViral #Shorts #RockstarGames #HindiGaming"""
        }
    }

    print(f"\n[TIER 1 EXECUTIVE] ChiefSupervisorAgent activated.")
    print(f"[TIER 1 EXECUTIVE] Target Event: {event['headline']}")
    print(f"                  Creator: {event['creator']} | URL: {event['stream_url']}")
    print(f"                  Section: {event['section_range']}")

    # 1. Tier 2 Strategy Review
    print("\n[TIER 2 STRATEGY] ContentStrategyAndAnalyticsSupervisor reviewing clip...")
    prepared_clip = chief.strategy_manager.review_and_prepare_clip(
        event=event,
        selector=chief.editorial_manager.clip_selector
    )
    print(f"[TIER 2 STRATEGY] Approved! Hook: '{prepared_clip.get('hook')}'")

    # 2. Tier 2 Editorial & Safe Rendering (Groq Whisper Word Subs + 9:16 Canvas)
    print("\n[TIER 2 PRODUCTION] EditorialProductionSupervisor directing SafeRendererAgent...")
    t0 = time.time()
    production_res = chief.editorial_manager.produce_video(prepared_clip)

    if production_res.get("status") != "SUCCESS":
        print(f"❌ [PRODUCTION FAILED]: {production_res.get('reason')}")
        sys.exit(1)

    video_path = production_res.get("video_path")
    print(f"✅ [TIER 2 PRODUCTION] Master Reel Rendered in {time.time()-t0:.1f}s!")
    print(f"                       Path: {video_path}")
    print(f"                       Size: {Path(video_path).stat().st_size / (1024*1024):.2f} MB")

    # 3. Tier 2 Publishing & Quality Assurance
    print("\n[TIER 2 PUBLISHING & QC] PublishingAndQcSupervisor inspecting master & publishing...")
    pub_res = chief.publishing_manager.inspect_and_publish(production_res)

    if pub_res.get("status") != "PUBLISHED":
        print(f"❌ [PUBLISH FAILED]: {pub_res.get('reason')}")
        sys.exit(1)

    remote_id = pub_res.get("remote_id")
    permalink = pub_res.get("permalink") or f"https://www.instagram.com/reel/{remote_id}/"

    print("\n" + "=" * 65)
    print(f"🎉 REEL #58 SUCCESSFULLY PUBLISHED TO INSTAGRAM REELS!")
    print(f"   Target Account: @hritiksingh_8 (ID: 17841467596649798)")
    print(f"   Media ID:       {remote_id}")
    print(f"   Live Reel URL:  {permalink}")
    print("=" * 65)

    # 4. Update Supabase Ledger
    try:
        import urllib.request
        sync_url = "https://vice-desk-intelligence-production.up.railway.app/api/ledger/record_publish"
        payload = {
            "event_id": event["id"],
            "media_id": remote_id,
            "permalink": permalink,
            "rendered_path": str(video_path),
        }
        req_sync = urllib.request.Request(
            sync_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req_sync, timeout=10) as r_s:
            print(f"[LEDGER] Recording publish receipt in database: {r_s.status} {r_s.read().decode()}")
    except Exception as se:
        print(f"[LEDGER] Sync note: {se}")

    return permalink

if __name__ == "__main__":
    trigger_super_agent_pipeline()
