"""
Tests for MetricsTracker, HypothesisEngine (Cohort Analysis), and CanaryManager (Safe Rollback).
"""
from src.analytics.tracker import MetricsTracker
from src.analytics.hypothesis import HypothesisEngine
from src.analytics.canary import CanaryManager


def test_metrics_tracker_record_snapshot():
    tracker = MetricsTracker()
    snap = tracker.record_snapshot(
        snapshot_id="snap-01",
        trace_id="tr-01",
        publish_intent_id="pub-01",
        metric_name="views",
        metric_value=15420.0,
        unit="count",
        window="24h",
        platform_definition="YouTube Shorts Views",
    )
    assert snap.metric_value == 15420.0
    assert snap.availability == "available"
    assert snap.window == "24h"


def test_hypothesis_engine_cohort_analysis():
    engine = HypothesisEngine()
    # Simulated 24h performance data across layout modes
    data = [
        {"layout_mode": "split_cam_game", "average_percentage_viewed": 82.5},
        {"layout_mode": "split_cam_game", "average_percentage_viewed": 79.0},
        {"layout_mode": "split_cam_game", "average_percentage_viewed": 85.0},
        {"layout_mode": "center_roi", "average_percentage_viewed": 61.0},
        {"layout_mode": "center_roi", "average_percentage_viewed": 64.5},
        {"layout_mode": "pip", "average_percentage_viewed": 71.0},
    ]
    res = engine.evaluate_layout_cohorts(data)
    assert res["cohort_averages"]["split_cam_game"] > res["cohort_averages"]["center_roi"]
    assert "split_cam_game" in res["recommended_policy_change"]


def test_canary_manager_rollback_on_regression():
    cm = CanaryManager(canary_traffic_pct=0.20)
    cm.deploy_canary("v2_aggressive_zoom")
    assert cm.canary_policy == "v2_aggressive_zoom"

    # Canary suffers quality regression (0.68 vs baseline 0.90)
    decision = cm.evaluate_and_decide(baseline_pass_rate=0.90, canary_pass_rate=0.68)
    assert decision["decision"] == "ROLLBACK"
    assert cm.is_rolled_back is True
    assert cm.active_policy == "v1_default"
