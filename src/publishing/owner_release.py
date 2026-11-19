"""Run a time-limited owner request from Railway variables without exposing a publishing HTTP route."""
import json
import logging
import os
import re
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from src.config import settings
from src.publishing.publishers import InstagramPublisher, YouTubePublisher

log=logging.getLogger("uvicorn.error")

def google(method,params,token,body=None):
    req=Request("https://www.googleapis.com/youtube/v3/videos?"+urlencode(params),
                data=json.dumps(body).encode() if body else None,method=method,
                headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
    with urlopen(req,timeout=25) as response:
        return json.load(response)

def run():
    if settings.emergency_kill_switch or int(os.getenv("VICE_RELEASE_UNTIL","0"))<time.time():
        return
    vid=os.getenv("VICE_RELEASE_VIDEO_ID","")
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}",vid):return
    try:
        ig=InstagramPublisher()
        if not ig.dry_run:
            for item in ig.get_recent_reels(limit=12):
                if item.get("media_type")=="VIDEO" and re.fullmatch(r"https://(?:www\.)?instagram\.com/(?:reel|p)/[\w-]+/?",item.get("permalink","")):
                    log.info("OWNER_RECEIPT Instagram %s %s %s",item.get("id"),item.get("timestamp"),item["permalink"])
    except Exception as exc:
        log.warning("OWNER_RECEIPT Instagram lookup %s",type(exc).__name__)
    try:
        yt=YouTubePublisher()
        token=yt.refresh_access_token_if_needed()
        if not token:return
        def read():return google("GET",{"part":"status,snippet","id":vid},token)["items"][0]
        row=read()
        status=row["status"]
        if status.get("uploadStatus")!="processed":
            log.warning("OWNER_RECEIPT %s processing=%s",vid,status.get("uploadStatus"));return
        title=os.environ["VICE_RELEASE_TITLE"]
        if row["snippet"]["title"] not in {title,os.environ["VICE_RELEASE_EXPECT_TITLE"]}:
            log.warning("OWNER_RECEIPT %s title mismatch",vid);return
        if status["privacyStatus"]!="public" or row["snippet"]["title"]!=title:
            snippet={k:v for k,v in row["snippet"].items() if k in {"categoryId","tags","defaultLanguage","defaultAudioLanguage","localized"} and k!="localized"}
            snippet.update(title=title,description=os.environ["VICE_RELEASE_DESCRIPTION"])
            writable={k:v for k,v in status.items() if k in {"embeddable","license","publicStatsViewable","selfDeclaredMadeForKids","containsSyntheticMedia"}}
            writable["privacyStatus"]="public"
            google("PUT",{"part":"snippet,status"},token,{"id":vid,"snippet":snippet,"status":writable})
        final=read()
        log.info("OWNER_RECEIPT YouTube %s %s %s",vid,final["status"]["privacyStatus"],final["status"]["uploadStatus"])
    except HTTPError as exc:
        try:reason=json.load(exc)["error"]["errors"][0]["reason"]
        except Exception:reason="provider_error"
        log.warning("OWNER_RECEIPT YouTube %s HTTP %s %s",vid,exc.code,reason)
    except Exception as exc:
        log.warning("OWNER_RECEIPT YouTube %s %s",vid,type(exc).__name__)

def start():
    if os.getenv("VICE_RELEASE_VIDEO_ID"):
        threading.Thread(target=run,daemon=True).start()
