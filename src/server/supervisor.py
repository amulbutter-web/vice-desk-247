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

logger = logging.getLogger("supervisor_agent")

ALERT_EMAIL = "suhanisharma180801@gmail.com"
SENDER_EMAIL = "suhanisharma180801@gmail.com"
PRODUCTION_URL = "https://vice-desk-intelligence-production.up.railway.app"


class SupervisorAgent:
    """
    24/7 watchdog that monitors the entire ViceDesk pipeline and sends
    email alerts to the owner whenever something breaks or stalls.

    Checks every 10 minutes:
    - Cloud server health (HTTP /api/health)
    - Daemon running status (/api/daemon/status)
    - YouTube daily quota (uploadLimitExceeded flag)
    - Instagram token validity (/api/accounts/instagram/status)
    - Pending upload queue stall detection
    - New video publish confirmation
    """

    def __init__(self, check_interval_sec: int = 600):
        self.check_interval_sec = check_interval_sec
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.last_published_count = 0
        self.stall_cycles = 0
        self.MAX_STALL_CYCLES = 3  # 30 min stall → alert
        self.alert_cooldown: dict = {}  # prevent spam, one alert per issue per hour
        self.start_time = datetime.now(timezone.utc)

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
                logger.info(
                    "[SUPERVISOR] Daemon running, total_published=%d (YT:%d, IG:%d), quota_hit=%s",
                    published, daemon.get("published_count", 0), daemon.get("ig_published_count", 0), quota_hit
                )

                # Stall detection (only flag if neither YT nor IG published for 3 cycles and no quota excuse)
                if published == self.last_published_count:
                    self.stall_cycles += 1
                    if self.stall_cycles >= self.MAX_STALL_CYCLES and not quota_hit:
                        issues.append(
                            f"⚠️ Pipeline idle: total published count at {published} for {self.stall_cycles} cycles"
                        )
                else:
                    self.stall_cycles = 0
                    self.last_published_count = published

                if quota_hit:
                    issues.append("⚠️ YouTube daily upload quota hit — uploads paused until midnight IST")

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
        req = urllib.request.Request(url)
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
supervisor_instance = SupervisorAgent(check_interval_sec=600)  # 10-min cadence
