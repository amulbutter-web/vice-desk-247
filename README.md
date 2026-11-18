# Gaming Content Intelligence Platform (V2)

An autonomous, 24/7 cloud-native gaming content intelligence and automated clip production engine.

## Architecture Overview

1. **Dual Ingestion Engine**:
   - **Mode A (Live)**: Ingests up to **15 concurrent active live streams** with isolated per-source rolling buffers (120s buffer), PTS-to-UTC wall-clock synchronization, discontinuity detection, and fair weighted round-robin scheduling.
   - **Mode B (Uploads & Authorized URLs)**: Ingests long-form gameplay videos or authorized clips with SHA-256 integrity checks and SSRF-safe URL validation.

2. **Multimodal Highlight Detection**:
   - Audio transient, volume energy, and speech prosody detection.
   - Visual activity, motion intensity, and scene cut detection.
   - **Narrative Boundary Engine**: Expands raw climax peaks into complete storytelling moments (`onset` -> `buildup` -> `peak` -> `resolution`), dynamically sizing clips between 10s and 90s without arbitrary truncation.
   - **False-Positive Filtering**: Rejects screams on loading screens, blank/black screens, and lobby music while properly detecting and preserving **silent clutch plays**.

3. **Creative 9:16 Editorial & FFmpeg Rendering Engine**:
   - Reframes horizontal 16:9 gameplay into vertical 9:16 mobile formats:
     - **Split View**: Streamer facecam on top (35%), gameplay on bottom (65%).
     - **Centered ROI Crop**: Keeps crosshairs and game action in view.
     - **Picture-in-Picture (PiP)**: Streamer facecam inset.
   - Applies kinetic zooms on peak moments and platform loudness normalization (-14 LUFS, -1.0 dBTP).
   - Word-level timed subtitles formatted within safe vertical zones (avoiding TikTok/Reels UI dead zones).
   - Generates strict typed FFmpeg filtergraphs in Python with zero shell-injection vulnerabilities.

4. **Deterministic Hard QC & Editorial Supervisor**:
   - Hard Machine Gates: Resolution (1080x1920), duration (10-90s), h264/aac codecs, audio presence, black screen check (<= 500ms), video freeze check (<= 1000ms).
   - Calibrated Editorial Rubric (0-3 scale): Story completeness, game framing, hook strength, audio clarity.
   - Automated repair loop capped at 2 revisions before escalating to human review.

5. **Rights Clearance & Idempotent Publishing Outbox**:
   - Verifies creator consent scope and enforces instant revocation.
   - Remote ambiguity reconciliation prevents duplicate uploads on network timeouts.
   - Safe draft-only / private upload defaults for YouTube Shorts and Instagram Reels.
   - Immediate Operator Emergency Kill-Switch.

6. **Analytics & Closed-Loop Improvement**:
   - Standardized metric snapshots (24h, 7d, 30d).
   - Cohort analysis by creative layout and duration.
   - Canary rollout with automatic rollback on quality regressions.

---

## Quickstart

### 1. Initialize Database
```bash
python -m src.cli init
```

### 2. Process an Uploaded Video
```bash
python -m src.cli process --file fixtures/sample_gameplay_1080p.mp4 --creator "shroud" --layout "split_cam_game"
```

### 3. Simulate 15 Concurrent Live Streams
```bash
python -m src.cli test-15-streams --count 15
```

### 4. Launch Operator Web Dashboard
```bash
python -m src.cli serve --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Test Suite
Run the test suite with:
```bash
pytest tests -v
```
