"""
Tests for RightsChecker, OutboxProcessor, Emergency Kill-Switch, and Remote Status Reconciliation.
"""
from src.publishing.rights_checker import RightsChecker
from src.publishing.reconciliation import RemoteReconciliationEngine
from src.publishing.outbox import OutboxProcessor
from src.publishing.publishers import YouTubePublisher, InstagramPublisher
from src.db.repository import Repository
from src.db.models import Source, MediaAsset, EventRevision, RenderedAsset
from src.config import settings


def test_rights_checker_consent_and_revocation():
    rc = RightsChecker()
    # Unregistered creator -> blocked
    ok, _ = rc.check_rights("creator-unknown", "youtube")
    assert ok is False

    # Registered creator -> cleared
    rc.register_consent("creator-01", "youtube")
    ok, _ = rc.check_rights("creator-01", "youtube")
    assert ok is True

    # Revoke consent -> instantly blocked
    rc.revoke_consent("creator-01", reason="contract_expired")
    ok, reason = rc.check_rights("creator-01", "youtube")
    assert ok is False
    assert "revoked" in reason.lower()


def test_remote_reconciliation_prevents_duplicate_posts():
    engine = RemoteReconciliationEngine()
    destination = "youtube"
    account = "streamer-01"
    sha = "f" * 64

    # First check: not published yet
    assert engine.check_remote_status(destination, account, sha) is None

    # Simulate completed upload
    engine.record_remote_publication(destination, account, sha, "yt-remote-1234")

    # Second check (e.g. after network timeout): detected as already published!
    remote = engine.check_remote_status(destination, account, sha)
    assert remote is not None
    assert remote["remote_id"] == "yt-remote-1234"


def test_outbox_emergency_kill_switch(db_session):
    repo = Repository(db_session)
    rc = RightsChecker()
    rc.register_consent("streamer-test", "youtube")
    reconciler = RemoteReconciliationEngine()
    outbox_proc = OutboxProcessor(session=db_session, rights_checker=rc, reconciler=reconciler)

    # Insert prerequisite FK chain: Source -> MediaAsset -> EventRevision -> RenderedAsset
    src = repo.create_or_get_source("streamer-test", "youtube", "https://youtube.com/streamer", "verified")
    asset = repo.create_media_asset("/tmp/test.mp4", "a" * 64, source_id=src.id, source_duration_ms=10000)
    
    rev = EventRevision(
        event_key="ev-test",
        media_id=asset.id,
        revision=1,
        source_start_ms=1000,
        source_end_ms=9000,
        payload={},
        provenance={},
    )
    db_session.add(rev)
    db_session.flush()

    rendered = RenderedAsset(
        event_revision_id=rev.id,
        sha256="c" * 64,
        output_ref="/tmp/rendered.mp4",
        target_platform="youtube",
    )
    db_session.add(rendered)
    db_session.flush()

    # Queue an intent referencing the valid RenderedAsset
    intent = repo.create_publish_intent(
        render_id=rendered.id,
        destination="youtube",
        account_ref="streamer-test",
        campaign_ref="camp-01",
        content_sha256="c" * 64,
        approval_ref="appr-01",
        rights_ref="rights-01",
        status="approved",
    )

    # Activate emergency kill switch
    settings.emergency_kill_switch = True
    try:
        results = outbox_proc.process_pending_outbox()
        assert results[0]["status"] == "HALTED"
    finally:
        settings.emergency_kill_switch = False
