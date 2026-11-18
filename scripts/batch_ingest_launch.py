"""
Batch Ingest & Auto-Publisher for GTA 6 Launch Streams.
Processes target creator streams, extracts initial launch excitement,
renders kinetic 9:16 vertical shorts, and publishes them to YouTube Shorts.
"""
import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Ensure root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from src.ingest.live_worker import LiveIngestWorker
from src.publishing.publishers import YouTubePublisher, PublishingError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("batch_ingest")

TARGET_STREAMS = [
    {
        "creator": "TGG",
        "url": "https://www.youtube.com/watch?v=xMXp80Cntxw",
        "game": "GTA 6",
        "notes": "73K watching - Global Launch Countdown",
        "priority": 1,
    },
    {
        "creator": "Mythpat",
        "url": "https://www.youtube.com/watch?v=LMbea5SozeM",
        "game": "GTA 6",
        "notes": "32K watching - India Hindi Launch Reaction",
        "priority": 2,
    },
    {
        "creator": "Typical Gamer",
        "url": "https://www.youtube.com/watch?v=3QjXNSf6keg",
        "game": "GTA 6",
        "notes": "25K watching - Free-roam live launch",
        "priority": 3,
    },
    {
        "creator": "Ducky Reloaded",
        "url": "https://www.youtube.com/watch?v=XuYm5c0Xfs4",
        "game": "GTA 6",
        "notes": "32K watching - Marathon launch",
        "priority": 4,
    },
    {
        "creator": "CarryisLive",
        "url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "game": "GTA 6",
        "notes": "CarryMinati Launch Special",
        "priority": 5,
    },
    {
        "creator": "Dattrax Plays",
        "url": "https://www.youtube.com/watch?v=isL0EoUff1A",
        "game": "GTA 6",
        "notes": "10K watching - India Gameplay Live",
        "priority": 6,
    },
    {
        "creator": "RakaZone Gaming",
        "url": "https://www.youtube.com/watch?v=GCkc4t1ZWYs",
        "game": "GTA 6",
        "notes": "3.8K watching - Walkthrough India",
        "priority": 7,
    },
    {
        "creator": "Kreek",
        "url": "https://www.youtube.com/watch?v=dy-oCN2NxfA",
        "game": "GTA 6",
        "notes": "11K watching - Day 1 Live",
        "priority": 8,
    },
    {
        "creator": "AS Gaming",
        "url": "https://www.youtube.com/watch?v=u1OGXGfOEI0",
        "game": "GTA 6",
        "notes": "3.3K watching - First Live Stream",
        "priority": 9,
    },
    {
        "creator": "8bit Goldy",
        "url": "https://www.youtube.com/watch?v=NdR6owrFWvA",
        "game": "GTA 6",
        "notes": "1.7K watching - Welcome to Vice City",
        "priority": 10,
    },
    {
        "creator": "Destin",
        "url": "https://www.youtube.com/watch?v=SJtQRxbFvFg",
        "game": "GTA 6",
        "notes": "1.6K watching - NZ Launch",
        "priority": 11,
    },
]


def run_batch_pipeline(start_from: int = 1, max_items: int = 11, auto_publish_top: int = 4):
    worker = LiveIngestWorker()
    yt_publisher = YouTubePublisher()
    
    print("\n" + "=" * 75)
    print(" VICE DESK 24/7 AI: GTA 6 LAUNCH BATCH INGEST & SHORTS PUBLISHER")
    print(f" Target Streams: {len(TARGET_STREAMS)} | Start: {start_from} | Max: {max_items}")
    print("=" * 75 + "\n")

    summary_path = PROJECT_ROOT / "data" / "gta6_launch_batch_summary.json"
    results = []
    if summary_path.exists():
        try:
            results = json.loads(summary_path.read_text())
        except Exception:
            results = []

    quota_exhausted = False

    for idx, item in enumerate(TARGET_STREAMS, 1):
        if idx < start_from or idx > max_items:
            continue

        creator = item["creator"]
        url = item["url"]
        game = item["game"]
        print(f"\n[{idx}/{len(TARGET_STREAMS)}] Processing Stream: {creator}")
        print(f"    URL: {url} ({item['notes']})")

        try:
            # Execute full AI clipping pipeline
            res = worker.process_url_job(
                url=url,
                creator_name=creator,
                game=game,
                layout_mode="split_cam_game",
                publish_to_youtube=False,
            )

            render_id = res["render_id"]
            video_path = res["output_path"]
            hook = res["hook"]
            title = res["title"]
            caption = res["caption"]
            qc_ok = res["qc_passed"]
            print(f"    -> Rendered: {render_id}.mp4 | QC Passed: {qc_ok}")
            print(f"    -> Viral Hook: {hook}")
            print(f"    -> Title: {title}")

            short_url = None
            if idx <= auto_publish_top and not quota_exhausted:
                print(f"    -> Uploading to YouTube Shorts...")
                try:
                    yt_res = yt_publisher.upload_short(
                        video_path=video_path,
                        title=f"{creator} GTA 6 LAUNCH! {hook} #Shorts",
                        description=f"{caption}\n\nLive stream: {url}\nAutomated by ViceDesk 24/7 AI Intelligence.",
                        privacy_status="public",
                    )
                    short_url = yt_res.get("video_url")
                    print(f"    -> [PUBLISHED] YouTube Short: {short_url}")
                except PublishingError as pe:
                    err_msg = str(pe)
                    if "quotaExceeded" in err_msg or "daily limit" in err_msg.lower():
                        print(f"    -> YouTube Daily API Quota limit reached. Marking remaining clips for manual 1-click publishing.")
                        quota_exhausted = True
                    else:
                        print(f"    -> YouTube Upload warning: {pe}")
            
            results.append({
                "creator": creator,
                "url": url,
                "render_id": render_id,
                "video_path": video_path,
                "hook": hook,
                "title": title,
                "qc_passed": qc_ok,
                "short_url": short_url,
                "status": "PUBLISHED" if short_url else "READY_FOR_REVIEW",
            })

            # Save progress after each clip
            summary_path.write_text(json.dumps(results, indent=2))

        except Exception as e:
            logger.error(f"Failed processing stream for {creator}: {e}", exc_info=True)
            results.append({
                "creator": creator,
                "url": url,
                "status": "FAILED",
                "error": str(e),
            })
            summary_path.write_text(json.dumps(results, indent=2))

    # Summary Output
    print("\n" + "=" * 75)
    print(" BATCH INGESTION & PUBLISHING SUMMARY")
    print("=" * 75)
    for r in results:
        status_str = f"[{r.get('status')}]"
        creator_str = r.get("creator", "Unknown")
        short = r.get("short_url") or "Saved locally in dashboard"
        print(f"{status_str:<18} {creator_str:<16} | Short: {short}")

    # Save summary report to JSON
    summary_path = PROJECT_ROOT / "data" / "gta6_launch_batch_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(results, indent=2))
    print(f"\nBatch report saved to: {summary_path}")
    return results


if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    max_c = int(sys.argv[2]) if len(sys.argv) > 2 else 11
    pub_count = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    run_batch_pipeline(start_from=start, max_items=max_c, auto_publish_top=pub_count)
