"""
SQLAlchemy models matching schema.sql specifications with support for SQLite and PostgreSQL.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    BigInteger,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    UniqueConstraint,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Source(Base):
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    creator_key = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)  # twitch, youtube, custom
    source_locator = Column(String(1024), nullable=False)
    authorization_status = Column(String(50), nullable=False, default="pending")  # verified, pending, revoked, expired
    authorization_ref = Column(String(255), nullable=True)
    source_state = Column(String(50), nullable=False, default="active")  # active, paused, stopped
    created_at_utc = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("platform", "source_locator", name="uq_platform_locator"),
    )


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    source_id = Column(String(36), ForeignKey("sources.id"), nullable=True)
    sha256 = Column(String(64), nullable=False)
    source_duration_ms = Column(BigInteger, nullable=True)
    storage_ref = Column(String(1024), nullable=False)
    rights_status = Column(String(50), nullable=False, default="pending")  # verified, pending, revoked, unknown
    state_version = Column(BigInteger, nullable=False, default=0)
    created_at_utc = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    media_id = Column(String(36), ForeignKey("media_assets.id"), nullable=True)
    source_id = Column(String(36), ForeignKey("sources.id"), nullable=True)
    job_type = Column(String(50), nullable=False)  # ingest, detect, render, qc, publish
    stage = Column(String(50), nullable=False)
    state_version = Column(BigInteger, nullable=False, default=0)
    lease_owner = Column(String(255), nullable=True)
    lease_expiry_utc = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at_utc = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at_utc = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("idx_jobs_work_q", "stage", "lease_expiry_utc", "created_at_utc"),
    )


class EventRevision(Base):
    __tablename__ = "event_revisions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    event_key = Column(String(255), nullable=False)
    media_id = Column(String(36), ForeignKey("media_assets.id"), nullable=False)
    revision = Column(Integer, nullable=False, default=1)
    source_start_ms = Column(BigInteger, nullable=False)
    source_end_ms = Column(BigInteger, nullable=False)
    payload = Column(JSON, nullable=False)
    provenance = Column(JSON, nullable=False)
    created_at_utc = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("event_key", "revision", name="uq_event_key_revision"),
    )


class RenderedAsset(Base):
    __tablename__ = "rendered_assets"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    event_revision_id = Column(String(36), ForeignKey("event_revisions.id"), nullable=False)
    sha256 = Column(String(64), nullable=False)
    output_ref = Column(String(1024), nullable=False)
    target_platform = Column(String(50), nullable=False)  # instagram, youtube
    config_version = Column(String(50), nullable=False, default="v1.0")
    qc_state = Column(String(50), nullable=False, default="pending")
    created_at_utc = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class QCAudit(Base):
    __tablename__ = "qc_audits"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    render_id = Column(String(36), ForeignKey("rendered_assets.id"), nullable=False)
    evaluator_type = Column(String(50), nullable=False)  # deterministic, multimodal, human
    evaluator_version = Column(String(50), nullable=False)
    result = Column(JSON, nullable=False)
    is_hard_pass = Column(Boolean, nullable=False)
    created_at_utc = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class PublishIntentRecord(Base):
    __tablename__ = "publish_intents"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    render_id = Column(String(36), ForeignKey("rendered_assets.id"), nullable=False)
    destination = Column(String(50), nullable=False)  # instagram, youtube
    account_ref = Column(String(255), nullable=False)
    campaign_ref = Column(String(255), nullable=False, default="")
    content_sha256 = Column(String(64), nullable=False)
    approval_ref = Column(String(255), nullable=False)
    rights_ref = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # draft, approved, queued, submitting, remote_processing, confirmed, failed, blocked
    remote_media_id = Column(String(255), nullable=True)
    remote_status = Column(String(255), nullable=True)
    last_attempt_utc = Column(DateTime(timezone=True), nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    version = Column(BigInteger, nullable=False, default=0)
    created_at_utc = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("destination", "account_ref", "campaign_ref", "content_sha256", name="uq_publish_dest_acct_sha"),
    )


class OutboxRecord(Base):
    __tablename__ = "outbox"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    publish_intent_id = Column(String(36), ForeignKey("publish_intents.id"), unique=True, nullable=False)
    next_attempt_utc = Column(DateTime(timezone=True), nullable=False)
    locked_until_utc = Column(DateTime(timezone=True), nullable=True)
    last_error_class = Column(String(255), nullable=True)
    created_at_utc = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class MetricSnapshotRecord(Base):
    __tablename__ = "metric_snapshots"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    publish_intent_id = Column(String(36), ForeignKey("publish_intents.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    measurement_window = Column(String(50), nullable=False)
    availability = Column(String(50), nullable=False)
    metric_unit = Column(String(50), nullable=True)
    metric_value = Column(Numeric, nullable=True)
    platform_definition = Column(Text, nullable=True)
    captured_at_utc = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("publish_intent_id", "metric_name", "measurement_window", "captured_at_utc", name="uq_metric_intent_window_time"),
    )


class EventHistory(Base):
    __tablename__ = "event_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(36), nullable=False)
    previous_state = Column(String(50), nullable=True)
    next_state = Column(String(50), nullable=False)
    actor_ref = Column(String(255), nullable=False)
    reason_code = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=True)
    created_at_utc = Column(DateTime(timezone=True), nullable=False, default=utc_now)
