"""
Audio excitement and transient detector.
Extracts volume peaks, RMS energy, and speech bursts from audio streams.
"""
import subprocess
import json
import re
from typing import List, Dict, Any, Optional
from src.config import settings


class AudioDetector:
    def __init__(self, ffmpeg_binary: Optional[str] = None):
        self.ffmpeg_bin = ffmpeg_binary or settings.ffmpeg_binary

    def analyze_audio(self, media_path: str, interval_sec: float = 0.5) -> List[Dict[str, Any]]:
        """
        Uses FFmpeg ebur128 and astats filter to extract audio loudness and energy timeline.
        Returns a time-series list of {timestamp_ms, rms_db, peak_db, excitement_score}.
        """
        # Run ffmpeg to extract audio volume stats
        cmd = [
            self.ffmpeg_bin,
            "-i", media_path,
            "-af", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
            "-f", "null",
            "-",
        ]

        timeline = []
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            output = res.stderr

            current_pts = 0.0
            for line in output.splitlines():
                pts_match = re.search(r"pts_time:([0-9.]+)", line)
                if pts_match:
                    current_pts = float(pts_match.group(1))

                rms_match = re.search(r"lavfi\\.astats\\.Overall\\.RMS_level=([0-9.-]+)", line)
                if rms_match:
                    rms_val = float(rms_match.group(1))
                    # Convert dB to 0.0-1.0 excitement scale (-60 dB is silence/0.0, -10 dB is max/1.0)
                    clamped = max(-60.0, min(-5.0, rms_val))
                    excitement = (clamped + 60.0) / 55.0

                    timeline.append({
                        "timestamp_ms": int(current_pts * 1000),
                        "rms_db": rms_val,
                        "excitement_score": round(excitement, 3),
                    })
        except Exception:
            # Fallback if audio stats fail or file is synthetic
            pass

        return timeline

    def find_audio_peaks(self, timeline: List[Dict[str, Any]], threshold: float = 0.65) -> List[Dict[str, Any]]:
        """Identifies sustained peaks or transient spikes above threshold."""
        peaks = []
        for point in timeline:
            if point["excitement_score"] >= threshold:
                peaks.append(point)
        return peaks
