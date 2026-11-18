"""
Narrative Boundary Engine.
Expands raw peak timestamps into complete storytelling events:
onset -> buildup -> peak -> resolution.
Snaps boundaries to natural scene cuts or speech pauses to avoid mid-word truncation.
"""
from typing import List, Dict, Any, Optional
from src.config import settings


class NarrativeBoundaryEngine:
    def __init__(
        self,
        default_pre_roll_ms: int = 15000,
        default_post_roll_ms: int = 18000,
        min_duration_ms: int = 30000,
        max_duration_ms: int = 50000,
    ):
        self.default_pre_roll_ms = default_pre_roll_ms
        self.default_post_roll_ms = default_post_roll_ms
        self.min_duration_ms = min_duration_ms
        self.max_duration_ms = max_duration_ms

    def expand_event_boundaries(
        self,
        peak_ms: int,
        source_duration_ms: int,
        scene_cuts_ms: Optional[List[int]] = None,
        speech_pauses_ms: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates onset, buildup, peak, resolution, and total window bounds.
        Snaps start and end to nearest natural scene cuts or speech pauses where possible.
        """
        scene_cuts = scene_cuts_ms or []
        pauses = speech_pauses_ms or []
        natural_boundaries = sorted(list(set(scene_cuts + pauses)))

        raw_start = max(0, peak_ms - self.default_pre_roll_ms)
        raw_end = min(source_duration_ms, peak_ms + self.default_post_roll_ms)

        # Snap start to nearest prior natural boundary within 2000ms
        snapped_start = raw_start
        candidates_start = [b for b in natural_boundaries if raw_start - 2000 <= b <= raw_start + 1000 and b < peak_ms]
        if candidates_start:
            snapped_start = max(0, candidates_start[-1])

        # Snap end to nearest subsequent natural boundary within 2500ms
        snapped_end = raw_end
        candidates_end = [b for b in natural_boundaries if raw_end - 1000 <= b <= raw_end + 2500 and b > peak_ms]
        if candidates_end:
            snapped_end = min(source_duration_ms, candidates_end[0])

        duration = snapped_end - snapped_start

        # Enforce minimum duration
        if (snapped_end - snapped_start) < self.min_duration_ms:
            needed = self.min_duration_ms - (snapped_end - snapped_start)
            can_expand_start = min(snapped_start, needed // 2)
            snapped_start -= can_expand_start
            remaining_needed = needed - can_expand_start
            snapped_end = min(source_duration_ms, snapped_end + remaining_needed)
            if (snapped_end - snapped_start) < self.min_duration_ms:
                snapped_start = max(0, snapped_end - self.min_duration_ms)

        # Enforce maximum duration
        if (snapped_end - snapped_start) > self.max_duration_ms:
            snapped_end = snapped_start + self.max_duration_ms

        onset_ms = snapped_start
        buildup_ms = onset_ms + int((peak_ms - onset_ms) * 0.5)
        resolution_ms = min(source_duration_ms, peak_ms + int((snapped_end - peak_ms) * 0.7))

        return {
            "window_start_ms": snapped_start,
            "window_end_ms": snapped_end,
            "duration_ms": snapped_end - snapped_start,
            "narrative_stages": {
                "onset_ms": onset_ms,
                "buildup_ms": buildup_ms,
                "peak_ms": peak_ms,
                "resolution_ms": resolution_ms,
            },
            "snapped_to_natural_boundary": (snapped_start != raw_start or snapped_end != raw_end),
        }
