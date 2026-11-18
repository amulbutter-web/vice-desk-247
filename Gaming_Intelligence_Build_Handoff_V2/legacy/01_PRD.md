# Product Requirements Document (PRD)
**Product:** Gaming Content Intelligence & Clip Automation (working title)  
**Scope:** A production-oriented system capable of live-stream and uploaded-video highlight discovery, professional editing, quality control, publishing and improvement from analytics. No project code or unattended deployment is authorized by this document.

## 1. Outcome and design principles
Enable rapid **high-quality and accurate** shorts from moment-rich gaming content with creator authorization, resilience on a cloud host, and data-driven improvement. Favor correctly bounded, engaging, complete moments over upload volume. User priority order: correct moment → compelling edit → valid review/supervision → actual platform publish → measurable learning → predictable operating cost. All key judgments and corrections should be inspectable, reversible and traceable.

## 2. Users and jobs
- **Operator:** register creator sources and permissions, set trend/creator discovery priorities, view pipeline health, review/reject clips, monitor posting and costs, inspect errors, audit analytics; later turn on guarded automation.
- **Creator/editor:** provide recordings/rights-authorized feeds; choose style preferences, language, framing and brand.
- **System workers:** process one source per isolated job with shared resource scheduling and cross-source deduplication.

## 3. Requirements matrix
| ID | Requirement / behavior | Priority | Definition of done |
|---|---|---|---|
| R01 | Live Gaming Intelligence page: selected top gamers from India, US and other regions plus a separate **trending-live/trending-video discovery** feed | P0 | Both lists load via compliant source APIs; each entry has provenance, freshness timestamp and authorization status |
| R02 | Target **15 simultaneous monitored live streams**, each with independent moment detection and clip job state | P0 target | Staged live load test at 1/2/5/15; store measured resource usage and 15-stream pass/fail. Not inferred from README |
| R03 | Uploaded Video Intelligence: file and authorized URL input; skip live monitor, share core pipeline | P0 | Same analysis/render/QC pipeline produces clips from local test fixtures |
| R04 | Rolling buffer + contextual event window; pre-roll, post-roll; missed connection recovery | P0 | Audio and video are aligned and start of highlight not truncated on 20 labelled fixtures |
| R05 | Candidate moment detection: sound, speech, gameplay visual changes and permitted platform chat metrics | P0 | Traceable scores with false positives/false negatives reported against labelled data |
| R06 | **Dynamic** start/end chosen on natural event boundaries, no forced 30-second clip | P0 | Per event, time bounds include buildup, peak, resolution; passes human-editor audit |
| R07 | Source and context metadata: streamer, game, timestamps, language, narrative, audio/video signals, rights | P0 | Fields have provenance pointers; unsupported details stay null |
| R08 | Editor-grade plan: 9:16, gameplay/HUD awareness, facecam tracking, game-action zoom, slomo where suitable, readable timed captions, music rights check | P0 | Deterministic FFmpeg render from typed edit decision list; no invalid cuts, offscreen subtitles or black-bar/crop errors in QC sample |
| R09 | Independent machine QC AND video-aware editorial QC, with bounded repair | P0 | Every published clip carries quality evidence; max 2 repair iterations; hard safety gates cannot be overridden by an LLM |
| R10 | Strong supervisor: release decision, halt/route/retry/escalation; human override and audit trail | P0 | Never publish failed, unapproved, rights-unknown or duplicate media |
| R11 | Titles/hooks/descriptions/hashtags with platform-safe limits and factual grounding | P0 | Text schema validated; no invented game events, identities, quotes or links |
| R12 | Instagram Reels + YouTube Shorts publishing, per-account quota, permission, retry, OAuth and post-status verification | P0 gated | Test accounts show media ID and verified publish status; no phantom success; quotas and rights enforced |
| R13 | Failure recovery and 24×7 cloud monitoring with health/alerts and dead-letter queue | P0 | Kill/restart network and workers on fixtures; no lost job, double post or endless loop |
| R14 | Storage cleanup only after remote success and retention threshold; resumable downloads/uploads | P0 | Data safely retained across restart; lifecycle runs without deleting undelivered drafts |
| R15 | Analytics: impressions/views, retention if available, interactions, posting time and clip attributes | P0 | Store metric definitions, sampled timestamps, access scope and source; no invented unavailable retention curve |
| R16 | Feedback learning: candidate model calibration, A/B metadata trials when platform-compliant, recommendations with uncertainty | P0 | Offline evaluation improves on holdout before deploying new weights; no 5-sample causal claims |
| R17 | Provider-swappable LLM/ASR/video-judge plus local fallback | P1 | Model adapters return same schema; switch models via config without changing workflow |
| R18 | Dashboard for approvals, batch review, experiment history, time-to-post, costs and alerts | P1 | Can operate and audit from mobile browser without laptop being on |
| R19 | Trend/creator prioritization and duplicate event clustering | P1 | Multiple creator views of same event detected and selection recorded |
| R20 | Scalable worker pool and optional GPU acceleration, with per-source fair scheduling | P1 | Can add compute without modifying contracts; fails gracefully when budget exceeded |
| R21 | Reel-reference research intake pipeline (metadata, permitted multimedia extraction, verified links and exact frame timestamps) | P2 research tool | Every finding records `source_url`, observed modality and confidence; no extrapolation from caption to invisible frame |
| R22 | Monetization/creator-service route and rights/contract tracking | P1 commercial dependency | Rights contract/account inventory exists before external monetization claims |

## 4. Original 15 responsibilities → implementation ownership
1 discovery: API-adapter job; 2 highlight detection: signal worker + model judge; 3 metadata: extraction worker; 4/5 edit: edit planner + rendering worker, parallel where safe; 6 editor supervisor: independent QC judge + rule gate; 7 titles/hashtags: text generation; 8 YouTube: publishing adapter; 9 Instagram: publishing adapter; 10 job/API/retry: orchestrator; 11 infra health: metrics/alerts; 12 lifecycle: storage worker; 13 analytics collection: scheduled connector; 14 engagement/retention segmentation: analyst worker; 15 feedback: controlled experiment/retraining logic. **No requirement implies a dedicated LLM for each responsibility.**

## 5. Nonfunctional and operational requirements
- **Continuity:** Recover from reboot/disconnect with job and source resume markers. Duplicate posting must be preventable even after timeout or partial response.
- **Latency:** measure ingest-to-candidate, candidate-to-preview, preview-to-approval and approval-to-publication; set actual SLO after trials, not an invented “instant”. Record p50/p95/p99 by stage and platform.
- **Isolation:** rights and OAuth credentials per publisher/source; never use GitHub-leaked API tokens; encrypt secrets at rest when feasible, limit file system and admin access.
- **Determinism:** input hash, commit, model/config versions, data lineage; typed handoffs; fixed retry budgets; external calls with idempotency keys/unique constraints.
- **Privacy:** use only creator-authorized streams/data; minimize retention of private chat/user handles; professional-account metrics only when authorized.
- **Costs:** prevent runaway inference/egress with per-account daily caps, resource admission and alerts. Quality-critical stages not removed solely for API savings.
- **Accessibility/edit polish:** captions legible on real phone-size preview and within platform-safe overlays.

## 6. Explicit exclusions and boundaries
- No guarantee of a 0.0001% error rate, “viral clips”, ₹40k–₹60k monthly revenue or 15 concurrent 1080p transcoding on a free Oracle VM.
- No unauthorized stream scraping, anti-bot circumvention, access to private Instagram Reels via exposed account data, use of leaked credentials or hidden/private comment-only links.
- Auto-publishing remains gated until actual tokens/scopes, permission/rights, quotas and platform testing are established.
- AI-written claims are NOT accepted as measurements, provenance, creator consent, auth or quota evidence.

## 7. Releases
- **R0:** offline rights-cleared video → good reviewed vertical clip; permanent evidence pipeline.
- **R1:** one authorized live source → production-style draft and preview.
- **R2:** controlled authenticated posting and post-confirmation, analytics, rollback/alerts.
- **R3:** 2 and then 5 concurrent streams, fair queues and performance tuning.
- **R4:** **15-stream target** on proven capacity; guarded autonomy, shadow audits, periodic human sampling.
