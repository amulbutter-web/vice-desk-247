-- Draft PostgreSQL starter. Requires reviewed migrations, OAuth/account tables, RLS/auth policies before production.
CREATE TABLE sources (
 id uuid PRIMARY KEY, creator_key text NOT NULL, platform text NOT NULL, source_locator text NOT NULL,
 authorization_status text NOT NULL CHECK (authorization_status IN ('verified','pending','revoked','expired')),
 authorization_ref text, source_state text NOT NULL, created_at_utc timestamptz NOT NULL DEFAULT now(),
 UNIQUE(platform,source_locator)
);
CREATE TABLE media_assets (
 id uuid PRIMARY KEY, source_id uuid REFERENCES sources(id), sha256 text NOT NULL,
 source_duration_ms bigint CHECK (source_duration_ms>=0), storage_ref text NOT NULL,
 rights_status text NOT NULL CHECK (rights_status IN ('verified','pending','revoked','unknown')),
 state_version bigint NOT NULL DEFAULT 0, created_at_utc timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE jobs (
 id uuid PRIMARY KEY, media_id uuid REFERENCES media_assets(id), source_id uuid REFERENCES sources(id),
 job_type text NOT NULL, stage text NOT NULL, state_version bigint NOT NULL DEFAULT 0,
 lease_owner text, lease_expiry_utc timestamptz, retry_count int NOT NULL DEFAULT 0,
 created_at_utc timestamptz NOT NULL DEFAULT now(), updated_at_utc timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX jobs_work_q ON jobs(stage,lease_expiry_utc,created_at_utc);
CREATE TABLE event_revisions (
 id uuid PRIMARY KEY, event_key text NOT NULL, media_id uuid NOT NULL REFERENCES media_assets(id),
 revision int NOT NULL CHECK(revision>0), source_start_ms bigint NOT NULL, source_end_ms bigint NOT NULL,
 payload jsonb NOT NULL, provenance jsonb NOT NULL, created_at_utc timestamptz NOT NULL DEFAULT now(),
 CHECK (source_start_ms>=0 AND source_end_ms>source_start_ms), UNIQUE(event_key,revision)
);
CREATE TABLE rendered_assets (
 id uuid PRIMARY KEY, event_revision_id uuid NOT NULL REFERENCES event_revisions(id),
 sha256 text NOT NULL, output_ref text NOT NULL, target_platform text NOT NULL, config_version text NOT NULL,
 qc_state text NOT NULL DEFAULT 'pending', created_at_utc timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE qc_audits (
 id uuid PRIMARY KEY, render_id uuid NOT NULL REFERENCES rendered_assets(id),
 evaluator_type text NOT NULL, evaluator_version text NOT NULL, result jsonb NOT NULL,
 is_hard_pass boolean NOT NULL, created_at_utc timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE publish_intents (
 id uuid PRIMARY KEY, render_id uuid NOT NULL REFERENCES rendered_assets(id), destination text NOT NULL,
 account_ref text NOT NULL, campaign_ref text NOT NULL DEFAULT '', content_sha256 text NOT NULL,
 approval_ref text NOT NULL, rights_ref text NOT NULL, status text NOT NULL,
 remote_media_id text, remote_status text, last_attempt_utc timestamptz,
 attempt_count int NOT NULL DEFAULT 0, version bigint NOT NULL DEFAULT 0,
 created_at_utc timestamptz NOT NULL DEFAULT now(),
 UNIQUE(destination,account_ref,campaign_ref,content_sha256)
);
CREATE TABLE outbox (
 id uuid PRIMARY KEY, publish_intent_id uuid NOT NULL UNIQUE REFERENCES publish_intents(id),
 next_attempt_utc timestamptz NOT NULL, locked_until_utc timestamptz,
 last_error_class text, created_at_utc timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE metric_snapshots (
 id uuid PRIMARY KEY, publish_intent_id uuid NOT NULL REFERENCES publish_intents(id),
 metric_name text NOT NULL, measurement_window text NOT NULL, availability text NOT NULL,
 metric_unit text, metric_value numeric NULL, platform_definition text,
 captured_at_utc timestamptz NOT NULL, UNIQUE(publish_intent_id,metric_name,measurement_window,captured_at_utc)
);
CREATE TABLE event_history (
 id bigserial PRIMARY KEY, trace_id text NOT NULL, entity_type text NOT NULL,
 entity_id uuid NOT NULL, previous_state text, next_state text NOT NULL,
 actor_ref text NOT NULL, reason_code text NOT NULL, payload jsonb,
 created_at_utc timestamptz NOT NULL DEFAULT now()
);
