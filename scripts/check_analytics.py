"""
YouTube Analytics check and pending upload script.
Checks channel stats, video analytics, and attempts to upload remaining 3 pending videos.
"""
import sys, os, json, urllib.request, urllib.parse
from pathlib import Path

# Load .env
env_file = Path("C:/Users/rudra/Documents/Earn/website S/gaming-content-intelligence/.env")
for line in env_file.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, _, v = line.partition("=")
        os.environ[k.strip()] = v.strip().strip('"')

sys.path.insert(0, "C:/Users/rudra/Documents/Earn/website S/gaming-content-intelligence")
from src.publishing.publishers import YouTubePublisher

pub = YouTubePublisher()
tok = pub.refresh_access_token_if_needed()
print(f"[TOKEN] Got token: {tok[:30]}...")


def yt_get(endpoint, params):
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}"
    full_url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full_url, headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


# 1. Channel info
try:
    ch = yt_get("channels", {"part": "snippet,statistics,status", "mine": "true"})
    item = ch.get("items", [{}])[0]
    stats = item.get("statistics", {})
    print(f"\n=== CHANNEL ANALYTICS ===")
    print(f"  Title: {item.get('snippet', {}).get('title')}")
    print(f"  Subscribers: {stats.get('subscriberCount', '?')}")
    print(f"  Total Views: {stats.get('viewCount', '?')}")
    print(f"  Total Videos: {stats.get('videoCount', '?')}")
except Exception as e:
    print(f"Channel fetch error: {e}")

# 2. Per-video stats for published shorts
published_ids = [
    ("TGG",             "jhRpk_QkcDM"),
    ("Mythpat",         "1GVrgEby71A"),
    ("Typical Gamer",   "tfhe6RLEQsU"),
    ("Ducky Reloaded",  "_J-jzlaikEE"),
    ("CarryisLive",     "olQSHO8MAjI"),
    ("Dattrax Plays",   "fCrxJnWjpe8"),
    ("RakaZone Gaming", "h2Bzk1xumkQ"),
    ("Kreek",           "6e8BfbBKIZg"),
]
ids_str = ",".join(vid_id for _, vid_id in published_ids)
try:
    vdata = yt_get("videos", {"part": "snippet,statistics,status", "id": ids_str})
    print(f"\n=== PUBLISHED SHORTS ANALYTICS ===")
    total_views = 0
    for v_item in vdata.get("items", []):
        s = v_item.get("statistics", {})
        views = int(s.get("viewCount", 0))
        likes = int(s.get("likeCount", 0))
        comments = int(s.get("commentCount", 0))
        total_views += views
        status = v_item.get("status", {}).get("privacyStatus", "?")
        title = v_item.get("snippet", {}).get("title", "")[:45]
        vid_id = v_item.get("id")
        creator = next((c for c, i in published_ids if i == vid_id), vid_id)
        print(f"  [{creator}] {title}")
        print(f"    Views: {views:,}  |  Likes: {likes:,}  |  Comments: {comments}  |  Status: {status}")
    print(f"\n  TOTAL VIEWS: {total_views:,}")
except Exception as e:
    print(f"Video stats error: {e}")

# 3. Try uploading remaining 3
pending = [
    {"creator": "AS Gaming",   "render": "render-fcd534ac.mp4",
     "title": "AS Gaming GTA 6 LAUNCH REACTION 🔥 #Shorts #GTA6",
     "desc": "AS Gaming first reaction to GTA 6 launch moment! Watch the hype! #GTA6 #Shorts #Gaming"},
    {"creator": "8bit Goldy",  "render": "render-5277a6d4.mp4",
     "title": "8bit Goldy LOSES IT at GTA 6 Launch 😱 #Shorts #GTA6",
     "desc": "8bit Goldy's GTA 6 launch reaction! Welcome to Vice City! #GTA6 #Shorts"},
    {"creator": "Destin",      "render": "render-411402c2.mp4",
     "title": "Destin NZ GTA 6 First Reaction 🤯 #Shorts #GTA6",
     "desc": "Destin's New Zealand GTA 6 launch! First to play! #GTA6 #Shorts"},
]
print(f"\n=== ATTEMPTING PENDING UPLOADS ===")
rendered_base = Path("C:/Users/rudra/Documents/Earn/website S/gaming-content-intelligence/data/rendered")
for p in pending:
    rpath = rendered_base / p["render"]
    if not rpath.exists():
        print(f"  SKIP {p['creator']}: file missing")
        continue
    mb = rpath.stat().st_size / 1024 / 1024
    print(f"  Uploading {p['creator']} ({mb:.1f}MB)...")
    try:
        result = pub.upload_short(
            video_path=str(rpath),
            title=p["title"],
            description=p["desc"],
            privacy_status="public",
            retry_on_401=True,
        )
        url = result.get("video_url", "?")
        print(f"    SUCCESS: {url}")
    except Exception as e:
        err = str(e)
        if "uploadLimitExceeded" in err or "quota" in err.lower():
            print(f"    QUOTA STILL HIT: Daily limit not reset yet. Retry after midnight IST.")
        else:
            print(f"    ERROR: {err[:200]}")
