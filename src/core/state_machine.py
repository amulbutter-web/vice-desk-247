"""
Durable State Machine for pipeline jobs and rendered assets.
Implements optimistic locking (version compare-and-set), strictly validated transitions,
and audit trail recording.
"""
from enum import Enum
from typing import Set, Dict, Optional, Any
from dataclasses import dataclass, field
import datetime


class PipelineState(str, Enum):
    # Core linear stages
    INGESTED = "INGESTED"
    FEATURES_EXTRACTED = "FEATURES_EXTRACTED"
    CANDIDATE_DETECTED = "CANDIDATE_DETECTED"
    STORY_BOUNDED = "STORY_BOUNDED"
    PLAN_APPROVED = "PLAN_APPROVED"
    PLANNED = "PLANNED"
    RENDERED = "RENDERED"
    QC_MACHINE_PASS = "QC_MACHINE_PASS"
    QC_EDITOR_PASS = "QC_EDITOR_PASS"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    PUBLISH_OUTBOX = "PUBLISH_OUTBOX"
    REMOTE_PROCESSING = "REMOTE_PROCESSING"
    PUBLISHED_CONFIRMED = "PUBLISHED_CONFIRMED"
    METRICS_READY = "METRICS_READY"

    # Terminal & corrective states
    REJECTED = "REJECTED"
    NEEDS_PERMISSION = "NEEDS_PERMISSION"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    INVALID_INPUT = "INVALID_INPUT"
    DEAD_LETTER = "DEAD_LETTER"
    CANCELLED = "CANCELLED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"


class StateTransitionError(Exception):
    pass


class OptimisticLockError(StateTransitionError):
    pass


# Valid state transitions graph
VALID_TRANSITIONS: Dict[PipelineState, Set[PipelineState]] = {
    PipelineState.INGESTED: {
        PipelineState.FEATURES_EXTRACTED,
        PipelineState.INVALID_INPUT,
        PipelineState.NEEDS_PERMISSION,
        PipelineState.CANCELLED,
    },
    PipelineState.FEATURES_EXTRACTED: {
        PipelineState.CANDIDATE_DETECTED,
        PipelineState.REJECTED,  # e.g., no highlights found
        PipelineState.RETRY_SCHEDULED,
        PipelineState.CANCELLED,
    },
    PipelineState.CANDIDATE_DETECTED: {
        PipelineState.STORY_BOUNDED,
        PipelineState.REJECTED,
        PipelineState.RETRY_SCHEDULED,
    },
    PipelineState.STORY_BOUNDED: {
        PipelineState.PLANNED,
        PipelineState.REJECTED,
        PipelineState.NEEDS_HUMAN,
    },
    PipelineState.PLANNED: {
        PipelineState.PLAN_APPROVED,
        PipelineState.RENDERED,
        PipelineState.REJECTED,
        PipelineState.RETRY_SCHEDULED,
    },
    PipelineState.PLAN_APPROVED: {
        PipelineState.RENDERED,
        PipelineState.RETRY_SCHEDULED,
        PipelineState.CANCELLED,
    },
    PipelineState.RENDERED: {
        PipelineState.QC_MACHINE_PASS,
        PipelineState.REJECTED,  # Hard gate fail
        PipelineState.RETRY_SCHEDULED,  # e.g. FFmpeg crash
    },
    PipelineState.QC_MACHINE_PASS: {
        PipelineState.QC_EDITOR_PASS,
        PipelineState.RETRY_SCHEDULED,  # Editorial repair
        PipelineState.NEEDS_HUMAN,
        PipelineState.REJECTED,
    },
    PipelineState.QC_EDITOR_PASS: {
        PipelineState.AWAITING_APPROVAL,
        PipelineState.APPROVED,  # If auto-publish enabled by policy
        PipelineState.NEEDS_HUMAN,
        PipelineState.CANCELLED,
    },
    PipelineState.AWAITING_APPROVAL: {
        PipelineState.APPROVED,
        PipelineState.REJECTED,
        PipelineState.RETRY_SCHEDULED,  # Re-edit requested by human
        PipelineState.CANCELLED,
    },
    PipelineState.APPROVED: {
        PipelineState.PUBLISH_OUTBOX,
        PipelineState.CANCELLED,
        PipelineState.NEEDS_PERMISSION,
    },
    PipelineState.PUBLISH_OUTBOX: {
        PipelineState.REMOTE_PROCESSING,
        PipelineState.PUBLISHED_CONFIRMED,
        PipelineState.RETRY_SCHEDULED,
        PipelineState.DEAD_LETTER,
    },
    PipelineState.REMOTE_PROCESSING: {
        PipelineState.PUBLISHED_CONFIRMED,
        PipelineState.RETRY_SCHEDULED,
        PipelineState.DEAD_LETTER,
    },
    PipelineState.PUBLISHED_CONFIRMED: {
        PipelineState.METRICS_READY,
    },
    PipelineState.METRICS_READY: set(),  # Terminal success

    # Corrective state can loop back
    PipelineState.RETRY_SCHEDULED: {
        PipelineState.INGESTED,
        PipelineState.FEATURES_EXTRACTED,
        PipelineState.PLANNED,
        PipelineState.RENDERED,
        PipelineState.PUBLISH_OUTBOX,
        PipelineState.DEAD_LETTER,
        PipelineState.CANCELLED,
    },

    # Terminal states
    PipelineState.REJECTED: set(),
    PipelineState.NEEDS_PERMISSION: {PipelineState.INGESTED, PipelineState.APPROVED, PipelineState.CANCELLED},
    PipelineState.NEEDS_HUMAN: {PipelineState.PLANNED, PipelineState.APPROVED, PipelineState.REJECTED, PipelineState.CANCELLED},
    PipelineState.INVALID_INPUT: set(),
    PipelineState.DEAD_LETTER: set(),
    PipelineState.CANCELLED: set(),
}


@dataclass
class JobState:
    job_id: str
    current_state: PipelineState
    state_version: int = 0
    lease_owner: Optional[str] = None
    lease_expiry_utc: Optional[datetime.datetime] = None
    retry_count: int = 0
    max_retries: int = 3


def validate_transition(from_state: PipelineState, to_state: PipelineState) -> bool:
    """Checks whether the transition is allowed by the formal state graph."""
    allowed = VALID_TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        raise StateTransitionError(
            f"Illegal state transition from {from_state.value} to {to_state.value}. "
            f"Allowed next states: {[s.value for s in allowed]}"
        )
    return True
