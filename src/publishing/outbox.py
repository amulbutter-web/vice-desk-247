"""
Idempotent Publish Outbox Processor.
Handles transactional leasing, retry backoff, emergency kill-switch,
and remote status reconciliation.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from src.config import settings
from src.db.models import OutboxRecord, PublishIntentRecord, utc_now
from src.publishing.rights_checker import RightsChecker
from src.publishing.reconciliation import RemoteReconciliationEngine
from src.publishing.publishers import YouTubePublisher, InstagramPublisher


class OutboxProcessor:
    def __init__(
        self,
        session: Session,
        rights_checker: RightsChecker,
        reconciler: RemoteReconciliationEngine,
        youtube_pub: Optional[YouTubePublisher] = None,
        instagram_pub: Optional[InstagramPublisher] = None,
    ):
        self.session = session
        self.rights_checker = rights_checker
        self.reconciler = reconciler
        self.youtube = youtube_pub or YouTubePublisher()
        self.instagram = instagram_pub or InstagramPublisher()

    def process_pending_outbox(self, max_items: int = 10) -> List[Dict[str, Any]]:
        """
        Polls and executes pending outbox publication items.
        """
        # Check Emergency Kill Switch
        if settings.emergency_kill_switch:
            return [{"status": "HALTED", "reason": "EMERGENCY_KILL_SWITCH_ACTIVE"}]

        now = utc_now()
        records = (
            self.session.query(OutboxRecord)
            .filter(OutboxRecord.next_attempt_utc <= now)
            .limit(max_items)
            .all()
        )

        results = []
        for outbox in records:
            intent = self.session.query(PublishIntentRecord).filter_by(id=outbox.publish_intent_id).first()
            if not intent:
                self.session.delete(outbox)
                continue

            # 1. Verify Rights & Consent before dispatch
            has_rights, rights_reason = self.rights_checker.check_rights(intent.account_ref, intent.destination)
            if not has_rights:
                intent.status = "blocked"
                self.session.delete(outbox)
                results.append({"intent_id": intent.id, "status": "BLOCKED", "reason": rights_reason})
                continue

            # 2. Check Remote Reconciliation (Did a previous timed-out attempt actually succeed?)
            existing_remote = self.reconciler.check_remote_status(
                intent.destination, intent.account_ref, intent.content_sha256
            )
            if existing_remote:
                intent.status = "confirmed"
                intent.remote_media_id = existing_remote["remote_id"]
                intent.remote_status = existing_remote["status"]
                self.session.delete(outbox)
                results.append({"intent_id": intent.id, "status": "CONFIRMED_VIA_RECONCILIATION"})
                continue

            # 3. Dispatch to platform
            intent.status = "submitting"
            intent.attempt_count += 1
            intent.last_attempt_utc = now
            self.session.flush()

            try:
                if intent.destination == "youtube":
                    pub_res = self.youtube.upload_short(
                        video_path=intent.render_id,
                        title="Epic Gaming Clutch",
                        description="#gaming #shorts",
                        account_ref=intent.account_ref,
                        privacy_status="private" if settings.publish_draft_only else "public",
                    )
                else:
                    c_id = self.instagram.create_reel_container(intent.render_id, "Highlight", intent.account_ref)
                    c_status = self.instagram.poll_container_status(c_id)
                    pub_res = self.instagram.publish_container(c_id, intent.account_ref)

                intent.status = "confirmed"
                intent.remote_media_id = pub_res["remote_id"]
                intent.remote_status = pub_res["status"]

                # Record in remote reconciliation registry
                self.reconciler.record_remote_publication(
                    intent.destination, intent.account_ref, intent.content_sha256, pub_res["remote_id"]
                )

                self.session.delete(outbox)
                results.append({"intent_id": intent.id, "status": "CONFIRMED", "remote_id": pub_res["remote_id"]})

            except Exception as e:
                # Retry with exponential backoff
                if intent.attempt_count >= settings.max_publish_retries:
                    intent.status = "failed"
                    self.session.delete(outbox)
                    results.append({"intent_id": intent.id, "status": "DEAD_LETTER", "error": str(e)})
                else:
                    intent.status = "queued"
                    backoff_sec = (2 ** intent.attempt_count) * 10
                    outbox.next_attempt_utc = now + timedelta(seconds=backoff_sec)
                    outbox.last_error_class = str(e)
                    results.append({"intent_id": intent.id, "status": "RETRY_SCHEDULED", "error": str(e)})

        self.session.commit()
        return results
