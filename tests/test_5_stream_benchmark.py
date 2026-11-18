"""
Test suite for PRD V4 5-Stream Concurrency Benchmark.
"""
from datetime import datetime, timezone
from src.ingest.stream_manager import StreamManager


def test_5_stream_concurrency_and_priority_scheduling():
    sm = StreamManager(max_streams=5)
    
    stream_configs = [
        {"id": "speed_live_01", "creator": "iShowSpeed", "platform": "youtube", "weight": 2},
        {"id": "kai_cenat_02", "creator": "KaiCenat", "platform": "twitch", "weight": 2},
        {"id": "tarik_val_03", "creator": "tarik", "platform": "twitch", "weight": 1},
        {"id": "gta6_feed_04", "creator": "ViceCityLive", "platform": "kick", "weight": 1},
        {"id": "shroud_fps_05", "creator": "shroud", "platform": "twitch", "weight": 1},
    ]

    for cfg in stream_configs:
        sm.register_stream(
            source_id=cfg["id"],
            creator_key=cfg["creator"],
            platform=cfg["platform"],
            locator=f"https://{cfg['platform']}.tv/{cfg['creator']}",
            priority_weight=cfg["weight"],
        )

    assert len(sm.sessions) == 5

    now = datetime.now(timezone.utc)
    for s_id in sm.sessions:
        sm.ingest_segment(
            source_id=s_id,
            segment_id=f"seg-{s_id}-001",
            pts_start_ms=0,
            pts_end_ms=4000,
            utc_start=now,
            utc_end=now,
            storage_path="/tmp/test.ts",
            size_bytes=2 * 1024 * 1024,
        )

    health = sm.get_system_health()
    assert health["active_streams_count"] == 5
    assert health["is_degraded"] is False

    schedule = sm.get_fair_scheduled_sources()
    assert len(schedule) == 5
    assert schedule[0] in ("speed_live_01", "kai_cenat_02")
