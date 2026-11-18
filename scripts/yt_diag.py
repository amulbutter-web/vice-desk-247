"""
Quick YouTube API diagnostic - check if API is enabled in this project.
"""
import os, json, urllib.request, urllib.parse
from pathlib import Path

env_file = Path("C:/Users/rudra/Documents/Earn/website S/gaming-content-intelligence/.env")
for line in env_file.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, _, v = line.partition("=")
        os.environ[k.strip()] = v.strip().strip('"')

client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
print(f"Client ID project: {client_id[:30]}")

# Refresh token
data = urllib.parse.urlencode({
    "client_id": client_id,
    "client_secret": client_secret,
    "refresh_token": refresh_token,
    "grant_type": "refresh_token",
}).encode("utf-8")
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    tok = res.get("access_token", "")
    print(f"Fresh token: {tok[:30]}...")

# Check YouTube Data API v3
chk_url = "https://www.googleapis.com/youtube/v3/channels"
params = urllib.parse.urlencode({"part": "snippet,statistics", "mine": "true"})
req2 = urllib.request.Request(f"{chk_url}?{params}", headers={"Authorization": f"Bearer {tok}"})
try:
    with urllib.request.urlopen(req2) as resp2:
        data2 = json.loads(resp2.read().decode())
        item = data2.get("items", [{}])[0]
        stats = item.get("statistics", {})
        print(f"CHANNEL: {item.get('snippet',{}).get('title','?')}")
        print(f"Subscribers: {stats.get('subscriberCount','?')}")
        print(f"Total Views: {stats.get('viewCount','?')}")
        print(f"Video Count: {stats.get('videoCount','?')}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"YT API ERROR {e.code}: {body[:500]}")
