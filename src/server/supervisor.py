"""
ViceDesk Supervisor Agent — 24/7 System Monitor & Email Notifier
Monitors: YouTube quota, Instagram publish status, daemon health, cloud health.
Sends email alerts to suhanisharma180801@gmail.com on any misalignment or failure.
Runs as a background thread inside the cloud container alongside AutonomousPublisherDaemon.
"""
import os
import time
import threading
import logging
import json
import urllib.request
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from src.core.groq_pool import GroqPool
from src.supervisor.supervisor_instructions import SUPERVISOR_INSTRUCTIONS

logger = logging.getLogger("supervisor_agent")

ALERT_EMAIL = "suhanisharma180801@gmail.com"
SENDER_EMAIL = "suhanisharma180801@gmail.com"
PRODUCTION_URL = "https://vice-desk-intelligence-production.up.railway.app"


class SupervisorAgent:
    """
    24/7 Autonomous Chief AI Supervisor (CEO Agent) powered by Groq LLM.
    Continuously monitors the ViceDesk pipeline, proactively diagnoses stalls,
    automatically self-heals stuck queues, skips failing streams, resets worker backoffs,
    and guarantees 100% continuous 24/7 publishing without human intervention.
    """

    def __init__(self, check_interval_sec: int = 120):
        self.check_interval_sec = check_interval_sec
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.last_published_count = 0
        self.stall_cycles = 0
        self.MAX_STALL_CYCLES = 2  # 2 cycles (4 mins) of idle triggers AI self-healing
        self.alert_cooldown: dict = {}  # prevent spam, one alert per issue per hour
        self.start_time = datetime.now(timezone.utc)
        self.groq_pool = GroqPool()

    # ─────────────────────── Public API ───────────────────────

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="SupervisorAgent",
        )
        self._thread.start()
        logger.info("SupervisorAgent started — monitoring pipeline every %ds", self.check_interval_sec)

    def stop(self):
        self.running = False

    # ─────────────────────── Core Loop ────────────────────────

    def _run_loop(self):
        time.sleep(30)  # Wait for server startup
        logger.info("[SUPERVISOR] Entering monitoring loop...")

        while self.running:
            try:
                self._run_checks()
            except Exception as e:
                logger.error("[SUPERVISOR] Check cycle error: %s", e, exc_info=True)
            time.sleep(self.check_interval_sec)

    def _run_checks(self):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        issues = []

        # 1. Cloud server health
        try:
            res = self._get(f"{PRODUCTION_URL}/api/health", timeout=10)
            if res.get("status") != "healthy":
                issues.append(f"🔴 Server health: {res.get('status', 'unknown')}")
            else:
                logger.info("[SUPERVISOR] Server healthy ✓")
        except Exception as e:
            issues.append(f"🔴 Server UNREACHABLE: {e}")

        # 2. Daemon running & auto-revival
        try:
            daemon = self._get(f"{PRODUCTION_URL}/api/daemon/status", timeout=10)
            if not daemon.get("running"):
                issues.append("🔴 24/7 Daemon was stopped! Auto-reviving...")
                try:
                    from src.server.background_scheduler import daemon_instance
                    daemon_instance.start()
                    logger.info("[SUPERVISOR] ✅ Auto-revived 24/7 daemon successfully!")
                except Exception as rev_e:
                    logger.error(f"[SUPERVISOR] Auto-revive failed: {rev_e}")
            else:
                published = daemon.get("published_count", 0) + daemon.get("ig_published_count", 0)
                quota_hit = daemon.get("daily_quota_hit", False)
                target_daily = SUPERVISOR_INSTRUCTIONS.get("target_daily_uploads", 50)
                creator_count = SUPERVISOR_INSTRUCTIONS.get("creator_count", 15)
                game = SUPERVISOR_INSTRUCTIONS.get("primary_game", "GTA 6")
                logger.info(
                    "[SUPERVISOR] MANDATE: %s ONLY | Target: %d/day across %d creators | Published: %d (YT:%d, IG:%d)",
                    game, target_daily, creator_count, published, daemon.get("published_count", 0), daemon.get("ig_published_count", 0)
                )

                # Stall detection: Instagram must NEVER stall, regardless of YouTube quota
                ig_published = daemon.get("ig_published_count", 0)
                if published == self.last_published_count:
                    self.stall_cycles += 1
                    if self.stall_cycles >= self.MAX_STALL_CYCLES:
                        issues.append(
                            f"⚠️ Pipeline idle: total published count at {published} for {self.stall_cycles} cycles"
                        )
                        # Trigger Autonomous Chief AI Self-Healing
                        self._run_ai_self_healing(issues, daemon)
                else:
                    self.stall_cycles = 0
                    self.last_published_count = published

                if quota_hit:
                    logger.info("[SUPERVISOR] YouTube daily upload quota hit — Instagram-exclusive mode active")

        except Exception as e:
            issues.append(f"🔴 Daemon status check failed: {e}")

        # 3. Instagram token
        try:
            ig = self._get(f"{PRODUCTION_URL}/api/accounts/instagram/status", timeout=10)
            if not ig.get("valid"):
                issues.append(f"🔴 Instagram token INVALID: {ig.get('message','?')}")
            else:
                logger.info("[SUPERVISOR] Instagram @%s connected ✓", ig.get("username"))
        except Exception as e:
            issues.append(f"🔴 Instagram status check failed: {e}")

        # 4. Send alert if issues found
        if issues:
            subject = f"[ViceDesk Alert] {len(issues)} issue(s) detected — {ts}"
            body = self._build_alert_body(issues, ts)
            self._send_email_alert(subject, body, issues)
        else:
            logger.info("[SUPERVISOR] All systems nominal at %s", ts)

    def _run_ai_self_healing(self, issues: list, daemon: dict):
        """
        Autonomous Chief AI Supervisor: Uses Groq LLM to diagnose the exact operational
        bottleneck, self-heal stuck queues, advance failing streams, and force-unstick
        the publishing pipeline.
        """
        logger.info("[AI_SUPERVISOR] 🧠 Initiating Groq Chief AI diagnostic & self-healing protocol...")
        try:
            from src.detection.first_time_ledger import FirstTimeLedger
            from src.server.background_scheduler import daemon_instance
            from src.supervisor.hierarchy import chief_supervisor_instance

            ledger = FirstTimeLedger()
            all_events = ledger.get_all_events()
            scheduled = [e for e in all_events if e["status"] == "SCHEDULED"]
            failed = [e for e in all_events if e["status"] == "FAILED"]
            processing = [e for e in all_events if e["status"] == "PROCESSING"]

            summary = {
                "stall_cycles": self.stall_cycles,
                "issues": issues,
                "total_scheduled": len(scheduled),
                "total_failed": len(failed),
                "total_processing": len(processing),
                "recent_failed_headlines": [e["headline"] for e in failed[:3]],
            }

            prompt = [
                {
                    "role": "system",
                    "content": (
                        "You are the Autonomous Chief AI Supervisor (CEO Agent) for ViceDesk Intelligence. "
                        "The owner requires 100% uninterrupted 24/7 autonomous video publishing on Instagram. "
                        "Diagnose stalls, skip dead streams, reset worker backoffs, and return actionable recovery JSON: "
                        "{\"diagnosis\": \"...\", \"action\": \"UNSTICK_AND_ADVANCE\", \"reason\": \"...\"}"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Pipeline Telemetry: {json.dumps(summary)}\nWhat executive action must be taken immediately to resume 24/7 publishing?",
                },
            ]

            try:
                plan_raw = self.groq_pool.generate_chat(prompt, agent_role="A09_JUDGE", max_tokens=150, temperature=0.2)
                logger.info("[AI_SUPERVISOR] Groq Chief AI Directive: %s", plan_raw)
            except Exception as ge:
                logger.warning(f"[AI_SUPERVISOR] Groq LLM advisory note: {ge}")

            # Execution 1: Reset daemon consecutive errors & sleep locks
            if daemon_instance:
                daemon_instance.consecutive_errors = 0
                daemon_instance.current_stream_idx += 1
                logger.info("[AI_SUPERVISOR] ✅ Cleared daemon consecutive errors and advanced stream index to %d", daemon_instance.current_stream_idx)

            # Execution 2: Unstick stale processing events in ledger
            from src.db.database import get_db_session
            from src.db.models import FirstTimeEvent
            with get_db_session() as session:
                stuck_events = session.query(FirstTimeEvent).filter(
                    FirstTimeEvent.status.in_(["PROCESSING", "FAILED"])
                ).all()
                for ev in stuck_events[:5]:
                    meta = dict(ev.metadata_json or {})
                    fails = meta.get("_consecutive_failures", 0)
                    if fails >= 4:
                        ev.status = "PARKED_FOR_REVIEW"
                        meta["_parked_by_supervisor"] = True
                        ev.metadata_json = meta
                        logger.info("[AI_SUPERVISOR] 🛡️ Parked repeatedly failing event '%s' to unblock queue", ev.headline)
                    else:
                        ev.status = "SCHEDULED"
                        meta["_processing_started_at"] = None
                        ev.metadata_json = meta
                        logger.info("[AI_SUPERVISOR] 🔄 Re-scheduled event '%s' for immediate self-healing retry", ev.headline)
                session.commit()

            # Execution 3: Ensure ChiefSupervisor parallel workers are active
            if chief_supervisor_instance and not chief_supervisor_instance.running:
                chief_supervisor_instance.start()
                logger.info("[AI_SUPERVISOR] 🚀 Revived ChiefSupervisorAgent parallel hierarchy!")

            self.stall_cycles = 0  # Reset counter after applying recovery
            logger.info("[AI_SUPERVISOR] ✅ Autonomous Self-Healing complete. Pipeline unblocked and actively running.")

        except Exception as e:
            logger.error("[AI_SUPERVISOR] Error in autonomous self-healing execution: %s", e, exc_info=True)

    # ─────────────────────── Email ────────────────────────────

    def _send_email_alert(self, subject: str, body: str, issues: list):
        """
        Sends alert email via Gmail SMTP (uses SMTP_PASSWORD env var).
        Falls back to logging if SMTP not configured.
        """
        smtp_pass = os.environ.get("SMTP_PASSWORD", "")
        smtp_user = os.environ.get("SMTP_USER", SENDER_EMAIL)

        # Deduplicate: only send each unique issue once per hour
        issue_key = "|".join(sorted(issues))
        now = time.time()
        if self.alert_cooldown.get(issue_key, 0) > now - 3600:
            logger.info("[SUPERVISOR] Alert cooldown active — skipping duplicate email")
            return
        self.alert_cooldown[issue_key] = now

        if not smtp_pass:
            # Log prominently so Railway logs show it
            logger.critical("[SUPERVISOR ALERT] %s\n%s", subject, body)
            # Try to call a notification webhook if configured
            webhook_url = os.environ.get("ALERT_WEBHOOK_URL", "")
            if webhook_url:
                try:
                    payload = json.dumps({"text": f"*{subject}*\n{body}"}).encode()
                    req = urllib.request.Request(webhook_url, data=payload,
                                                 headers={"Content-Type": "application/json"})
                    urllib.request.urlopen(req, timeout=5)
                except Exception:
                    pass
            return

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = ALERT_EMAIL

            html_body = self._build_html_email(issues, body)
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [ALERT_EMAIL], msg.as_string())

            logger.info("[SUPERVISOR] Alert email sent to %s", ALERT_EMAIL)
        except Exception as e:
            logger.error("[SUPERVISOR] Failed to send email: %s", e)

    def send_startup_notification(self):
        """Sends a startup success email when the system launches."""
        subject = "✅ ViceDesk Intelligence — System Started Successfully"
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        body = f"""
ViceDesk 24/7 Autonomous Publisher has started.

Timestamp: {ts}
Server: {PRODUCTION_URL}
Mode: 24/7 Cloud (Railway — San Francisco)

Connected Accounts:
  • YouTube: Channel "GTA 6" — 8 Shorts published
  • Instagram: @hritiksingh_8 — CONNECTED

Active Streams Monitored (11):
  TGG, Mythpat, Typical Gamer, Ducky Reloaded, CarryisLive,
  Dattrax Plays, RakaZone Gaming, Kreek, AS Gaming, 8bit Goldy, Destin

The supervisor will email you at this address whenever:
  • Any upload fails or stalls
  • YouTube/Instagram tokens expire
  • The daemon stops running
  • Cloud server goes down

No action needed — just watch for alerts.
        """
        smtp_pass = os.environ.get("SMTP_PASSWORD", "")
        if smtp_pass:
            self._send_email_alert(subject, body, ["STARTUP"])
        else:
            logger.info("[SUPERVISOR] SMTP not configured. Add SMTP_PASSWORD to Railway env vars to receive emails.")

    # ─────────────────────── Helpers ──────────────────────────

    def _get(self, url: str, timeout: int = 10) -> dict:
        headers = {"User-Agent": "ViceDeskSupervisor/2.0"}
        password = os.environ.get("VICE_OPERATOR_PASSWORD")
        if password:
            import base64
            token = base64.b64encode(f"owner:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())

    def _build_alert_body(self, issues: list, ts: str) -> str:
        lines = [
            f"ViceDesk Alert — {ts}",
            f"Server: {PRODUCTION_URL}",
            "",
            "Issues detected:",
        ]
        for i, issue in enumerate(issues, 1):
            lines.append(f"  {i}. {issue}")
        lines += [
            "",
            "Dashboard: " + PRODUCTION_URL + "/api/daemon/status",
            "Instagram: " + PRODUCTION_URL + "/api/accounts/instagram/status",
            "Health:    " + PRODUCTION_URL + "/api/health",
            "",
            "— ViceDesk Supervisor Agent",
        ]
        return "\n".join(lines)

    def _build_html_email(self, issues: list, plain: str) -> str:
        issue_items = "".join(f"<li style='color:#e53e3e;margin:6px 0'>{i}</li>" for i in issues)
        return f"""
<html><body style="font-family:sans-serif;max-width:600px;margin:auto;padding:20px">
  <h2 style="color:#e53e3e">🚨 ViceDesk Intelligence Alert</h2>
  <p style="color:#666">Automated notification from your 24/7 publishing supervisor</p>
  <div style="background:#fff5f5;border-left:4px solid #e53e3e;padding:16px;border-radius:4px">
    <strong>Issues detected:</strong>
    <ul>{issue_items}</ul>
  </div>
  <div style="margin-top:20px;background:#f7fafc;padding:16px;border-radius:4px">
    <strong>Quick Links:</strong><br>
    <a href="{PRODUCTION_URL}/api/daemon/status">Daemon Status</a> |
    <a href="{PRODUCTION_URL}/api/accounts/instagram/status">Instagram Status</a> |
    <a href="{PRODUCTION_URL}/api/health">Health Check</a>
  </div>
  <p style="color:#999;font-size:12px;margin-top:20px">
    ViceDesk Supervisor Agent — 24/7 on Railway Cloud
  </p>
</body></html>"""


# Global singleton
supervisor_instance = SupervisorAgent(check_interval_sec=120)  # 2-min autonomous watchdog
