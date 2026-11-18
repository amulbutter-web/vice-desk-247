"""
Repository layer providing atomic transactions, lease locking,
version compare-and-set, and idempotent outbox queries.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from src.db.models import (
    Source,
    MediaAsset,
    Job,
    EventRevision,
    RenderedAsset,
    QCAudit,
    PublishIntentRecord,
    OutboxRecord,
    MetricSnapshotRecord,
    EventHistory,
    gen_uuid,
    utc_now,
)
from src.core.state_machine import PipelineState, validate_transition, OptimisticLockError


class Repository:
    def __init__(self, session: Session):
        self.session = session

    # Source operations
    def create_or_get_source(
        self, creator_key: str, platform: str, source_locator: str, authorization_status: str = "pending"
    ) -> Source:
        source = (
            self.session.query(Source)
            .filter_by(platform=platform, source_locator=source_locator)
            .first()
        )
        if not source:
            source = Source(
                creator_key=creator_key,
                platform=platform,
                source_locator=source_locator,
                authorization_status=authorization_status,
                source_state="active",
            )
            self.session.add(source)
            self.session.flush()
        return source

    def list_active_sources(self) -> List[Source]:
        return self.session.query(Source).filter_by(source_state="active").all()

    # Media Asset operations
    def create_media_asset(
        self, storage_ref: str, sha256: str, source_id: Optional[str] = None, source_duration_ms: Optional[int] = None, rights_status: str = "pending"
    ) -> MediaAsset:
        asset = MediaAsset(
            source_id=source_id,
            sha256=sha256,
            source_duration_ms=source_duration_ms,
            storage_ref=storage_ref,
            rights_status=rights_status,
        )
        self.session.add(asset)
        self.session.flush()
        return asset

    def get_media_asset(self, asset_id: str) -> Optional[MediaAsset]:
        return self.session.query(MediaAsset).filter_by(id=asset_id).first()

    # Job & Lease Management (Optimistic Locking & Crash-Safe Queue)
    def create_job(self, job_type: str, stage: str, media_id: Optional[str] = None, source_id: Optional[str] = None) -> Job:
        job = Job(
            media_id=media_id,
            source_id=source_id,
            job_type=job_type,
            stage=stage,
            state_version=1,
        )
        self.session.add(job)
        self.session.flush()
        self.record_history("SYSTEM", "job", job.id, None, stage, "JOB_CREATED", {"job_type": job_type})
        return job

    def acquire_job_lease(
        self, worker_id: str, lease_duration_sec: int = 60, stage: Optional[str] = None
    ) -> Optional[Job]:
        now = utc_now()
        query = self.session.query(Job).filter(
            or_(
                Job.lease_owner.is_(None),
                Job.lease_expiry_utc < now,
            )
        )
        if stage:
            query = query.filter_by(stage=stage)
        
        job = query.order_by(Job.created_at_utc.asc()).first()
        if not job:
            return None

        # Acquire lease with version increment
        job.lease_owner = worker_id
        job.lease_expiry_utc = now + timedelta(seconds=lease_duration_sec)
        job.state_version += 1
        job.updated_at_utc = now
        self.session.flush()
        return job

    def transition_job_state(
        self, job_id: str, expected_version: int, new_stage: str, actor_ref: str, reason_code: str, payload: Optional[Dict] = None
    ) -> Job:
        job = self.session.query(Job).filter_by(id=job_id).with_for_update().first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.state_version != expected_version:
            raise OptimisticLockError(
                f"Version conflict for job {job_id}: expected {expected_version}, got {job.state_version}"
            )

        prev_stage = job.stage
        # Validate through state machine
        try:
            from_enum = PipelineState(prev_stage)
            to_enum = PipelineState(new_stage)
            validate_transition(from_enum, to_enum)
        except ValueError:
            # Stage names might be sub-tasks, allow if not in enum
            pass

        job.stage = new_stage
        job.state_version += 1
        job.lease_owner = None
        job.lease_expiry_utc = None
        job.updated_at_utc = utc_now()
        self.session.flush()

        self.record_history(actor_ref, "job", job.id, prev_stage, new_stage, reason_code, payload)
        return job

    def recover_expired_leases(self) -> int:
        now = utc_now()
        expired_jobs = self.session.query(Job).filter(
            and_(Job.lease_owner.isnot(None), Job.lease_expiry_utc < now)
        ).all()
        count = 0
        for job in expired_jobs:
            job.lease_owner = None
            job.lease_expiry_utc = None
            job.retry_count += 1
            job.state_version += 1
            count += 1
        self.session.flush()
        return count

    # Audit & History
    def record_history(
        self, actor_ref: str, entity_type: str, entity_id: str, prev_state: Optional[str], next_state: str, reason_code: str, payload: Optional[Dict] = None
    ):
        history = EventHistory(
            trace_id=gen_uuid(),
            entity_type=entity_type,
            entity_id=entity_id,
            previous_state=prev_state,
            next_state=next_state,
            actor_ref=actor_ref,
            reason_code=reason_code,
            payload=payload or {},
        )
        self.session.add(history)
        self.session.flush()

    # Outbox & Idempotency
    def find_publish_intent_by_hash(
        self, destination: str, account_ref: str, campaign_ref: str, content_sha256: str
    ) -> Optional[PublishIntentRecord]:
        return (
            self.session.query(PublishIntentRecord)
            .filter_by(
                destination=destination,
                account_ref=account_ref,
                campaign_ref=campaign_ref,
                content_sha256=content_sha256,
            )
            .first()
        )

    def create_publish_intent(
        self,
        render_id: str,
        destination: str,
        account_ref: str,
        campaign_ref: str,
        content_sha256: str,
        approval_ref: str,
        rights_ref: str,
        status: str = "draft",
    ) -> PublishIntentRecord:
        # Check idempotency first
        existing = self.find_publish_intent_by_hash(destination, account_ref, campaign_ref, content_sha256)
        if existing:
            return existing

        intent = PublishIntentRecord(
            render_id=render_id,
            destination=destination,
            account_ref=account_ref,
            campaign_ref=campaign_ref,
            content_sha256=content_sha256,
            approval_ref=approval_ref,
            rights_ref=rights_ref,
            status=status,
            version=1,
        )
        self.session.add(intent)
        self.session.flush()

        # Add to outbox if approved
        if status in {"approved", "queued"}:
            outbox = OutboxRecord(
                publish_intent_id=intent.id,
                next_attempt_utc=utc_now(),
            )
            self.session.add(outbox)
            self.session.flush()

        return intent
