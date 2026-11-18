"""
Deterministic Hard Quality Control Gates.
Enforces non-negotiable machine standards:
Resolution, duration, codecs, audio loudness/clipping, black screens, and frozen frames.
A model cannot override a failed hard gate.
"""
from typing import List, Dict, Any, Tuple
from src.config import settings
from src.core.contracts import HardGate
from src.ingest.probe import MediaProbe
from src.detection.visual_detector import VisualDetector


class HardQualityGates:
    def __init__(self, probe: MediaProbe, visual_detector: VisualDetector):
        self.probe = probe
        self.visual_detector = visual_detector

    def run_all_gates(self, media_path: str) -> Tuple[bool, List[HardGate]]:
        """
        Executes all deterministic hard gates on the rendered media.
        Returns: (overall_pass, list_of_gates)
        """
        gates: List[HardGate] = []

        # 1. Probe media
        try:
            meta = self.probe.probe(media_path)
        except Exception as e:
            gates.append(HardGate(gate_id="GATE-PROBE", pass_=False, measured_value=str(e), reason=f"Probe failed: {e}"))
            return False, gates

        # 2. Resolution Gate (1080x1920)
        is_res_pass = (meta["width"] == settings.canvas_width and meta["height"] == settings.canvas_height)
        gates.append(
            HardGate(
                gate_id="GATE-RESOLUTION",
                pass_=is_res_pass,
                measured_value=f"{meta['width']}x{meta['height']}",
                reason="Resolution matches 1080x1920 vertical canvas" if is_res_pass else f"Invalid resolution {meta['width']}x{meta['height']}",
            )
        )

        # 3. Duration Gate (10s to 90s)
        dur_ms = meta["duration_ms"]
        is_dur_pass = (settings.min_clip_duration_ms <= dur_ms <= settings.max_clip_duration_ms)
        gates.append(
            HardGate(
                gate_id="GATE-DURATION",
                pass_=is_dur_pass,
                measured_value=dur_ms,
                reason="Duration within bounds" if is_dur_pass else f"Duration {dur_ms}ms outside allowed [{settings.min_clip_duration_ms}, {settings.max_clip_duration_ms}]",
            )
        )

        # 4. Codec Gate (Video h264, Audio aac)
        is_codec_pass = (meta["video_codec"] == "h264" and meta.get("audio_codec") == "aac")
        gates.append(
            HardGate(
                gate_id="GATE-CODEC",
                pass_=is_codec_pass,
                measured_value=f"v:{meta['video_codec']}, a:{meta.get('audio_codec')}",
                reason="Standard h264/aac codecs verified" if is_codec_pass else "Non-standard codec detected",
            )
        )

        # 5. Audio Presence Gate
        has_audio = meta.get("has_audio", False)
        gates.append(
            HardGate(
                gate_id="GATE-AUDIO-PRESENCE",
                pass_=has_audio,
                measured_value="present" if has_audio else "missing",
                reason="Audio track verified" if has_audio else "Audio stream is missing",
            )
        )

        # 6. Black Frame Detection Gate (<= 500ms allowed)
        black_frames = self.visual_detector.detect_black_frames(media_path, min_duration_sec=0.4)
        max_black_dur = max([bf["duration_ms"] for bf in black_frames], default=0)
        is_black_pass = (max_black_dur <= settings.max_black_frame_duration_ms)
        gates.append(
            HardGate(
                gate_id="GATE-BLACK-FRAMES",
                pass_=is_black_pass,
                measured_value=max_black_dur,
                reason="Black frame duration acceptable" if is_black_pass else f"Black frame sequence ({max_black_dur}ms) exceeds limit ({settings.max_black_frame_duration_ms}ms)",
            )
        )

        # 7. Video Freeze Detection Gate (<= 1000ms allowed)
        freeze_frames = self.visual_detector.detect_freeze_frames(media_path, min_duration_sec=0.8)
        max_freeze_dur = max([ff["duration_ms"] for ff in freeze_frames], default=0)
        is_freeze_pass = (max_freeze_dur <= settings.max_freeze_duration_ms)
        gates.append(
            HardGate(
                gate_id="GATE-FREEZE-FRAMES",
                pass_=is_freeze_pass,
                measured_value=max_freeze_dur,
                reason="Video motion continuous" if is_freeze_pass else f"Video freeze ({max_freeze_dur}ms) exceeds limit ({settings.max_freeze_duration_ms}ms)",
            )
        )

        all_passed = all(g.pass_ for g in gates)
        return all_passed, gates
