-- =====================================================================
-- Supabase PostgreSQL 17 Production Schema for ClipIntel / Vice Desk
-- Project ref: vxbtaekawtpnaxrmduxj
-- Replaces incompatible MySQL Drizzle schema with native PostgreSQL DDL
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table (Compatible with Supabase Auth)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    open_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    role VARCHAR(32) DEFAULT 'user' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 2. Stream Sources (Twitch, YouTube, Kick, Upload)
CREATE TABLE IF NOT EXISTS sources (
    id VARCHAR(64) PRIMARY KEY,
    creator_key VARCHAR(120) NOT NULL,
    platform VARCHAR(32) NOT NULL,
    handle VARCHAR(160),
    game VARCHAR(120),
    source_type VARCHAR(32) DEFAULT 'LIVE_STREAM' NOT NULL,
    source_url TEXT,
    authorization_status VARCHAR(32) DEFAULT 'pending' NOT NULL,
    source_state VARCHAR(32) DEFAULT 'idle' NOT NULL,
    priority INT DEFAULT 100 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 3. Media Assets
CREATE TABLE IF NOT EXISTS media_assets (
    id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(64) REFERENCES sources(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    duration_ms INT NOT NULL,
    width INT NOT NULL,
    height INT NOT NULL,
    fps NUMERIC(5,2) NOT NULL,
    codec_video VARCHAR(32),
    codec_audio VARCHAR(32),
    storage_type VARCHAR(32) DEFAULT 'LOCAL' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 4. Candidate Highlight Events
CREATE TABLE IF NOT EXISTS candidate_events (
    id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(64) REFERENCES sources(id) ON DELETE CASCADE,
    media_asset_id VARCHAR(64) REFERENCES media_assets(id),
    title VARCHAR(255) NOT NULL,
    category VARCHAR(64) DEFAULT 'action' NOT NULL,
    status VARCHAR(32) DEFAULT 'NEEDS_EDITOR' NOT NULL,
    scout_score INT NOT NULL,
    window_start_ms INT NOT NULL,
    window_end_ms INT NOT NULL,
    peak_ms INT,
    audio_loudness_db NUMERIC(5,2),
    chat_velocity INT DEFAULT 0,
    visual_motion_score NUMERIC(5,2),
    silent_clutch BOOLEAN DEFAULT FALSE,
    hostile_chat_detected BOOLEAN DEFAULT FALSE,
    transcript TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 5. Creative Edit Plans
CREATE TABLE IF NOT EXISTS edit_plans (
    id VARCHAR(64) PRIMARY KEY,
    candidate_id VARCHAR(64) REFERENCES candidate_events(id) ON DELETE CASCADE,
    trace_id VARCHAR(64) NOT NULL,
    version INT DEFAULT 1 NOT NULL,
    layout_mode VARCHAR(32) DEFAULT 'split_cam_game' NOT NULL,
    hook_text VARCHAR(120),
    caption_style VARCHAR(32) DEFAULT 'viral_gold' NOT NULL,
    loudness_target_lufs NUMERIC(5,2) DEFAULT -14.0 NOT NULL,
    plan_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 6. Rendered 9:16 Assets
CREATE TABLE IF NOT EXISTS rendered_assets (
    id VARCHAR(64) PRIMARY KEY,
    candidate_id VARCHAR(64) REFERENCES candidate_events(id) ON DELETE CASCADE,
    edit_plan_id VARCHAR(64) REFERENCES edit_plans(id),
    file_path TEXT NOT NULL,
    public_url TEXT,
    sha256 VARCHAR(64) NOT NULL,
    duration_ms INT NOT NULL,
    width INT DEFAULT 1080 NOT NULL,
    height INT DEFAULT 1920 NOT NULL,
    fps INT DEFAULT 60 NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 7. QC Audits & Hard Gates
CREATE TABLE IF NOT EXISTS qc_audits (
    id VARCHAR(64) PRIMARY KEY,
    rendered_asset_id VARCHAR(64) REFERENCES rendered_assets(id) ON DELETE CASCADE,
    verdict VARCHAR(16) NOT NULL, -- PASS or FAIL
    hard_gate_pass BOOLEAN NOT NULL,
    black_frame_detected BOOLEAN DEFAULT FALSE,
    frozen_frame_detected BOOLEAN DEFAULT FALSE,
    audio_sync_ok BOOLEAN DEFAULT TRUE,
    safe_zone_pass BOOLEAN DEFAULT TRUE,
    reviewer_model VARCHAR(64),
    review_score INT,
    repair_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 8. Publish Outbox & Idempotency
CREATE TABLE IF NOT EXISTS publish_intents (
    id VARCHAR(64) PRIMARY KEY,
    candidate_id VARCHAR(64) REFERENCES candidate_events(id),
    rendered_asset_id VARCHAR(64) REFERENCES rendered_assets(id),
    destination VARCHAR(32) NOT NULL, -- instagram, youtube, tiktok
    status VARCHAR(32) DEFAULT 'QUEUED' NOT NULL, -- QUEUED, IN_PROGRESS, PUBLISHED, FAILED
    container_id VARCHAR(120),
    remote_media_id VARCHAR(120),
    caption TEXT,
    scheduled_for TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 9. Metric Snapshots & Self-Learning
CREATE TABLE IF NOT EXISTS metric_snapshots (
    id VARCHAR(64) PRIMARY KEY,
    publish_intent_id VARCHAR(64) REFERENCES publish_intents(id) ON DELETE CASCADE,
    views INT DEFAULT 0,
    likes INT DEFAULT 0,
    shares INT DEFAULT 0,
    comments INT DEFAULT 0,
    avg_watch_time_sec NUMERIC(6,2),
    completion_rate NUMERIC(5,2),
    retention_curve JSONB,
    captured_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 10. Operational Health & Locks
CREATE TABLE IF NOT EXISTS operation_controls (
    key VARCHAR(64) PRIMARY KEY,
    value VARCHAR(255) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

INSERT INTO operation_controls (key, value) VALUES
    ('emergency_kill_switch', 'false'),
    ('auto_post_unlocked', 'false'),
    ('daily_post_cap', '25'),
    ('post_gap_min', '45'),
    ('quota_limit', '50'),
    ('quota_usage', '0')
ON CONFLICT (key) DO NOTHING;
