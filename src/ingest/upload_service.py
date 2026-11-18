"""
Mode B Upload and Authorized URL Ingestion Service.
Handles local file uploads, checksum validation, URL verification (SSRF prevention),
and media probe before registering assets into storage.
"""
from pathlib import Path
from typing import Dict, Any, Optional
from src.config import settings
from src.core.security import validate_ingest_url
from src.ingest.probe import MediaProbe, MediaProbeError


class UploadService:
    def __init__(self, probe: Optional[MediaProbe] = None):
        self.probe = probe or MediaProbe()

    def process_file_upload(self, file_path: str, creator_key: str, rights_verified: bool = False) -> Dict[str, Any]:
        """
        Validates an uploaded local video file.
        Checks existence, integrity, audio/video streams, duration, and SHA256.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        meta = self.probe.probe(str(path))
        sha256 = self.probe.compute_sha256(str(path))

        # Check duration bounds
        if meta["duration_ms"] < settings.min_clip_duration_ms:
            raise MediaProbeError(
                f"Video duration ({meta['duration_ms']}ms) is below minimum allowed ({settings.min_clip_duration_ms}ms)"
            )

        rights_status = "verified" if rights_verified else "pending"

        return {
            "storage_path": str(path.resolve()),
            "sha256": sha256,
            "duration_ms": meta["duration_ms"],
            "width": meta["width"],
            "height": meta["height"],
            "fps": meta["fps"],
            "video_codec": meta["video_codec"],
            "audio_codec": meta["audio_codec"],
            "has_audio": meta["has_audio"],
            "creator_key": creator_key,
            "rights_status": rights_status,
        }

    def process_authorized_url(self, url: str, creator_key: str, rights_verified: bool = False) -> Dict[str, Any]:
        """
        Validates an authorized URL input.
        Runs SSRF protection check and ensures proper scheme and hostname.
        """
        clean_url = validate_ingest_url(url)
        return {
            "source_url": clean_url,
            "creator_key": creator_key,
            "rights_status": "verified" if rights_verified else "pending",
        }
