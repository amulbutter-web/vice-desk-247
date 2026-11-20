# =====================================================================
# Vice Desk / ClipIntel — Production Container
# Optimized for Railway, Coolify, Local Docker, and Linux VPS
# =====================================================================
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PORT=8000 \
    FFMPEG_BINARY=ffmpeg

WORKDIR /app

# Install system dependencies: FFmpeg, FFprobe, Node.js + Deno (for yt-dlp JS runtime), and fonts for ASS subtitles
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    curl \
    unzip \
    nodejs \
    && (which node || ln -s $(which nodejs) /usr/local/bin/node) \
    && (curl -fsSL https://deno.land/install.sh | sh && ln -s /root/.deno/bin/deno /usr/local/bin/deno || true) \
    && fc-cache -f -v \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies manifest
COPY pyproject.toml ./

# Install Python requirements
RUN pip install --no-cache-dir \
    fastapi==0.115.6 \
    python-multipart \
    uvicorn==0.32.1 \
    pydantic==2.10.3 \
    pydantic-settings==2.14.2 \
    sqlalchemy>=2.0.0 \
    psycopg2-binary>=2.9.0 \
    jsonschema>=4.20.0 \
    click>=8.0.0 \
    "yt-dlp[default]" \
    starlette==0.41.3 \
    pytest==8.4.2 \
    pytest-asyncio==0.26.0

# Copy source code, scripts, and assets
COPY src/ ./src/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Ensure entrypoint and directories are prepared
RUN chmod +x /app/scripts/entrypoint.sh \
    && mkdir -p /app/data/rendered /app/data/media /app/data/temp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
