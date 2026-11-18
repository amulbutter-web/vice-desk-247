"""
Tests for MediaProbe, RingBuffer, 15-Stream Manager, and SSRF security validation.
"""
import pytest
from datetime import datetime, timezone
from src.ingest.probe import MediaProbe, MediaProbeError
from src.ingest.ring_buffer import RingBuffer
from src.ingest.stream_manager import StreamManager
from src.core.security import validate_ingest_url, SSRFValidationError


def test_media_probe_real_video(sample_video):
    probe = MediaProbe()
    meta = probe.probe(sample_video)
    assert meta["width"] == 1920
    assert meta["height"] == 1080
    assert meta["video_codec"] == "h264"
    assert meta["has_audio"] is True
    assert meta["duration_ms"] >= 14000

    sha = probe.compute_sha256(sample_video)
    assert len(sha) == 64


def test_ring_buffer_discontinuity_detection():
    rb = RingBuffer(source_id="stream-test-01", max_duration_sec=60)
    now = datetime.now(timezone.utc)

    # Segment 1 (0 -> 4000ms)
    s1 = rb.add_segment("s1", 0, 4000, now, now, "/tmp/s1.ts", 1000)
    assert s1.is_discontinuous is False

    # Segment 2 (4000 -> 8000ms, contiguous)
    s2 = rb.add_segment("s2", 4000, 8000, now, now, "/tmp/s2.ts", 1000)
    assert s2.is_discontinuous is False

    # Segment 3 (jump to 12000ms -> 4000ms gap, discontinuous!)
    s3 = rb.add_segment("s3", 12000, 16000, now, now, "/tmp/s3.ts", 1000)
    assert s3.is_discontinuous is True
    assert rb.discontinuity_count == 1


def test_ring_buffer_prunes_physical_files_on_disk(tmp_path):
    rb = RingBuffer(source_id="stream-purge-01", max_duration_sec=10)
    now = datetime.now(timezone.utc)

    # Create dummy segment file on disk
    seg_file = tmp_path / "seg_old.ts"
    seg_file.write_bytes(b"TEST_MPEGTS_PAYLOAD")
    assert seg_file.exists()

    # Add old segment
    rb.add_segment("s1", 0, 5000, now, now, str(seg_file), 100)
    assert seg_file.exists()

    # Add newer segment that exceeds max_duration_sec (10s window: latest 25000 - 10000 = 15000 min allowed)
    seg_file_new = tmp_path / "seg_new.ts"
    seg_file_new.write_bytes(b"NEW_PAYLOAD")
    rb.add_segment("s2", 20000, 25000, now, now, str(seg_file_new), 100)

    # s1 should have been pruned from memory AND physically deleted from disk
    assert len(rb.segments) == 1
    assert not seg_file.exists(), "Old segment file on disk must be unlinked to prevent disk exhaustion!"
    assert seg_file_new.exists()


def test_15_concurrent_stream_manager():
    sm = StreamManager(max_streams=15)
    now = datetime.now(timezone.utc)

    # Register 15 active streams
    for i in range(1, 16):
        sm.register_stream(
            source_id=f"stream-{i:02d}",
            creator_key=f"creator-{i}",
            platform="twitch",
            locator=f"rtmp://feed/{i}",
            priority_weight=2 if i <= 3 else 1,
        )

    # Adding a 16th stream must be rejected
    with pytest.raises(ValueError):
        sm.register_stream(
            source_id="stream-16",
            creator_key="creator-16",
            platform="twitch",
            locator="rtmp://feed/16",
        )

    # Ingest data into all 15 streams
    for s_id in sm.sessions:
        sm.ingest_segment(
            source_id=s_id,
            segment_id=f"seg-{s_id}",
            pts_start_ms=0,
            pts_end_ms=4000,
            utc_start=now,
            utc_end=now,
            storage_path="/tmp/test.ts",
            size_bytes=1024 * 1024,
        )

    health = sm.get_system_health()
    assert health["active_streams_count"] == 15
    assert health["is_degraded"] is False

    schedule = sm.get_fair_scheduled_sources()
    assert len(schedule) == 15


def test_ssrf_url_validation_blocks_private_ips():
    # Loopback
    with pytest.raises(SSRFValidationError):
        validate_ingest_url("http://127.0.0.1/video.mp4")

    # Localhost
    with pytest.raises(SSRFValidationError):
        validate_ingest_url("http://localhost:8080/stream")

    # Cloud metadata endpoint (AWS / GCP / Oracle)
    with pytest.raises(SSRFValidationError):
        validate_ingest_url("http://169.254.169.254/latest/meta-data/")

    # Private LAN
    with pytest.raises(SSRFValidationError):
        validate_ingest_url("http://192.168.1.10/video.mp4")

    # Allowed external URL
    assert validate_ingest_url("https://clips.twitch.tv/my_clip") == "https://clips.twitch.tv/my_clip"
