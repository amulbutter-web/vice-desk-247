"""
Security guards, anti-prompt injection, URL allowlist, and safe-zone validators.
Prevents SSRF, shell injection, and malicious LLM hijacking from untrusted media/chat.
"""
import re
import ipaddress
import urllib.parse
from typing import Tuple, Dict, Any


class SecurityError(Exception):
    pass


class SSRFValidationError(SecurityError):
    pass


# Disallowed IP ranges for URL ingestion (private, loopback, link-local, cloud metadata)
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.169.254/32"),  # AWS / GCP / Oracle Cloud metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

ALLOWED_SCHEMES = {"http", "https"}


def validate_ingest_url(url: str, allow_private: bool = False) -> str:
    """
    Validates URL before downloading media.
    Guards against SSRF, internal port scanning, and cloud metadata theft.
    """
    parsed = urllib.parse.urlparse(url.strip())
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise SSRFValidationError(f"Disallowed URL scheme: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("Missing hostname in URL")

    # Reject localhost directly
    if hostname.lower() in {"localhost", "localhost.localdomain"}:
        raise SSRFValidationError(f"Direct localhost access forbidden: {hostname}")

    # Check IP addresses
    try:
        ip = ipaddress.ip_address(hostname)
        if not allow_private:
            for net in BLOCKED_IP_NETWORKS:
                if ip in net:
                    raise SSRFValidationError(f"Target IP {ip} is within blocked private/metadata network {net}")
    except ValueError:
        # Hostname is a domain name, not raw IP
        pass

    return url.strip()


def sanitize_untrusted_text(text: str, max_length: int = 500) -> str:
    """
    Sanitizes untrusted text originating from chat, OCR, transcripts, or video overlays.
    Strips control characters, terminal escape sequences, and prompt-injection keywords.
    """
    if not text:
        return ""

    # Truncate to avoid buffer exhaustion
    cleaned = text[:max_length]

    # Remove ANSI escape sequences
    cleaned = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", cleaned)

    # Remove non-printable / control characters except newline and tab
    cleaned = "".join(ch for ch in cleaned if ch == "\n" or ch == "\t" or (ord(ch) >= 32 and ord(ch) != 127))

    # Neutralize common prompt injection markers
    injection_patterns = [
        r"(?i)\b(system|assistant|developer)\s*:\s*",
        r"(?i)\bignore\s+all\s+(previous|prior)\s+instructions\b",
        r"(?i)\byou\s+are\s+now\s+in\s+(dan|developer|override)\s+mode\b",
        r"(?i)\bprint\s+(env|environment|api_key|token|secrets)\b",
    ]
    for pattern in injection_patterns:
        cleaned = re.sub(pattern, "[FILTERED_INJECTION]", cleaned)

    return cleaned.strip()


def validate_safe_zone(
    x: int, y: int, width: int, height: int, canvas_width: int = 1080, canvas_height: int = 1920
) -> Tuple[bool, str]:
    """
    Ensures text or overlays stay within safe 9:16 mobile zones:
    - Top 15% clear (story progress bars, account info)
    - Bottom 20% clear (captions, platform sound selector, comments)
    - Side 10% clear (like/share/bookmark buttons)
    """
    top_limit = int(canvas_height * 0.15)
    bottom_limit = int(canvas_height * 0.80)
    left_limit = int(canvas_width * 0.10)
    right_limit = int(canvas_width * 0.90)

    element_top = y
    element_bottom = y + height
    element_left = x
    element_right = x + width

    if element_top < top_limit:
        return False, f"Element violates top safe zone (y={element_top} < {top_limit})"
    if element_bottom > bottom_limit:
        return False, f"Element violates bottom safe zone (y+h={element_bottom} > {bottom_limit})"
    if element_left < left_limit:
        return False, f"Element violates left safe zone (x={element_left} < {left_limit})"
    if element_right > right_limit:
        return False, f"Element violates right safe zone (x+w={element_right} > {right_limit})"

    return True, "Safe zone respected"
