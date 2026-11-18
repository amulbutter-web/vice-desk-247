"""
Unit tests for the State Machine, optimistic locking, and lease recovery.
"""
import pytest
from src.core.state_machine import (
    PipelineState,
    validate_transition,
    StateTransitionError,
    OptimisticLockError,
)
from src.db.repository import Repository


def test_valid_pipeline_transitions():
    assert validate_transition(PipelineState.INGESTED, PipelineState.FEATURES_EXTRACTED)
    assert validate_transition(PipelineState.FEATURES_EXTRACTED, PipelineState.CANDIDATE_DETECTED)
    assert validate_transition(PipelineState.CANDIDATE_DETECTED, PipelineState.STORY_BOUNDED)
    assert validate_transition(PipelineState.STORY_BOUNDED, PipelineState.PLANNED)
    assert validate_transition(PipelineState.PLANNED, PipelineState.RENDERED)
    assert validate_transition(PipelineState.RENDERED, PipelineState.QC_MACHINE_PASS)
    assert validate_transition(PipelineState.QC_MACHINE_PASS, PipelineState.QC_EDITOR_PASS)
    assert validate_transition(PipelineState.QC_EDITOR_PASS, PipelineState.APPROVED)
    assert validate_transition(PipelineState.APPROVED, PipelineState.PUBLISH_OUTBOX)
    assert validate_transition(PipelineState.PUBLISH_OUTBOX, PipelineState.PUBLISHED_CONFIRMED)


def test_illegal_state_transition():
    # Direct jump from INGESTED to PUBLISHED_CONFIRMED must be blocked!
    with pytest.raises(StateTransitionError):
        validate_transition(PipelineState.INGESTED, PipelineState.PUBLISHED_CONFIRMED)


def test_optimistic_locking_and_lease(db_session):
    repo = Repository(db_session)
    job = repo.create_job(job_type="detect", stage=PipelineState.INGESTED.value)

    # Worker 1 acquires lease
    leased = repo.acquire_job_lease(worker_id="worker-1", lease_duration_sec=30)
    assert leased is not None
    assert leased.id == job.id
    assert leased.lease_owner == "worker-1"
    initial_version = leased.state_version

    # Worker 1 transitions state successfully
    repo.transition_job_state(
        job_id=job.id,
        expected_version=initial_version,
        new_stage=PipelineState.FEATURES_EXTRACTED.value,
        actor_ref="worker-1",
        reason_code="EXTRACTION_COMPLETE",
    )

    # Worker 2 attempts transition with stale version -> OptimisticLockError!
    with pytest.raises(OptimisticLockError):
        repo.transition_job_state(
            job_id=job.id,
            expected_version=initial_version,  # Stale version
            new_stage=PipelineState.CANDIDATE_DETECTED.value,
            actor_ref="worker-2",
            reason_code="STALE_WORKER",
        )


def test_expired_lease_recovery(db_session):
    from datetime import datetime, timezone, timedelta
    repo = Repository(db_session)
    job = repo.create_job(job_type="render", stage=PipelineState.PLANNED.value)

    # Set lease to already expired
    job.lease_owner = "worker-dead"
    job.lease_expiry_utc = datetime.now(timezone.utc) - timedelta(seconds=10)
    db_session.commit()

    # Run lease recovery
    recovered = repo.recover_expired_leases()
    assert recovered >= 1

    # Job is freed
    re_job = db_session.query(type(job)).filter_by(id=job.id).first()
    assert re_job.lease_owner is None
    assert re_job.retry_count == 1
