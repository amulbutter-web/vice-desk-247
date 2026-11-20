"""
FFmpeg Rendering Engine.
Executes media composition jobs, monitors rendering progress,
enforces timeouts, and validates the output file.
"""
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from src.config import settings
from src.core.contracts import EditPlan
from src.editor.filtergraph import FiltergraphGenerator
from src.ingest.probe import MediaProbe, MediaProbeError


class RenderError(Exception):
    pass


# Global rendering semaphore: allows exactly 1 FFmpeg render process across all threads
# Prevents cloud container Out-Of-Memory (OOM) SIGKILL (exit code -9)
_RENDER_GLOBAL_SEMAPHORE = threading.Semaphore(1)


class VideoRenderer:
    def __init__(self, probe: Optional[MediaProbe] = None, ffmpeg_bin: Optional[str] = None):
        self.probe = probe or MediaProbe()
        self.ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_binary

    def render_clip(
        self,
        source_path: str,
        output_path: str,
        edit_plan: EditPlan,
        subtitle_filters: Optional[List[str]] = None,
        ass_subtitle_path: Optional[str] = None,
        timeout_sec: int = 360,
    ) -> Dict[str, Any]:
        """
        Executes FFmpeg rendering of the specified EditPlan.
        Returns rendered media metadata including sha256.
        """
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = FiltergraphGenerator.build_render_command(
            source_path=source_path,
            output_path=str(out_file.resolve()),
            edit_plan=edit_plan,
            ffmpeg_bin=self.ffmpeg_bin,
            subtitle_filters=subtitle_filters,
            ass_subtitle_path=ass_subtitle_path,
        )

        try:
            with _RENDER_GLOBAL_SEMAPHORE:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
            if res.returncode != 0:
                raise RenderError(f"FFmpeg failed with exit code {res.returncode}: {res.stderr}")
        except subprocess.TimeoutExpired:
            raise RenderError(f"Rendering timed out after {timeout_sec} seconds")
        except Exception as e:
            raise RenderError(f"Rendering execution failed: {e}")

        if not out_file.exists() or out_file.stat().st_size == 0:
            raise RenderError("Render output file was not created or is empty")

        # Probe output media to verify dimensions, duration, and codecs
        probe_meta = self.probe.probe(str(out_file))
        sha256 = self.probe.compute_sha256(str(out_file))

        return {
            "output_path": str(out_file.resolve()),
            "sha256": sha256,
            "width": probe_meta["width"],
            "height": probe_meta["height"],
            "fps": probe_meta["fps"],
            "duration_ms": probe_meta["duration_ms"],
            "size_bytes": probe_meta["size_bytes"],
            "video_codec": probe_meta["video_codec"],
            "audio_codec": probe_meta["audio_codec"],
            "has_audio": probe_meta["has_audio"],
        }
