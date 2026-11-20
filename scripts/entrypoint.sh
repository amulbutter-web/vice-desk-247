#!/bin/sh
set -e

export PYTHONUTF8=1
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

echo "=== VICE DESK INTELLIGENCE 24/7 CLOUD SERVER STARTING ==="
echo "Date: $(date -u)"

# Clean up any legacy yt-dlp plugin cache or conflicting files
rm -rf /root/.config/yt-dlp/plugins /tmp/plugin.zip 2>/dev/null || true

# Prepare cookies: prioritize repository file /app/data/youtube_cookies.txt
if [ -f "/app/data/youtube_cookies.txt" ] && [ -s "/app/data/youtube_cookies.txt" ]; then
    echo "[ENTRYPOINT] Using verified cookies from /app/data/youtube_cookies.txt"
    cp /app/data/youtube_cookies.txt /tmp/youtube_cookies.txt
    chmod 600 /tmp/youtube_cookies.txt
    COOKIE_SIZE=$(wc -c < /tmp/youtube_cookies.txt 2>/dev/null || echo 0)
    echo "[ENTRYPOINT] Cookies verified: ${COOKIE_SIZE} bytes"
elif [ -n "$YOUTUBE_COOKIES_BASE64" ]; then
    echo "[ENTRYPOINT] Detected YOUTUBE_COOKIES_BASE64 — decoding via Python safe decoder..."
    python3 -c "import os, base64, re; raw = os.getenv('YOUTUBE_COOKIES_BASE64', ''); clean = re.sub(r'[^A-Za-z0-9+/=]', '', raw); open('/tmp/youtube_cookies.txt', 'wb').write(base64.b64decode(clean)) if clean else None" || true
    chmod 600 /tmp/youtube_cookies.txt 2>/dev/null || true
    COOKIE_SIZE=$(wc -c < /tmp/youtube_cookies.txt 2>/dev/null || echo 0)
    echo "[ENTRYPOINT] Cookies decoded: ${COOKIE_SIZE} bytes"
fi

# Ensure data directories exist
mkdir -p /app/data/rendered /app/data/media /app/data/temp

echo "[ENTRYPOINT] Starting ViceDesk Uvicorn Server on port ${PORT:-8000}..."
exec python -m uvicorn src.server.app:app --host 0.0.0.0 --port "${PORT:-8000}"
