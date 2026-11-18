"""
FFprobe wrapper and media inspector.
Safely extracts stream metadata, codec details, audio channels, and checks media integrity.
"""
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from src.config import settings


class MediaProbeError(Exception):
    pass


class MediaProbe:
    def __init__(self, ffprobe_binary: Optional[str] = None):
        self.ffprobe_bin = ffprobe_binary or settings.ffprobe_binary

    def probe(self, file_path: str) -> Dict[str, Any]:
        """Runs ffprobe on a file and returns parsed stream metadata."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Media file does not exist: {file_path}")

        cmd = [
            self.ffprobe_bin,
            "-v", "error",
            "-show_format",
            "-show_streams",
            "-print_format", "json",
            str(path.resolve()),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            data = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise MediaProbeError(f"ffprobe failed with code {e.returncode}: {e.stderr}")
        except json.JSONDecodeError as e:
            raise MediaProbeError(f"Failed to parse ffprobe JSON output: {e}")
        except Exception as e:
            raise MediaProbeError(f"Unexpected error running ffprobe: {e}")

        streams = data.get("streams", [])
        fmt = data.get("format", {})

        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

        if not video_streams:
            raise MediaProbeError("Media contains no video stream")

        v_stream = video_streams[0]
        # Parse framerate (e.g. "60/1" or "30000/1001")
        fps_str = v_stream.get("r_frame_rate", "30/1")
        fps = 30.0
        try:
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) > 0 else 30.0
        except Exception:
            fps = 30.0

        duration_sec = float(fmt.get("duration", v_stream.get("duration", 0.0)))
        duration_ms = int(duration_sec * 1000)

        return {
            "duration_ms": duration_ms,
            "duration_sec": duration_sec,
            "width": int(v_stream.get("width", 0)),
            "height": int(v_stream.get("height", 0)),
            "fps": fps,
            "video_codec": v_stream.get("codec_name"),
            "audio_codec": audio_streams[0].get("codec_name") if audio_streams else None,
            "audio_channels": int(audio_streams[0].get("channels", 0)) if audio_streams else 0,
            "audio_sample_rate": int(audio_streams[0].get("sample_rate", 0)) if audio_streams else 0,
            "size_bytes": int(fmt.get("size", path.stat().st_size)),
            "bitrate": int(fmt.get("bit_rate", 0)),
            "has_audio": len(audio_streams) > 0,
        }

    @staticmethod
    def compute_sha256(file_path: str) -> str:
        """Computes SHA-256 hash of media file in streaming chunks."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(1024 * 1024):
                hasher.update(chunk)
        return hasher.hexdigest()
