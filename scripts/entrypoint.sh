#!/bin/sh
set -e

export PYTHONUTF8=1
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

echo "=== VICE DESK INTELLIGENCE 24/7 CLOUD SERVER STARTING ==="
echo "Date: $(date -u)"

# Clean up any legacy yt-dlp plugin cache or conflicting files
rm -rf /root/.config/yt-dlp/plugins /tmp/plugin.zip 2>/dev/null || true

# Decode YOUTUBE_COOKIES_BASE64 if provided in Railway env
if [ -n "$YOUTUBE_COOKIES_BASE64" ]; then
    echo "[ENTRYPOINT] Detected YOUTUBE_COOKIES_BASE64 — exporting to /tmp/youtube_cookies.txt"
    printf '%s' "$YOUTUBE_COOKIES_BASE64" | base64 -d > /tmp/youtube_cookies.txt || true
    chmod 600 /tmp/youtube_cookies.txt 2>/dev/null || true
    mkdir -p /app/data 2>/dev/null || true
    cp /tmp/youtube_cookies.txt /app/data/youtube_cookies.txt 2>/dev/null || true
    COOKIE_SIZE=$(wc -c < /tmp/youtube_cookies.txt 2>/dev/null || echo 0)
    echo "[ENTRYPOINT] Cookies file written: ${COOKIE_SIZE} bytes"
fi

# Ensure data directories exist
mkdir -p /app/data/rendered /app/data/media /app/data/temp

echo "[ENTRYPOINT] Starting ViceDesk Uvicorn Server on port ${PORT:-8000}..."
exec python -m uvicorn src.server.app:app --host 0.0.0.0 --port "${PORT:-8000}"
