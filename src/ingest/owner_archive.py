"""Read an operator-provisioned original from an exact video-ID archive on the worker."""
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
import os
import re
import subprocess
import uuid


def archive_excerpt(url, section_start, seconds, output_dir, ffmpeg):
    root=os.getenv("VICE_ORIGINALS_DIR","")
    if not root:
        return None
    parsed=urlsplit(url)
    if parsed.hostname not in {"www.youtube.com","youtube.com"} or parsed.path!="/watch":
        return None
    video_id=parse_qs(parsed.query).get("v",[""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}",video_id):
        return None
    root=Path(root).resolve()
    source=(root/(video_id+".mp4")).resolve()
    if source.parent!=root or not source.is_file():
        return None
    target=Path(output_dir)/("original_"+uuid.uuid4().hex+".mp4")
    try:
        subprocess.run([ffmpeg,"-nostdin","-v","error","-ss",section_start,"-protocol_whitelist","file",
                        "-format_whitelist","mov","-i",str(source),"-t",str(seconds),"-map","0:v:0","-map","0:a:0?",
                        "-c:v","libx264","-preset","veryfast","-c:a","aac",str(target)],check=True,timeout=240,capture_output=True)
        if target.stat().st_size<1024:raise ValueError("Requested interval has no source footage")
        return target
    except BaseException:
        target.unlink(missing_ok=True)
        raise
