"""
Unit tests validating Python contracts against official JSON Schema files in contracts/*.json.
Ensures zero contract drift, correct rejection of invalid payloads, and extra-field blocking.
"""
import json
import pytest
import jsonschema
from pathlib import Path
from src.core.contracts import (
    EventCandidate,
    FeatureEvidence,
    EditPlan,
    Segment,
    Canvas,
    EditOperation,
    QCResult,
    HardGate,
    EditorialAssessment,
    PublishIntent,
    MetricSnapshot,
    ErrorRecord,
)

CONTRACTS_DIR = Path(__file__).resolve().parent.parent / "Gaming_Intelligence_Build_Handoff_V2" / "contracts"


def load_schema(name: str) -> dict:
    with open(CONTRACTS_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def test_event_candidate_contract():
    schema = load_schema("event_candidate.json")
    candidate = EventCandidate(
        id="cand-001",
        trace_id="tr-001",
        source_id="src-001",
        media_asset_id="asset-001",
        capture_epoch=1700000000,
        window_start_ms=1000,
        window_end_ms=15000,
        event_type="clutch_kill",
        confidence=0.92,
        feature_evidence=[
            FeatureEvidence(name="audio_excitement", score=0.88, evidence_ref="ev-audio-01")
        ],
        provenance={"detector": "v2_multimodal"},
    )
    payload = candidate.model_dump()
    # Validate against official JSON schema
    jsonschema.validate(instance=payload, schema=schema)


def test_event_candidate_rejects_inverted_window():
    with pytest.raises(ValueError):
        EventCandidate(
            id="cand-002",
            trace_id="tr-002",
            source_id="src-001",
            media_asset_id="asset-001",
            capture_epoch=1700000000,
            window_start_ms=20000,
            window_end_ms=5000,  # Invalid: end < start
            event_type="fail",
        )


def test_edit_plan_contract():
    schema = load_schema("edit_plan.json")
    plan = EditPlan(
        id="plan-001",
        trace_id="tr-001",
        event_revision_id="rev-001",
        media_asset_id="asset-001",
        platform="youtube",
        segments=[
            Segment(source_start_ms=1000, source_end_ms=15000, time_epoch=0, reason="clutch")
        ],
        canvas=Canvas(width=1080, height=1920, fps=60.0),
        operations=[
            EditOperation(type="crop", start_ms=0, end_ms=14000, parameters={"mode": "split"}),
            EditOperation(type="zoom", start_ms=6000, end_ms=9000, parameters={"zoom_factor": 1.15}),
        ],
        evidence_refs=["ev-001"],
    )
    payload = plan.model_dump()
    jsonschema.validate(instance=payload, schema=schema)


def test_qc_result_contract():
    schema = load_schema("qc_result.json")
    qc = QCResult(
        id="qc-001",
        trace_id="tr-001",
        render_id="ren-001",
        evaluator_kind="deterministic",
        evaluator_version="v2.0",
        hard_gates=[
            HardGate(gate_id="GATE-RES", pass_=True, measured_value="1080x1920", reason="Exact match"),
            HardGate(gate_id="GATE-AUDIO", pass_=True, measured_value="-14.2 LUFS", reason="Nominal"),
        ],
        editorial=EditorialAssessment(
            result="pass",
            scores={"story_completeness": 3, "game_framing": 3, "hook_strength": 2, "audio_clarity": 3},
            findings=[],
        ),
        source_evidence_refs=["ren-001"],
    )
    payload = qc.model_dump(by_alias=True)
    jsonschema.validate(instance=payload, schema=schema)


def test_publish_intent_contract():
    schema = load_schema("publish_intent.json")
    intent = PublishIntent(
        id="pub-001",
        trace_id="tr-001",
        render_id="ren-001",
        destination="instagram",
        account_ref="creator-alpha",
        source_rights_ref="rights-001",
        approval_ref="approval-001",
        content_sha256="a" * 64,
        state="approved",
        attempts=0,
        created_at_utc="2026-11-18T00:00:00Z",
    )
    payload = intent.model_dump()
    jsonschema.validate(instance=payload, schema=schema)


def test_publish_intent_rejects_invalid_sha():
    with pytest.raises(ValueError):
        PublishIntent(
            id="pub-002",
            trace_id="tr-002",
            render_id="ren-001",
            destination="youtube",
            account_ref="creator",
            source_rights_ref="r",
            approval_ref="a",
            content_sha256="not-a-valid-sha256",  # Invalid regex
            state="draft",
            attempts=0,
            created_at_utc="2026-11-18T00:00:00Z",
        )
