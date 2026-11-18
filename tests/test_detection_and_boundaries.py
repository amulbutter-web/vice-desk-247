"""
Tests for Narrative Boundary Engine, Multi-Signal Analysis, and False-Positive Filter.
"""
from src.detection.narrative_boundary import NarrativeBoundaryEngine
from src.detection.false_positive_filter import FalsePositiveFilter


def test_narrative_boundary_expansion():
    engine = NarrativeBoundaryEngine(
        default_pre_roll_ms=4000,
        default_post_roll_ms=5000,
        min_duration_ms=10000,
        max_duration_ms=90000,
    )
    # Peak at 20,000ms in a 60,000ms video
    bounds = engine.expand_event_boundaries(
        peak_ms=20000,
        source_duration_ms=60000,
        scene_cuts_ms=[15000, 26000],
    )
    assert bounds["window_start_ms"] <= 16000
    assert bounds["window_end_ms"] >= 25000
    assert bounds["duration_ms"] >= 10000
    assert "narrative_stages" in bounds
    assert bounds["narrative_stages"]["peak_ms"] == 20000


def test_false_positive_loading_screen_scream():
    fp = FalsePositiveFilter()
    candidate = {"window_start_ms": 1000, "window_end_ms": 15000}
    freeze_frames = [{"start_ms": 2000, "end_ms": 8000, "duration_ms": 6000}]  # 6s freeze
    black_frames = []

    # High scream excitement (0.9), but on frozen screen -> MUST REJECT!
    is_valid, reason, _ = fp.evaluate_candidate(
        event_candidate=candidate,
        black_frames=black_frames,
        freeze_frames=freeze_frames,
        audio_excitement=0.9,
        visual_activity=0.1,
    )
    assert is_valid is False
    assert reason == "REJECTED_LOADING_SCREEN_SCREAM"


def test_false_positive_black_screen():
    fp = FalsePositiveFilter()
    candidate = {"window_start_ms": 1000, "window_end_ms": 15000}
    black_frames = [{"start_ms": 3000, "end_ms": 7000, "duration_ms": 4000}]  # 4s black
    freeze_frames = []

    is_valid, reason, _ = fp.evaluate_candidate(
        event_candidate=candidate,
        black_frames=black_frames,
        freeze_frames=freeze_frames,
        audio_excitement=0.8,
        visual_activity=0.5,
    )
    assert is_valid is False
    assert reason == "REJECTED_BLACK_SCREEN_OVERLAP"


def test_silent_clutch_acceptance():
    fp = FalsePositiveFilter()
    candidate = {"window_start_ms": 5000, "window_end_ms": 20000}
    black_frames = []
    freeze_frames = []

    # Quiet audio (0.2), but intense visual action (0.85) -> MUST ACCEPT AS SILENT CLUTCH!
    is_valid, reason, metrics = fp.evaluate_candidate(
        event_candidate=candidate,
        black_frames=black_frames,
        freeze_frames=freeze_frames,
        audio_excitement=0.2,
        visual_activity=0.85,
    )
    assert is_valid is True
    assert reason == "ACCEPTED_SILENT_CLUTCH"
    assert metrics["classification"] == "silent_clutch"
