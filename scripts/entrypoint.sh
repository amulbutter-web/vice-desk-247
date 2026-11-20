#!/bin/sh
set -e

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

# Decode YOUTUBE_COOKIES_BASE64 if provided in Railway env
if [ -n "$YOUTUBE_COOKIES_BASE64" ]; then
    echo "[ENTRYPOINT] Detected YOUTUBE_COOKIES_BASE64 — exporting to /tmp/youtube_cookies.txt"
    printf '%s' "$YOUTUBE_COOKIES_BASE64" | base64 -d > /tmp/youtube_cookies.txt || true
    chmod 600 /tmp/youtube_cookies.txt 2>/dev/null || true
    COOKIE_SIZE=$(wc -c < /tmp/youtube_cookies.txt 2>/dev/null || echo 0)
    echo "[ENTRYPOINT] Cookies file written: ${COOKIE_SIZE} bytes"
fi

# Ensure data directories exist
mkdir -p /app/data/rendered /app/data/media /app/data/temp

echo "[ENTRYPOINT] Starting ViceDesk Uvicorn Server on port ${PORT:-8000}..."
exec python -m uvicorn src.server.app:app --host 0.0.0.0 --port "${PORT:-8000}"
