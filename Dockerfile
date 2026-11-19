# =====================================================================
# Vice Desk / ClipIntel — Production Container
# Optimized for Railway, Coolify, Local Docker, and Linux VPS
# =====================================================================
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
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

# Install bgutil-pot binary for Proof-of-Origin token generation (bypasses YouTube bot challenges on cloud servers)
RUN curl -fsSL -o /usr/local/bin/bgutil-pot \
    https://github.com/jim60105/bgutil-ytdlp-pot-provider-rs/releases/download/v0.8.1/bgutil-pot-linux-x86_64 \
    && chmod +x /usr/local/bin/bgutil-pot

# Install yt-dlp plugin for bgutil-pot
RUN mkdir -p /root/.config/yt-dlp/plugins \
    && curl -fsSL -o /tmp/plugin.zip \
    https://github.com/jim60105/bgutil-ytdlp-pot-provider-rs/releases/download/v0.8.1/bgutil-ytdlp-pot-provider-rs.zip \
    && unzip /tmp/plugin.zip -d /root/.config/yt-dlp/plugins/ \
    && rm /tmp/plugin.zip

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
    jsonschema>=4.20.0 \
    click>=8.0.0 \
    "yt-dlp[default]" \
    yt-dlp-ejs>=0.8.0 \
    bgutil-ytdlp-pot-provider \
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
