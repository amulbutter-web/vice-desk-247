# =====================================================================
# Vice Desk / ClipIntel — Production Container
# Optimized for Coolify (coollabs.io), Local Docker, and Linux VPS
# =====================================================================
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    FFMPEG_BINARY=ffmpeg

WORKDIR /app

# Install system dependencies: FFmpeg, FFprobe, Node.js (for yt-dlp JS runtime), and fonts for ASS subtitles
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    curl \
    nodejs \
    && fc-cache -f -v \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies manifest
COPY pyproject.toml ./

# Install Python requirements
RUN pip install --no-cache-dir \
    fastapi==0.115.6 \
    uvicorn==0.32.1 \
    pydantic==2.10.3 \
    pydantic-settings==2.14.2 \
    sqlalchemy>=2.0.0 \
    jsonschema>=4.20.0 \
    click>=8.0.0 \
    yt-dlp \
    starlette==0.41.3 \
    pytest==8.4.2 \
    pytest-asyncio==0.26.0

# Copy source code and assets
COPY src/ ./src/
COPY data/ ./data/

# Ensure directories exist
RUN mkdir -p /app/data/rendered /app/data/media /app/data/temp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "uvicorn", "src.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
