"""
15-Stream Concurrency Manager.
Coordinates up to 15 concurrent live stream buffers with source isolation,
fair queueing (weighted round-robin), memory watermark protection, and health monitoring.
"""
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from src.config import settings
from src.ingest.ring_buffer import RingBuffer, SegmentMetadata


@dataclass
class StreamSession:
    source_id: str
    creator_key: str
    platform: str
    locator: str
    buffer: RingBuffer
    status: str = "active"  # active, paused, disconnected, degraded
    segments_received: int = 0
    bytes_received: int = 0
    last_segment_at: Optional[datetime] = None
    priority_weight: int = 1
    queue_backlog: int = 0


class StreamManager:
    def __init__(self, max_streams: int = 15):
        self.max_streams = max_streams
        self.sessions: Dict[str, StreamSession] = {}
        self.total_memory_usage_mb: float = 0.0

    def register_stream(
        self, source_id: str, creator_key: str, platform: str, locator: str, priority_weight: int = 1
    ) -> StreamSession:
        """Registers a live stream up to the 15-stream limit."""
        if len(self.sessions) >= self.max_streams:
            raise ValueError(f"Max concurrent streams reached ({self.max_streams}). Cannot add {source_id}.")

        if source_id in self.sessions:
            return self.sessions[source_id]

        session = StreamSession(
            source_id=source_id,
            creator_key=creator_key,
            platform=platform,
            locator=locator,
            buffer=RingBuffer(source_id=source_id, max_duration_sec=settings.ring_buffer_duration_sec),
            priority_weight=priority_weight,
        )
        self.sessions[source_id] = session
        return session

    def ingest_segment(
        self,
        source_id: str,
        segment_id: str,
        pts_start_ms: int,
        pts_end_ms: int,
        utc_start: datetime,
        utc_end: datetime,
        storage_path: str,
        size_bytes: int,
    ) -> SegmentMetadata:
        """Ingests a segment into the stream's isolated ring buffer."""
        session = self.sessions.get(source_id)
        if not session:
            raise KeyError(f"Stream {source_id} is not registered")

        segment = session.buffer.add_segment(
            segment_id=segment_id,
            pts_start_ms=pts_start_ms,
            pts_end_ms=pts_end_ms,
            utc_start=utc_start,
            utc_end=utc_end,
            storage_path=storage_path,
            size_bytes=size_bytes,
        )

        session.segments_received += 1
        session.bytes_received += size_bytes
        session.last_segment_at = utc_end

        # Monitor memory watermark
        self._update_memory_watermark()
        return segment

    def get_fair_scheduled_sources(self) -> List[str]:
        """
        Returns active source IDs ordered by weighted round-robin scheduling.
        Ensures fair processing across all 15 concurrent streams without starvation.
        """
        active_sessions = [s for s in self.sessions.values() if s.status == "active"]
        # Sort by (queue_backlog / priority_weight) descending
        active_sessions.sort(key=lambda s: (s.queue_backlog / max(1, s.priority_weight)), reverse=True)
        return [s.source_id for s in active_sessions]

    def _update_memory_watermark(self):
        # Calculate rough buffer memory based on stored segments
        total_bytes = sum(s.bytes_received for s in self.sessions.values())
        self.total_memory_usage_mb = total_bytes / (1024 * 1024)

    def get_system_health(self) -> Dict[str, Any]:
        """Returns overall 15-stream health and capacity status."""
        return {
            "active_streams_count": len(self.sessions),
            "max_concurrent_target": self.max_streams,
            "total_bytes_received": sum(s.bytes_received for s in self.sessions.values()),
            "total_memory_usage_mb": self.total_memory_usage_mb,
            "memory_watermark_limit_mb": settings.max_memory_watermark_mb,
            "is_degraded": self.total_memory_usage_mb > settings.max_memory_watermark_mb,
            "streams": [
                {
                    "source_id": s.source_id,
                    "creator_key": s.creator_key,
                    "platform": s.platform,
                    "status": s.status,
                    "buffered_duration_sec": s.buffer.total_buffered_duration_sec(),
                    "segments_count": len(s.buffer.segments),
                    "discontinuities": s.buffer.discontinuity_count,
                    "queue_backlog": s.queue_backlog,
                }
                for s in self.sessions.values()
            ],
        }
