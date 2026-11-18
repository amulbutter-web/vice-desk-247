"""
Pytest fixtures and synthetic test media generators.
Generates lightweight, real playable MP4 files using FFmpeg to test real encoding,
probing, black frame detection, freeze detection, and vertical rendering.
"""
import os
import sys
import subprocess
import pytest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import settings
from src.db.database import Base, engine, SessionLocal
from src.db.models import utc_now


@pytest.fixture(scope="session")
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_test_db):
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="session")
def fixtures_dir(tmp_path_factory) -> Path:
    fdir = tmp_path_factory.mktemp("test_media_fixtures")
    return fdir


@pytest.fixture(scope="session")
def sample_video(fixtures_dir) -> str:
    """
    Generates a synthetic 15-second 1920x1080 30fps test video with audio tone.
    """
    out_path = fixtures_dir / "sample_gameplay_1080p.mp4"
    if out_path.exists():
        return str(out_path)

    cmd = [
        settings.ffmpeg_binary,
        "-y",
        "-f", "lavfi",
        "-i", "testsrc=size=1920x1080:rate=30",
        "-f", "lavfi",
        "-i", "sine=frequency=440:sample_rate=48000",
        "-t", "15",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        str(out_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return str(out_path)


@pytest.fixture(scope="session")
def black_screen_video(fixtures_dir) -> str:
    """
    Generates a 12-second test video containing 2 seconds of pure black frames.
    """
    out_path = fixtures_dir / "black_screen_test.mp4"
    if out_path.exists():
        return str(out_path)

    cmd = [
        settings.ffmpeg_binary,
        "-y",
        "-f", "lavfi",
        "-i", "color=c=black:size=1920x1080:rate=30",
        "-f", "lavfi",
        "-i", "sine=frequency=220:sample_rate=48000",
        "-t", "12",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        str(out_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return str(out_path)


@pytest.fixture(scope="session")
def silent_video(fixtures_dir) -> str:
    """
    Generates a 10-second test video with NO audio stream.
    """
    out_path = fixtures_dir / "silent_no_audio.mp4"
    if out_path.exists():
        return str(out_path)

    cmd = [
        settings.ffmpeg_binary,
        "-y",
        "-f", "lavfi",
        "-i", "testsrc=size=1920x1080:rate=30",
        "-t", "10",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-an",
        str(out_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return str(out_path)
