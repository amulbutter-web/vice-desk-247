"""
Rolling Ring Buffer for live streams.
Maintains timestamped segments, maps source PTS to UTC wall-clock,
and detects stream discontinuities and clock drifts.
"""
import os
import collections
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class SegmentMetadata:
    segment_id: str
    source_id: str
    pts_start_ms: int
    pts_end_ms: int
    utc_start: datetime
    utc_end: datetime
    storage_path: str
    size_bytes: int
    is_discontinuous: bool = False
    drift_ms: int = 0


class RingBuffer:
    def __init__(self, source_id: str, max_duration_sec: int = 120):
        self.source_id = source_id
        self.max_duration_sec = max_duration_sec
        self.segments: collections.deque[SegmentMetadata] = collections.deque()
        self.last_pts_end_ms: Optional[int] = None
        self.discontinuity_count: int = 0

    def add_segment(
        self,
        segment_id: str,
        pts_start_ms: int,
        pts_end_ms: int,
        utc_start: datetime,
        utc_end: datetime,
        storage_path: str,
        size_bytes: int,
    ) -> SegmentMetadata:
        """Adds a new segment, detecting PTS jumps, gaps, and discontinuities."""
        is_discontinuous = False
        drift_ms = 0

        if self.last_pts_end_ms is not None:
            gap = pts_start_ms - self.last_pts_end_ms
            # If gap is negative (PTS reset) or > 500ms (packet loss/disconnect)
            if gap < -50 or gap > 500:
                is_discontinuous = True
                self.discontinuity_count += 1
                drift_ms = gap

        segment = SegmentMetadata(
            segment_id=segment_id,
            source_id=self.source_id,
            pts_start_ms=pts_start_ms,
            pts_end_ms=pts_end_ms,
            utc_start=utc_start,
            utc_end=utc_end,
            storage_path=storage_path,
            size_bytes=size_bytes,
            is_discontinuous=is_discontinuous,
            drift_ms=drift_ms,
        )

        self.segments.append(segment)
        self.last_pts_end_ms = pts_end_ms

        # Prune old segments beyond max_duration_sec
        self._prune()
        return segment

    def _prune(self):
        if not self.segments:
            return
        latest_pts = self.segments[-1].pts_end_ms
        min_allowed_pts = latest_pts - (self.max_duration_sec * 1000)

        while self.segments and self.segments[0].pts_end_ms < min_allowed_pts:
            old_seg = self.segments.popleft()
            # Physical disk reclamation to prevent storage exhaustion under 24/7 stream recording
            if old_seg.storage_path and os.path.isfile(old_seg.storage_path):
                try:
                    os.remove(old_seg.storage_path)
                except OSError:
                    pass

    def get_window(self, start_ms: int, end_ms: int, pre_roll_ms: int = 4000, post_roll_ms: int = 5000) -> Tuple[List[SegmentMetadata], bool]:
        """
        Retrieves all segments covering the requested event window including pre-roll and post-roll.
        Returns (segments, contains_discontinuity).
        """
        target_start = max(0, start_ms - pre_roll_ms)
        target_end = end_ms + post_roll_ms

        selected = []
        has_discontinuity = False

        for seg in self.segments:
            # Overlaps with target window
            if seg.pts_end_ms >= target_start and seg.pts_start_ms <= target_end:
                selected.append(seg)
                if seg.is_discontinuous:
                    has_discontinuity = True

        return selected, has_discontinuity

    def total_buffered_duration_sec(self) -> float:
        if not self.segments:
            return 0.0
        return (self.segments[-1].pts_end_ms - self.segments[0].pts_start_ms) / 1000.0
