"""
Typed data contracts conforming to official JSON Schema specifications.
Strictly disallows arbitrary/unvalidated properties (extra = 'forbid').
"""
from typing import List, Dict, Optional, Literal, Union, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class FeatureEvidence(BaseModel):
    name: str = Field(..., min_length=1)
    score: float
    evidence_ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class EventCandidate(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(..., min_length=1)
    trace_id: str = Field(..., min_length=1)
    source_id: str = Field(..., min_length=1)
    media_asset_id: str = Field(..., min_length=1)
    capture_epoch: int = Field(..., ge=0)
    window_start_ms: int = Field(..., ge=0)
    window_end_ms: int = Field(..., ge=0)
    event_type: str = Field(..., min_length=1)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    feature_evidence: List[FeatureEvidence] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @field_validator("window_end_ms")
    @classmethod
    def validate_window(cls, v: int, info) -> int:
        if "window_start_ms" in info.data and v < info.data["window_start_ms"]:
            raise ValueError("window_end_ms must be >= window_start_ms")
        return v


class Segment(BaseModel):
    source_start_ms: int = Field(..., ge=0)
    source_end_ms: int = Field(..., ge=1)
    time_epoch: int = Field(..., ge=0)
    reason: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @field_validator("source_end_ms")
    @classmethod
    def validate_segment_order(cls, v: int, info) -> int:
        if "source_start_ms" in info.data and v <= info.data["source_start_ms"]:
            raise ValueError("source_end_ms must be strictly greater than source_start_ms")
        return v


class Canvas(BaseModel):
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)
    fps: float = Field(..., gt=0)

    model_config = ConfigDict(extra="forbid")


class EditOperation(BaseModel):
    type: Literal[
        "crop",
        "zoom",
        "overlay_text",
        "subtitle",
        "slow_motion",
        "fade",
        "audio_gain",
        "pip",
        "hard_cut"
    ]
    start_ms: int = Field(..., ge=0)
    end_ms: int = Field(..., ge=0)
    parameters: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class EditPlan(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(..., min_length=1)
    trace_id: str = Field(..., min_length=1)
    event_revision_id: str = Field(..., min_length=1)
    media_asset_id: str = Field(..., min_length=1)
    platform: Literal["instagram", "youtube"]
    segments: List[Segment] = Field(..., min_length=1)
    canvas: Canvas
    operations: List[EditOperation] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class HardGate(BaseModel):
    gate_id: str = Field(..., min_length=1)
    pass_: bool = Field(..., alias="pass")
    measured_value: Optional[Union[float, str]] = None
    reason: str

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class EditorialFinding(BaseModel):
    start_ms: int = Field(..., ge=0)
    end_ms: int = Field(..., ge=0)
    reason: str = Field(..., min_length=1)
    suggested_fix: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class EditorialAssessment(BaseModel):
    result: Literal["pass", "repair", "reject", "human_review"]
    scores: Dict[str, int]
    findings: List[EditorialFinding] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @field_validator("scores")
    @classmethod
    def validate_score_range(cls, v: Dict[str, int]) -> Dict[str, int]:
        for k, score in v.items():
            if score < 0 or score > 3:
                raise ValueError(f"Score for {k} must be within [0, 3], got {score}")
        return v


class QCResult(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(..., min_length=1)
    trace_id: str = Field(..., min_length=1)
    render_id: str = Field(..., min_length=1)
    evaluator_kind: Literal["deterministic", "multimodal", "human"]
    evaluator_version: str = Field(..., min_length=1)
    hard_gates: List[HardGate] = Field(default_factory=list)
    editorial: EditorialAssessment
    source_evidence_refs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class PublishIntent(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(..., min_length=1)
    trace_id: str = Field(..., min_length=1)
    render_id: str = Field(..., min_length=1)
    destination: Literal["instagram", "youtube"]
    account_ref: str = Field(..., min_length=1)
    source_rights_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    content_sha256: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    state: Literal[
        "draft",
        "approved",
        "queued",
        "submitting",
        "remote_processing",
        "unknown",
        "confirmed",
        "failed",
        "blocked"
    ]
    remote_media_id: Optional[str] = None
    attempts: int = Field(default=0, ge=0)
    created_at_utc: str

    model_config = ConfigDict(extra="forbid")


class MetricSnapshot(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(..., min_length=1)
    trace_id: str = Field(..., min_length=1)
    publish_intent_id: str = Field(..., min_length=1)
    metric_name: str
    availability: str
    metric_value: Optional[float] = None
    unit: str
    platform_definition: str
    window: str
    captured_at_utc: str

    model_config = ConfigDict(extra="forbid")


class ErrorRecord(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(..., min_length=1)
    trace_id: str = Field(..., min_length=1)
    code: str
    stage: str
    trace_id_external: str
    message: str
    retryable: bool
    retry_after_utc: Optional[str] = None
    diagnostic_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
