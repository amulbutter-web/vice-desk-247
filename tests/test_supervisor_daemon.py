"""
Tests for 24/7 SupervisorDaemon process management and health verification.
"""
import time
import pytest
from src.supervisor.daemon import SupervisorDaemon


def test_supervisor_daemon_lifecycle():
    # Use alternate test port to avoid conflict
    test_port = 8019
    supervisor = SupervisorDaemon(port=test_port)

    try:
        # 1. Start server
        supervisor.start_server()
        assert supervisor.server_proc is not None
        assert supervisor.server_proc.poll() is None

        # Wait up to 5 seconds for health
        healthy = False
        for _ in range(10):
            time.sleep(0.5)
            if supervisor.check_server_health():
                healthy = True
                break

        assert healthy is True, f"Server did not become healthy on port {test_port}"

    finally:
        # 2. Stop server
        supervisor.stop()
        time.sleep(0.5)
        assert supervisor.server_proc.poll() is not None
