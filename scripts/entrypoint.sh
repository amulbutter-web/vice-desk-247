#!/bin/sh
set -e

export PYTHONUTF8=1
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

echo "=== VICE DESK INTELLIGENCE 24/7 CLOUD SERVER STARTING ==="
echo "Date: $(date -u)"

# Start bgutil-pot token server on localhost in background if binary exists
if [ -x /usr/local/bin/bgutil-pot ]; then
    echo "[ENTRYPOINT] Starting bgutil-pot PO-token server on 127.0.0.1:4416..."
    /usr/local/bin/bgutil-pot server --host 127.0.0.1 --port 4416 &
    sleep 2
    echo "[ENTRYPOINT] bgutil-pot server backgrounded successfully."
else
    echo "[ENTRYPOINT] WARNING: /usr/local/bin/bgutil-pot not found. Proceeding with standard yt-dlp extractor."
fi

# Start Cloudflare WARP userspace proxy via Wireproxy ONLY if explicitly enabled (ENABLE_WARP=1)
if [ -x /usr/local/bin/wireproxy ] && [ "${ENABLE_WARP:-0}" = "1" ]; then
    echo "[ENTRYPOINT] Initializing Cloudflare WARP userspace proxy via Python setup..."
    mkdir -p /app/data/warp
    python3 /app/scripts/setup_warp.py || python3 scripts/setup_warp.py || true
    if [ -f "/app/data/warp/wgcf-profile.conf" ]; then
        echo "[ENTRYPOINT] Starting wireproxy (SOCKS5 :1080, HTTP :8080)..."
        /usr/local/bin/wireproxy -c /app/data/warp/wgcf-profile.conf &
        sleep 2
        echo "[ENTRYPOINT] Cloudflare WARP wireproxy started successfully."
    fi
fi

# Prepare cookies: decode and VALIDATE YOUTUBE_COOKIES_BASE64, otherwise keep pristine repo file
VALID_COOKIES=0
if [ -n "$YOUTUBE_COOKIES_BASE64" ]; then
    echo "[ENTRYPOINT] Detected YOUTUBE_COOKIES_BASE64 — validating UTF-8 Netscape cookie format..."
    if python3 -c "import os, base64, re; raw = os.getenv('YOUTUBE_COOKIES_BASE64', ''); clean = re.sub(r'[^A-Za-z0-9+/=]', '', raw); data = base64.b64decode(clean) if clean else b''; text = data.decode('utf-8', errors='ignore'); assert len(text) > 500; open('/tmp/youtube_cookies.txt', 'w', encoding='utf-8').write(text); open('/app/data/youtube_cookies.txt', 'w', encoding='utf-8').write(text)" 2>/dev/null; then
        chmod 600 /app/data/youtube_cookies.txt /tmp/youtube_cookies.txt 2>/dev/null || true
        COOKIE_SIZE=$(wc -c < /app/data/youtube_cookies.txt 2>/dev/null || echo 0)
        echo "[ENTRYPOINT] Valid cookies decoded from env: ${COOKIE_SIZE} bytes (UTF-8 sanitized)"
        VALID_COOKIES=1
    else
        echo "[ENTRYPOINT] WARNING: YOUTUBE_COOKIES_BASE64 is invalid or corrupted. Discarding env var and using repo file."
    fi
fi

if [ "$VALID_COOKIES" = "0" ] && [ -f "/app/data/youtube_cookies.txt" ] && [ -s "/app/data/youtube_cookies.txt" ]; then
    echo "[ENTRYPOINT] Using verified pristine cookies from repository /app/data/youtube_cookies.txt"
    python3 -c "raw = open('/app/data/youtube_cookies.txt', 'rb').read(); open('/tmp/youtube_cookies.txt', 'w', encoding='utf-8').write(raw.decode('utf-8', errors='ignore'))" 2>/dev/null || cp /app/data/youtube_cookies.txt /tmp/youtube_cookies.txt
    chmod 600 /tmp/youtube_cookies.txt
    COOKIE_SIZE=$(wc -c < /tmp/youtube_cookies.txt 2>/dev/null || echo 0)
    echo "[ENTRYPOINT] Repository cookies verified: ${COOKIE_SIZE} bytes"
fi

# Ensure data directories exist
mkdir -p /app/data/rendered /app/data/media /app/data/temp

echo "[ENTRYPOINT] Starting ViceDesk Uvicorn Server on port ${PORT:-8000}..."
exec python -m uvicorn src.server.app:app --host 0.0.0.0 --port "${PORT:-8000}"
