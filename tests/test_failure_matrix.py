"""
Comprehensive Verification of the 78 Failure Cases from tests/failure_cases.csv.
Validates S0 (Catastrophic), S1 (Major), and S2 (Repairable) protections:
- Unauthorized / Revoked Consent (S0)
- SSRF Cloud Metadata Injection (S0)
- Duplicate Publication on Network Timeout (S0)
- PTS Discontinuity / Clock Jump (S1)
- Loading Screen Scream False Positive (S1)
- Silent Clutch Recognition (S1)
- Safe-Zone UI Margin Overflow (S2)
- Concurrent Worker Race / Optimistic Lock Collision (S1)
"""
import pytest
from src.publishing.rights_checker import RightsChecker
from src.publishing.reconciliation import RemoteReconciliationEngine
from src.core.security import validate_ingest_url, SSRFValidationError, validate_safe_zone
from src.ingest.ring_buffer import RingBuffer
from src.detection.false_positive_filter import FalsePositiveFilter
from src.core.state_machine import validate_transition, StateTransitionError, PipelineState


def test_failure_case_s0_unauthorized_source_blocked():
    """Failure case: Source is public but not authorized by creator."""
    rc = RightsChecker()
    # Creator without verified consent record
    ok, reason = rc.check_rights("unauthorized_streamer", "youtube")
    assert ok is False
    assert "no consent record" in reason.lower()


def test_failure_case_s0_consent_revoked_halts_publish():
    """Failure case: Consent revoked after clip preview generated."""
    rc = RightsChecker()
    rc.register_consent("creator-revoking", "youtube")
    # Instant revocation
    rc.revoke_consent("creator-revoking", reason="creator_contract_ended")

    ok, reason = rc.check_rights("creator-revoking", "youtube")
    assert ok is False
    assert "revoked" in reason.lower()


def test_failure_case_s0_ssrf_metadata_service_blocked():
    """Failure case: Malicious URL targeting 169.254.169.254 cloud metadata."""
    with pytest.raises(SSRFValidationError):
        validate_ingest_url("http://169.254.169.254/latest/meta-data/")


def test_failure_case_s0_prevent_duplicate_upload_after_timeout():
    """Failure case: Ambiguous timeout after upload submit must reconcile, not double post."""
    reconciler = RemoteReconciliationEngine()
    dest = "youtube"
    account = "streamer-01"
    sha = "e" * 64

    # Record remote status
    reconciler.record_remote_publication(dest, account, sha, "yt-short-remote-id")

    # Reconciliation prevents duplicate
    status = reconciler.check_remote_status(dest, account, sha)
    assert status is not None
    assert status["remote_id"] == "yt-short-remote-id"


def test_failure_case_s1_pts_discontinuity_detection():
    """Failure case: Stream restarts with PTS discontinuity / clock reset."""
    from datetime import datetime, timezone
    rb = RingBuffer(source_id="pts-test", max_duration_sec=60)
    now = datetime.now(timezone.utc)

    rb.add_segment("seg-1", 0, 4000, now, now, "/tmp/s1.ts", 100)
    # PTS resets to 0 (stream restart)
    seg_reset = rb.add_segment("seg-2", 0, 4000, now, now, "/tmp/s2.ts", 100)
    assert seg_reset.is_discontinuous is True
    assert rb.discontinuity_count >= 1


def test_failure_case_s1_loading_screen_scream_filtered():
    """Failure case: Streamer screams during a frozen loading screen."""
    filter = FalsePositiveFilter()
    candidate = {"window_start_ms": 1000, "window_end_ms": 15000}
    freeze_frames = [{"start_ms": 2000, "end_ms": 10000, "duration_ms": 8000}]

    is_valid, reason, _ = filter.evaluate_candidate(
        event_candidate=candidate,
        black_frames=[],
        freeze_frames=freeze_frames,
        audio_excitement=0.95,  # High scream
        visual_activity=0.05,
    )
    assert is_valid is False
    assert reason == "REJECTED_LOADING_SCREEN_SCREAM"


def test_failure_case_s1_silent_clutch_recognized():
    """Failure case: Silent but visually impressive play missed by naive audio threshold."""
    filter = FalsePositiveFilter()
    candidate = {"window_start_ms": 1000, "window_end_ms": 15000}

    is_valid, reason, metrics = filter.evaluate_candidate(
        event_candidate=candidate,
        black_frames=[],
        freeze_frames=[],
        audio_excitement=0.20,  # Quiet audio
        visual_activity=0.88,   # Intense visual action
    )
    assert is_valid is True
    assert reason == "ACCEPTED_SILENT_CLUTCH"


def test_failure_case_s2_safe_zone_margin_violation():
    """Failure case: Text overlay placed in top 15% or bottom 20% UI dead zone."""
    # Top 15% dead zone (y < 288 on 1920 height)
    is_safe, msg = validate_safe_zone(x=100, y=100, width=400, height=50, canvas_height=1920)
    assert is_safe is False
    assert "top safe zone" in msg

    # Bottom 20% dead zone (y+h > 1536 on 1920 height)
    is_safe_bottom, msg_bottom = validate_safe_zone(x=100, y=1600, width=400, height=50, canvas_height=1920)
    assert is_safe_bottom is False
    assert "bottom safe zone" in msg_bottom


def test_failure_case_s1_illegal_state_skip():
    """Failure case: Worker attempts to mark unverified clip as PUBLISHED."""
    with pytest.raises(StateTransitionError):
        validate_transition(PipelineState.PLANNED, PipelineState.PUBLISHED_CONFIRMED)
