# Experiment-first build roadmap, oracle ops and go/no-go decisions
This is a **sequence**, not a promised timeline. The final product retains the 15-stream target; stages avoid committing to unsupported capacity or unsafe auto-posts.

## Stage A — Source preservation and decisive questions
A1. Treat user archive's GPT initial discussion as scope, Claude as quality/engineering correction, Manus as research inventory with incomplete reel media. Keep copy and hash, no source modification.
A2. Name the initial authorized source/account for testing; default personal recordings. Explicit rights and redistribution limits, planned Instagram/YouTube professional accounts. Keep credentials out of docs.
A3. Decide **testing-mode publishing** = draft/private human-approved; production autopublish separate gate. Determine permitted source route (Twitch native clipping, creator feed, file upload, authorized other platform API).
A4. Create reproducible labelled benchmark. Don't implement code until test success/fail conditions are written.
**Exit:** PRD frozen for initial tests; 30 fixture videos with labels; rights register; test accounts planned.

## Stage B — Technical bake-off, no architecture lock-in
B1. Clone/audit pinned PeakCut; verify license, dependency hashes, vulnerabilities, test runner, implemented providers and live adapter. Compare current upstream commit to pinned baseline and document deltas.
B2. Execute same uploaded-video test set in PeakCut, OpenShorts, SupoClip. Compare actual clip completeness, crop quality, subtitle WER, speed and hardware footprint. Concat and editor MCP modules remain optional until they outperform FFmpeg on specific functions.
B3. Provider competition: Gemini vs vision-capable xAI/open model on game-event judge; Sherpa vs faster-whisper/WhisperX on multilingual ASR; DeepSeek/Groq/Gemini on structured text; independent **rendered video** quality judge.
B4. Implement only narrow interfaces for top two candidates; store baseline score/cost and failure examples.
**Exit:** scored matrix + winning combination backed by fixtures; documented fallback for each selected model.

## Stage C — Recorded-video production-quality loop
C1. Authorized file/URL validation + ingest normalization and immutable source metadata.
C2. Candidate generation + event boundaries + typed edit planner + FFmpeg render + subtitles + source-to-render evidence map.
C3. Machine QC + different-model vision QC + at-most-two revise loop + human approval UI. Keep manual editing/export if final AI QC not high-confidence.
C4. Add full logs, per-stage cost/latency/recall and a regression fixture for every serious error.
**Exit:** real rendered media on labelled test set, not sample JSON or dummy screenshots.

## Stage D — One real authorized live channel
D1. Native Twitch Clip API / approved creator input route test; if clip-length mismatch, permitted rolling ingest route.
D2. Rolling 60–120 sec pre-event context (tunable by measured delays), post-event capture, reconnect logic and time-base synchronization.
D3. Perform on actual live feed with incomplete events and delayed peaks; show p95 time to preview and failures; never infer rights from live URL.
**Exit:** video clip ready from live, with automatic safety QC and human approval.

## Stage E — Publishing and analytics gates
E1. Register/inspect Meta professional account OAuth permissions, public media URL, available quota endpoint, container processing state and exact media ID.
E2. Register YouTube OAuth and required API/audit status; verify test upload privacy behavior. Use explicit platform allowed test account.
E3. Add idempotent publish queue, remote post reconciliation, backoff, status and audit log; approval before public publishing.
E4. Collect metric snapshots with types/time; analyze as observational, use pre-registered A/B tests and confidence intervals, preserve holdout.
**Exit:** at least one verified post per platform **where authorization and app review permit**, plus retries and duplicate-block tests. No false success.

## Stage F — Oracle 24/7 and 15-stream capability
F1. Verify OCI account, available A1 ARM quota and actual instance type. Official Always Free equivalent is 2 OCPU and 12 GB, 1,500 OCPU-hours/9,000 GB-hours per month; availability and reclaim/idle policy require account check.
F2. Make container ARM64-compatible; minimal Docker Compose: API/UI, postgres, worker and reverse proxy with TLS; secrets volume and backups, admin auth/2FA where available, SSH locked down and firewall. Process supervisor and heartbeat; Telegram/Pager alerts.
F3. Run on 1 stream; increase to 2, 5, 15 with real workload and reserved render/ASR capacity. Track CPU, RSS, swap, queue age, disk retention, network bandwidth and external API rates. Free OCI may only run the control plane and low-load jobs; offload rendering/ASR or upgrade rather than drop quality-critical steps.
F4. Perform 24h endurance with deliberate network loss, restarts, 429s, ASR provider failure, full disk and remote publish timeout. Verify no double uploads, data loss or runaway billing.
F5. Add 24/7 monitored operation only after Gate 3/4 quality is met, operating permissions cleared and safe manual emergency stop implemented.

## Decision checkpoints user should review before autonomous coding
**D0:** Authorized sources? (default owned/explicitly consented).  **D1:** Which adapter wins controlled tests?  **D2:** What quality rubric and minimum acceptable false-approval ceiling?  **D3:** What is the hard monthly spend cap, API token limit and publishing quota?  **D4:** Which accounts can be automated legally?  **D5:** Load-test says hardware enough for 15? If no, approve scaled worker architecture.

## 24/7 operations essentials
`healthz` for API, `readyz` for downstream dependencies, `/metrics` for CPU memory/disk/network/queue, failed state alerts, read-only status dashboard, backups, restore drills, log rotation, secret scanning and clear manual kill switch `PUBLISH_ENABLED=false` default. On API outage/restriction, do not circumvent platform checks; preserve drafts for review. On worker restart, replay durable jobs only after locking/transition reconciliation.

## Source-truth cautions worth preserving
- Prior 21/21 tests in Manus = previous harness only; rerun with own environment and SHA.
- 50-vs-100 Instagram daily publishing references conflicted in original research; read authenticated actual API quota and conservatively throttle.
- The user archived Instagram export covers **captions/links**, not recovered reel MP4/audio. The 168 Reel shares are an intake queue, NOT proof those Reel contents have been visually extracted.
- Duplicated final Manus attachments may carry the same SHA; dedupe on content rather than counting them as new evidence.
