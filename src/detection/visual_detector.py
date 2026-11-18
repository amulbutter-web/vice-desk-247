"""
Visual activity and scene cut detector.
Extracts motion intensity, scene cut boundaries, and detects visual freezes or blank frames.
"""
import subprocess
import re
from typing import List, Dict, Any, Optional
from src.config import settings


class VisualDetector:
    def __init__(self, ffmpeg_binary: Optional[str] = None):
        self.ffmpeg_bin = ffmpeg_binary or settings.ffmpeg_binary

    def detect_scene_cuts(self, media_path: str, threshold: float = 0.3) -> List[int]:
        """
        Uses FFmpeg select filter with scene score to detect visual scene transitions.
        Returns a list of cut timestamps in milliseconds.
        """
        cmd = [
            self.ffmpeg_bin,
            "-i", media_path,
            "-filter_complex", f"select='gt(scene,{threshold})',metadata=print:file=-",
            "-f", "null",
            "-",
        ]

        cuts_ms = []
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            for line in res.stdout.splitlines():
                match = re.search(r"pts_time:([0-9.]+)", line)
                if match:
                    pts_sec = float(match.group(1))
                    cuts_ms.append(int(pts_sec * 1000))
        except Exception:
            pass

        return sorted(list(set(cuts_ms)))

    def detect_black_frames(self, media_path: str, min_duration_sec: float = 0.4) -> List[Dict[str, Any]]:
        """
        Uses FFmpeg blackdetect filter to detect blank / black screens.
        """
        cmd = [
            self.ffmpeg_bin,
            "-i", media_path,
            "-vf", f"blackdetect=d={min_duration_sec}:pix_th=0.10",
            "-f", "null",
            "-",
        ]

        black_intervals = []
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            for line in res.stderr.splitlines():
                if "blackdetect" in line:
                    start_match = re.search(r"black_start:([0-9.]+)", line)
                    end_match = re.search(r"black_end:([0-9.]+)", line)
                    dur_match = re.search(r"black_duration:([0-9.]+)", line)
                    if start_match and end_match:
                        black_intervals.append({
                            "start_ms": int(float(start_match.group(1)) * 1000),
                            "end_ms": int(float(end_match.group(1)) * 1000),
                            "duration_ms": int(float(dur_match.group(1)) * 1000) if dur_match else 0,
                        })
        except Exception:
            pass

        return black_intervals

    def detect_freeze_frames(self, media_path: str, min_duration_sec: float = 1.0) -> List[Dict[str, Any]]:
        """
        Uses FFmpeg freezedetect filter to detect static / frozen video screens.
        """
        cmd = [
            self.ffmpeg_bin,
            "-i", media_path,
            "-vf", f"freezedetect=n=0.003:d={min_duration_sec}",
            "-f", "null",
            "-",
        ]

        freezes = []
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            current_start = None
            for line in res.stderr.splitlines():
                if "freeze_start" in line:
                    m = re.search(r"freeze_start: ([0-9.]+)", line)
                    if m:
                        current_start = int(float(m.group(1)) * 1000)
                elif "freeze_end" in line and current_start is not None:
                    m = re.search(r"freeze_end: ([0-9.]+)", line)
                    if m:
                        end_ms = int(float(m.group(1)) * 1000)
                        freezes.append({
                            "start_ms": current_start,
                            "end_ms": end_ms,
                            "duration_ms": end_ms - current_start,
                        })
                        current_start = None
        except Exception:
            pass

        return freezes
