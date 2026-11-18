# DATA CONTRACTS — IMPLEMENTATION-READY SCHEMA OUTLINE

## Standard rules
1. All contracts have `schema_version`, stable `id`, `created_at_utc`, `trace_id`, `source_id`/`media_id` where relevant, and `provenance`. Milliseconds are integers. Never mix relative source timestamps with wall timestamps, percentages with 0–1 fractions, or presentation timestamp units without conversion.
2. `unknown` = JSON `null` and distinct from `0`/false. Confidence is an estimate backed by evidence, not permission to invent links or captions. `evidence_refs` must be valid source segment/frame/audio ids when asserted.
3. State is database-owned with optimistic version and append-only event log. Agents do not rewrite long-running job memory in natural language; maintain compact typed state and reread sources on demand.
4. JSON schemas in `contracts/` illustrate minimum validations, **not** guaranteed production schemas or direct GitHub repo schema compatibility. Extend with migrations/versioning and validate using real code. No shell commands or arbitrary filesystem path strings supplied by LLM.
5. Model output must be parsed, schema validated, semantic constraints tested (source length, clock epochs, rights, media operations), and rejected if unsafe, regardless of whether it parses as valid JSON.

## Key entity relationships
`Creator` 1→N `AuthorizedSource`; `AuthorizedSource` 1→N `CaptureEpoch` 1→N `Segment`; `MediaAsset` references authorized source and immutable checksum; `MediaAsset` 1→N `CandidateEvent`; `CandidateEvent` 1→N `EventRevision`/`EditPlan`; `EditPlan` 1→N `RenderedAsset`; each `RenderedAsset` → `QCAudit`, optional `Approval`, 0→N `PublishIntent`; each confirmed `PlatformPost` 1→N `MetricSnapshot`; `PolicyVersion` links all inference decisions and experiments. `Consent/License` attaches to creator, asset, destination and derivative/use rights; separate `LicenseAsset` for fonts/music/B-roll.

## Suggested API surface
- `POST /v1/media/uploads/initiate`, `POST /v1/media/uploads/complete` (with hash and authorized rights record).
- `POST /v1/sources`, `POST /v1/sources/{id}/start|pause|stop` (operator authenticated).
- `GET /v1/discovery?platform=&region=&game=&type=top|trending_live|trending_video` with provenance and freshness.
- `GET /v1/jobs/{id}`, `GET /v1/events/{id}`, `GET /v1/events/{id}/evidence`.
- `POST /v1/events/{id}/edit-plans`, `POST /v1/edit-plans/{id}/render`, `GET /v1/rendered/{id}/qc`.
- `POST /v1/rendered/{id}/approve|reject|repair`, `POST /v1/rendered/{id}/publish-intents` (human approval or verified guarded policy only).
- `GET /v1/publish-intents/{id}/status`, `GET /v1/metrics/{post_id}`, `GET /v1/experiments`, `POST /v1/policies/{id}/propose|promote|rollback`.
- `GET /v1/health/ready`, `/health/live`, `/health/processing`, `GET /v1/audit?trace_id=`. No public unauthenticated mutating endpoints.

## Error contracts
All external endpoints return a typed `Problem` with stable `code`, human-readable message, stage, trace ID, retryable flag, retry_after_utc, relevant provider/account and safe diagnostic id; NEVER include raw access tokens/cookies/URLs. External-provided error text is logged sanitized and not executed. See `contracts/error.json`.

## Contract examples
`contracts/event_candidate.json` (source-relative timing, feature evidence, proposed events), `contracts/edit_plan.json` (editor intent not FFmpeg commands), `contracts/qc_result.json` (hard gates vs editorial scores), `contracts/publish_intent.json` (rights/account/approval/outbox), `contracts/metric_snapshot.json` (unavailable metrics explicit). These are P0 schemas; extend with actual data model and align with DB migrations.

## Database correctness choices
Use PostgreSQL JSONB for rich evidence only where structured columns insufficient; normalized status/state, unique intent constraints, foreign keys and transactionally written outbox are necessary. Index by source/clip/status/time, and capture UTC timestamps plus source-relative offsets. `schema.sql` contains a *starter* schema showing the most important relational constraints; production migrations must add user/team/account OAuth separation, source licenses and all nullable metadata. SQLite can be adequate for a single-owner early stage, but design migration path to PostgreSQL before 15 sources/parallel publishers.

## Event and edit constraints
- Event input: source stream exists and is authorized; `0 <= context_start <= onset <= peak <= resolution <= context_end <= media_duration`, with cross-epoch cases explicitly split; if an event is nonstandard, record `structure_exception` and evidence rather than fabricate stages.
- Edit plan: `source_start_ms >= 0`, `source_end_ms > source_start_ms`, ordered and in range, crop rectangles within source; no blend of different source identities without explicit multi-source montage; text overlays have safe zones, no arbitrary URL or executable expression.
- QC result: hard gate list is machine measured. Model may only add a suggested editorial score/reasons; a `hard_failed` result cannot be changed to pass by LLM. State coordinator maps results to pass/fix/reject/human.
- Publish intent: created only after required approvals and valid permissions; remote processing may remain unknown, use reconciliation; actual user-visible 'published' requires remote ID + status.
- Metrics: recorded with `source_metric_name`, unit, interval, platform, retrieval timestamp and explicit availability.
