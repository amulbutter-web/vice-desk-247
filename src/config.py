"""
Configuration management for Gaming Content Intelligence Platform.
Implements environment variable loading, strict validation, and defaults.
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Environment & Identity
    app_name: str = "Gaming Content Intelligence Platform"
    environment: str = Field(default="development", description="development, staging, production")
    debug: bool = False
    
    # Storage Paths
    data_dir: Path = BASE_DIR / "data"
    media_dir: Path = BASE_DIR / "data" / "media"
    rendered_dir: Path = BASE_DIR / "data" / "rendered"
    temp_dir: Path = BASE_DIR / "data" / "temp"
    
    # Database
    db_url: str = Field(
        default=f"sqlite:///{BASE_DIR / 'data' / 'platform.db'}",
        validation_alias=AliasChoices("DATABASE_URL", "DB_URL", "db_url"),
        description="Database connection string (SQLite WAL or PostgreSQL)"
    )
    
    # 15-Stream Concurrency Target
    target_concurrent_streams: int = 15
    ring_buffer_duration_sec: int = 120  # 2 minutes rolling buffer
    segment_duration_sec: int = 4        # 4s segment chunks
    max_memory_watermark_mb: int = 4096  # Alert / backpressure threshold
    
    # Editorial & Media Bounds
    canvas_width: int = 1080
    canvas_height: int = 1920
    canvas_fps: float = 60.0
    min_clip_duration_ms: int = 10000   # 10s
    max_clip_duration_ms: int = 90000   # 90s
    default_pre_roll_ms: int = 4000     # 4s approach
    default_post_roll_ms: int = 5000    # 5s resolution
    
    # Safe Zones for 9:16 (avoiding platform UI overlays)
    safe_zone_top_pct: float = 0.15     # Top 15% clear
    safe_zone_bottom_pct: float = 0.20  # Bottom 20% clear (captions, audio title)
    safe_zone_side_pct: float = 0.10    # Side 10% clear (buttons)
    
    # QC Gate Tolerances
    lufs_target_integrated: float = -14.0
    lufs_tolerance: float = 2.0         # Target range: [-16.0, -12.0]
    max_true_peak_dbtp: float = -1.0
    max_black_frame_duration_ms: int = 1500
    max_freeze_duration_ms: int = 6000
    max_repair_revisions: int = 2
    
    # Rights & Publishing
    emergency_kill_switch: bool = False
    publish_draft_only: bool = True     # Never post public by default; private/draft
    max_publish_retries: int = 5
    outbox_lease_timeout_sec: int = 60
    
    # External Tools
    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"

    # Publishing & Credentials
    instagram_access_token: Optional[str] = None
    instagram_account_id: Optional[str] = "17841467596649798"
    instagram_username: Optional[str] = "hritiksingh_8"
    meta_app_id: Optional[str] = None
    meta_app_secret: Optional[str] = None
    meta_client_token: Optional[str] = None

    youtube_access_token: Optional[str] = None
    youtube_refresh_token: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    groq_api_keys: Optional[str] = None
    extra_groq_scout_key_1: Optional[str] = None
    extra_groq_scout_key_2: Optional[str] = None

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
for path in [settings.data_dir, settings.media_dir, settings.rendered_dir, settings.temp_dir]:
    path.mkdir(parents=True, exist_ok=True)
