"""
Tests for LiveIngestWorker and End-to-End URL Ingestion with Vice Desk API.
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from src.server.app import app
from src.ingest.live_worker import LiveIngestWorker


def test_live_ingest_worker_e2e(sample_video, tmp_path):
    worker = LiveIngestWorker()
    
    # Process local sample stream
    res = worker.process_url_job(
        url=sample_video,
        creator_name="iShowSpeed",
        game="GTA 6",
        layout_mode="split_cam_game",
    )

    assert res["status"] == "COMPLETED"
    assert res["creator"] == "iShowSpeed"
    assert res["qc_passed"] is True
    assert Path(res["output_path"]).exists()
    assert Path(res["output_path"]).stat().st_size > 1000
    assert res["resolution"] == "1080x1920"


def test_api_ingest_url_sync_and_ready_clips(sample_video):
    client = TestClient(app)

    # 1. Trigger ingest synchronously
    resp = client.post(
        "/api/ingest/url?sync=true",
        json={
            "url": sample_video,
            "creator_name": "iShowSpeed",
            "game": "GTA 6",
            "priority": 100,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert data["creator"] == "iShowSpeed"
    assert data["resolution"] == "1080x1920"
    assert data["qc_passed"] is True

    # 2. Verify clip appears in GET /api/clips/ready
    ready_resp = client.get("/api/clips/ready")
    assert ready_resp.status_code == 200
    ready_data = ready_resp.json()
    assert ready_data["count"] > 0
    assert any(c["filename"] == f"{data['render_id']}.mp4" for c in ready_data["clips"])


def test_api_ingest_url_async_dispatch():
    client = TestClient(app)

    # Trigger background async ingest with YouTube stream URL
    resp = client.post(
        "/api/ingest/url",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "creator_name": "iShowSpeed",
            "game": "GTA 6",
            "priority": 100,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "INGEST_QUEUED"
    assert data["creator"] == "iShowSpeed"
    assert "source_id" in data
