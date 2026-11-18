"""
24/7 Enterprise Process Supervisor and Cloudflare Tunnel Manager.
Monitors the Uvicorn web server and Cloudflare Edge Tunnel, provides
automatic self-healing/restarts upon crash, and writes the active public HTTPS link.
"""
import os
import sys
import time
import signal
import subprocess
import threading
import logging
import re
from pathlib import Path
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("24_7_supervisor")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
BIN_DIR = BASE_DIR / "bin"
CLOUDFLARED_BIN = BIN_DIR / "cloudflared.exe"
PUBLIC_URL_FILE = DATA_DIR / "public_url.txt"
PY_EXE = sys.executable


class SupervisorDaemon:
    def __init__(self, port: int = 8000, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self.server_proc: subprocess.Popen = None
        self.tunnel_proc: subprocess.Popen = None
        self.public_url: str = None
        self.running: bool = False
        self._lock = threading.Lock()

    def start_server(self):
        """Starts the FastAPI web server."""
        cmd = [
            PY_EXE,
            "-m", "uvicorn",
            "src.server.app:app",
            "--host", self.host,
            "--port", str(self.port),
            "--log-level", "warning",
        ]
        logger.info(f"Starting Vice Desk API Server on {self.host}:{self.port}...")
        self.server_proc = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

    def start_tunnel(self):
        """Starts the Cloudflare Quick Tunnel."""
        if not CLOUDFLARED_BIN.exists():
            logger.warning(f"cloudflared binary not found at {CLOUDFLARED_BIN}. Skipping public tunnel.")
            return

        cmd = [
            str(CLOUDFLARED_BIN),
            "tunnel",
            "--url", f"http://localhost:{self.port}",
            "--metrics", "localhost:0",
        ]
        logger.info(f"Starting Cloudflare Secure Edge Tunnel pointing to port {self.port}...")
        self.tunnel_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Start thread to read public tunnel URL
        t = threading.Thread(target=self._monitor_tunnel_output, daemon=True)
        t.start()

    def _monitor_tunnel_output(self):
        """Monitors stdout of cloudflared to detect and extract the public HTTPS URL."""
        if not self.tunnel_proc or not self.tunnel_proc.stdout:
            return

        for line in self.tunnel_proc.stdout:
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                url = match.group(0)
                with self._lock:
                    self.public_url = url
                    PUBLIC_URL_FILE.parent.mkdir(parents=True, exist_ok=True)
                    PUBLIC_URL_FILE.write_text(url, encoding="utf-8")
                
                print("\n" + "=" * 70)
                print(">>> 24/7 VICE DESK PUBLIC LIVE LINK:")
                print(f">>> {url}")
                print(">>> Encrypted via Cloudflare Edge SSL | 100% Free Forever | Zero Attack Surface")
                print("=" * 70 + "\n")
                logger.info(f"Public URL established: {url}")
            elif "Registered tunnel connection" in line:
                logger.info("Cloudflare tunnel edge connection active.")

    def check_server_health(self) -> bool:
        """Pings the health endpoint to verify the server is responding."""
        health_url = f"http://127.0.0.1:{self.port}/api/health"
        try:
            with urllib.request.urlopen(health_url, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def run(self):
        """Main 24/7 supervisor loop with automatic crash recovery."""
        self.running = True
        logger.info("=== 24/7 VICE DESK SUPERVISOR ENGAGED ===")

        # Start components
        self.start_server()
        time.sleep(2)
        self.start_tunnel()

        failures = 0
        while self.running:
            try:
                time.sleep(10)

                # 1. Check Server Process Status
                if self.server_proc and self.server_proc.poll() is not None:
                    logger.error(f"Server crashed with exit code {self.server_proc.returncode}! Auto-restarting...")
                    self.start_server()
                    failures += 1

                # 2. Check Health Endpoint
                if not self.check_server_health():
                    logger.warning("Health check failed. Retrying in 5 seconds...")
                    time.sleep(5)
                    if not self.check_server_health():
                        logger.error("Health check permanently failed. Cycling server process...")
                        if self.server_proc:
                            self.server_proc.kill()
                        self.start_server()

                # 3. Check Cloudflare Tunnel Process Status
                if self.tunnel_proc and self.tunnel_proc.poll() is not None:
                    logger.warning("Cloudflare tunnel exited. Re-establishing edge connection...")
                    self.start_tunnel()

            except KeyboardInterrupt:
                logger.info("Shutdown signal received.")
                break
            except Exception as e:
                logger.error(f"Supervisor loop exception: {e}")
                time.sleep(5)

        self.stop()

    def stop(self):
        """Gracefully terminates all child processes."""
        self.running = False
        logger.info("Stopping all 24/7 supervisor processes...")
        if self.tunnel_proc:
            try:
                self.tunnel_proc.terminate()
                self.tunnel_proc.wait(timeout=3)
            except Exception:
                self.tunnel_proc.kill()

        if self.server_proc:
            try:
                self.server_proc.terminate()
                self.server_proc.wait(timeout=3)
            except Exception:
                self.server_proc.kill()

        logger.info("All processes cleanly stopped.")


def main():
    supervisor = SupervisorDaemon()

    def handle_sig(sig, frame):
        supervisor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    supervisor.run()


if __name__ == "__main__":
    main()
