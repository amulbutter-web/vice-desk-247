"""Read an operator-provisioned original from an exact video-ID archive on the worker."""
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
import json
import logging
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import os
import re
import subprocess
import uuid


def archive_excerpt(url, section_start, seconds, output_dir, ffmpeg):
    root=os.getenv("VICE_ORIGINALS_DIR","")
    parsed=urlsplit(url)
    if parsed.hostname not in {"www.youtube.com","youtube.com"} or parsed.path!="/watch":
        return None
    video_id=parse_qs(parsed.query).get("v",[""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}",video_id):
        return None
    source = None
    protocols = "file"
    if root:
        root = Path(root).resolve()
        candidate = (root / (video_id + ".mp4")).resolve()
        if candidate.parent == root and candidate.is_file():
            source = candidate
    if source is None:
        endpoint = os.getenv("VICE_ARCHIVE_ENDPOINT")
        key = os.getenv("VICE_ARCHIVE_READ_KEY")
        if not endpoint or not key:
            return None
        try:
            req = Request(endpoint + "?id=" + video_id, headers={"Authorization": "Bearer " + key})
            with urlopen(req, timeout=10) as response:
                signed = json.load(response)["url"]
            if urlsplit(signed).scheme != "https" or urlsplit(signed).netloc != urlsplit(endpoint).netloc:
                return None
            source = signed
            protocols = "https,tls,tcp"
        except (HTTPError, URLError, TimeoutError, KeyError, ValueError) as exc:
            if getattr(exc, "code", None) != 404:
                logging.getLogger(__name__).warning("Archive lookup unavailable (%s)", type(exc).__name__)
            return None
    target=Path(output_dir)/("original_"+uuid.uuid4().hex+".mp4")
    try:
        subprocess.run([ffmpeg,"-nostdin","-v","error","-ss",section_start,"-protocol_whitelist",protocols,
                        "-format_whitelist","mov","-i",str(source),"-t",str(seconds),"-map","0:v:0","-map","0:a:0?",
                        "-c:v","libx264","-preset","veryfast","-c:a","aac",str(target)],check=True,timeout=240,capture_output=True)
        if target.stat().st_size<1024:raise ValueError("Requested interval has no source footage")
        return target
    except subprocess.CalledProcessError:
        target.unlink(missing_ok=True)
        raise ValueError("Could not decode archived interval") from None
    except BaseException:
        target.unlink(missing_ok=True)
        raise
