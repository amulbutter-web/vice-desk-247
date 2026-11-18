"""
Tests real CarryMinati Vice City / Strip Club moment processing and publishing.
Renders 1080p Blur-Fill Ultra clip and publishes directly to Instagram Reels (@hritiksingh_8).
"""
import sys, os, json, urllib.request
from pathlib import Path

# Load .env
env_file = Path("C:/Users/rudra/Documents/Earn/website S/gaming-content-intelligence/.env")
for line in env_file.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, _, v = line.partition("=")
        os.environ[k.strip()] = v.strip().strip('"')

sys.path.insert(0, "C:/Users/rudra/Documents/Earn/website S/gaming-content-intelligence")
from src.ingest.live_worker import LiveIngestWorker
from src.publishing.publishers import InstagramPublisher

worker = LiveIngestWorker()
ig_pub = InstagramPublisher()

# Verify Instagram connection first
status = ig_pub.verify_credentials()
print(f"[INSTAGRAM STATUS] {status.get('message')}")
if not status.get("valid"):
    print("Instagram not valid, stopping.")
    sys.exit(1)

sample_file = Path("C:/Users/rudra/Documents/Earn/website S/gaming-content-intelligence/data/temp/carry_test.mp4")
if not sample_file.exists():
    print(f"Error: {sample_file} not found.")
    sys.exit(1)

print(f"\n[1] Processing real CarryMinati live stream footage ({sample_file.stat().st_size / 1024 / 1024:.2f} MB)...")
res = worker.process_url_job(
    url=str(sample_file),
    creator_name="CarryisLive",
    game="GTA 6",
    layout_mode="blur_fill",
    publish_to_youtube=False,
)

render_id = res.get("render_id")
out_path = res.get("output_path")
hook = "CARRYMINATI IN STRIP CLUB GTA 6 💀🔞"
title = "CarryMinati Found The Strip Club in GTA 6! 😂🔥"
caption = (
    "CarryMinati roaming in Vice City and found the strip club! 💀🎮\n\n"
    "Full stream on CarryisLive! #GTA6 #CarryMinati #ViceCity #GTA6Launch #GamingReels #Reels #Shorts"
)

print(f"[2] Render Complete!")
print(f"    Render ID: {render_id}")
print(f"    Output Path: {out_path} ({Path(out_path).stat().st_size / 1024 / 1024:.2f} MB)")

# Copy to static web cdn directory so Railway / Meta can download it
cdn_target = Path("C:/Users/rudra/Documents/Earn/website S/gaming-content-intelligence/src/server/static") / f"{render_id}.mp4"
import shutil
shutil.copyfile(out_path, cdn_target)
print(f"[3] Staged to static CDN: {cdn_target}")

# Print upload payload
print(f"\n[4] Ready for Instagram upload to @{status.get('username')}:")
print(f"    Title: {title}")
print(f"    Hook: {hook}")
