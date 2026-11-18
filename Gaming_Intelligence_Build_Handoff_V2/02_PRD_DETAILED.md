# FULL PRODUCT REQUIREMENTS DOCUMENT — GAMING CONTENT INTELLIGENCE
**Status:** target specification, not proof of implementation. **Product principle:** no silent loss of user-requested capability during optimization. Track each requirement ID to an implementation issue, real test and acceptance evidence.

## Users, jobs and permissions
- **Owner/operator:** watch creator discovery, trend sources, live workloads, clip queue, quality scores, platform connections, storage, costs, activity/audit logs; approve, revise, hold, pause, reprocess and ultimately enable calibrated automation from phone or PC.
- **Source creator/team:** opt in and authorize owned uploads, stream feed or official platform editor privileges; see provenance, crediting preferences, allowed uses and expiration/revocation.
- **Reviewer/editor:** inspect source context and final clip, make timeline edits, correct crop, fix subtitles, approve or reject with reason; create gold-label training/evaluation cases.
- **Automated pipeline:** process all chosen live sources independently, skip or queue pressure safely, recover without duplicates, never fake successful publishing.

## Product-level workflows
**Mode A / LIVE:** search and score sources → select top creators/trending lives → verify source authorization → create one monitored source state per feed → open permitted live adapter → timestamped rolling segments (video, audio and allowed chat metrics) → candidate generation (audio + visual + context) → clip-level contextual evidence → event boundary editor → cross-camera / per-source duplicate clustering → creative edit planner + renderer → machine QC → independent editorial/multimodal QC → bounded correction loop → approval policy → platform-specific ready asset variants → verified publish → post-publication analytics → evaluated feedback changes.

**Mode B / UPLOAD:** manual file or permitted URL → checksum and media validation → optional full-video indexing → same downstream candidate, context, editing, QC, publishing, analytics. No live source or rolling buffer. Input may be long-form VOD, highlight compilation, gameplay recording or creator-provided export. Provide multiple candidate clips and allow later replay.

**Competing-source rule:** two streamers' similar events may be independently valuable; deduplicate only if materially the same event and use a policy with editorial context, not by co-occurrence time alone. Never suppress another creator's valid highlight because the first stream was clipped.

## Features and acceptance specifications
| ID | Criticality | Feature and operator-visible acceptance |
|---|---|---|
| FR-001 | Must | Top gamers discovery: source platform, region, game, explicit ranking method/date, user-defined lists and authorization state visible |
| FR-002 | Must | Separate trending live and trending video discovery: provenance, popularity metric used and freshness; 'not available' instead of invented trend rank |
| FR-003 | Must | One-click add/remove/pause/resume creator/feed and editable priority, concurrency, retention and source rights controls |
| FR-004 | Full-target Must | **15 concurrent actively analyzed live sources**, with per-source isolation, fair queues and end-to-end clip outcome in repeat load tests; no '15 URL monitors only' substitution |
| FR-005 | Must | File upload and creator-authorized URL path with resumability, explicit limitations and shared core pipeline |
| FR-006 | Must | Live ingest with source-clock + wall-clock mapping, rolling pre/post buffer, reconnect, discontinuity flags and segment integrity |
| FR-007 | Must | Independently assess audio excitement, speech meaning, permissible chat rate, temporal visual events, UI/gameplay changes and cross-signal calibration |
| FR-008 | Must | Detect silent but visually impressive moments, gradual tension and aftermath; don't require multiple spikes simultaneously |
| FR-009 | Must | Accurate event category, onset, buildup, pivot, peak, resolution and contextual time ranges with confidence/evidence |
| FR-010 | Must | **Dynamic clip length**, multiple moments/segments where justified, source sync and natural scene/word/sound boundaries; adapt to each platform's limits |
| FR-011 | Must | Provenance: source media ID, creator, consent scope, exact timecode, language, location-independent UTC, model/prompt/version, input checksum, confidence |
| FR-012 | Must | Independent story/context integrity: clip must be comprehensible, not misleading by removing necessary lead-up or consequence |
| FR-013 | Must | Editor plan supports smart crop, gameplay/HUD + facecam + game object saliency, transitions, zoom, slow motion, speed ramps, cuts, captions, color/audio polish |
| FR-014 | Must | Creativity is conditional on clip; no template spam, unmotivated effects, distortions or fake excitement; fidelity preserved |
| FR-015 | Must | Subtitle diarization/timing/readability, optional multilingual captions, accurate names/game terms; no hallucinated speech |
| FR-016 | Must | Hook/title/metadata grounded in viewed/transcribed event, no made-up claims or uncredited identity; distinct per platform |
| FR-017 | Must | Machine post-render QC: duration, codecs, frame size, A/V sync, black/frozen segments, loudness/clipping, crop zones, subtitle safe area, duplicates |
| FR-018 | Must | Multimodal output-review judge sees actual rendered video/audio (or deliberate dense frames + audio) and references source event; not transcript-only |
| FR-019 | Must | Independent supervisor routes pass/fix/reject/escalate with structured reasons, severity and bounded fixes; never removes hard gates |
| FR-020 | Must | Human review queue with side-by-side source and output, trim handles, preview mobile safe areas, approve/disapprove, reason labels |
| FR-021 | Must gated | Instagram Reels publishing with supported IG account + precise login path/scopes, media-container status poll, duplicate prevention, refreshed caps |
| FR-022 | Must gated | YouTube vertical upload with OAuth, explicit `privacyStatus=private` during safe tests, metadata, resumption, processing confirmation |
| FR-023 | Must | Real publishing status / URL / ID, error context, quota throttle and idempotency ledger; zero false success by definition |
| FR-024 | Must | 24/7 cloud runtime with autosupervision, health checks, bounded queues, backpressure and alert delivery while owner devices off |
| FR-025 | Must | Cleanly handle API rate limit, provider outage, download loss, storage exhaustion, worker crash and partial process with visible recovery |
| FR-026 | Must | Raw/processed data retention and safe deletion conditions; nonfinal or unconfirmed uploads must not lose last recoverable artifact |
| FR-027 | Must | Actual platform metrics and their definitions/availability, snapshots at selected windows and attribution to content/edit decisions |
| FR-028 | Must | Feedback comparisons, controlled experiments, holdouts and model/version gating so strategy improves only when supported by data |
| FR-029 | Must | Anti-duplication: exact file hashes, near duplicate video/audio fingerprints, repeated source events, platform account uniqueness |
| FR-030 | Must | Audit trail for every job, decision and failed check, with replay into specified configuration without relying on model memory |
| FR-031 | Must | Platform/creator rights registry and suppression on expired/revoked permissions, no assumption that public video is redistributable |
| FR-032 | Must | Secrets management, authenticated operator dashboard, provider keys isolation, least privileges and input URL anti-SSRF checks |
| FR-033 | Important | Modular provider evaluation (Grok/xAI, Gemini, DeepSeek, Groq, local weights and other candidates) per task, not hype/brand |
| FR-034 | Important | Offline or low-cost fallbacks that maintain **quality gates** and queue work rather than silently publish lower-quality clips |
| FR-035 | Important | Visual event deduplication across streamers with credit/rights context and editorial override |
| FR-036 | Important | Content scheduling/priority to balance freshness and quality; current per-platform rate limits and owner policy |
| FR-037 | Important | Mobile-first controls, Telegram or equivalent notifications, kill switch, feedback for false positives/negatives |
| FR-038 | Research | Reels knowledge intake from original Instagram export, permitted video/audio, frame-by-frame resource identification and GitHub verification |
| FR-039 | Research | A/B test competitor implementations: PeakCut vs OpenShorts vs SupoClip vs components from additional repo shortlist |
| FR-040 | Commercial | Monetization options without earnings guarantees: authorized creator clipping service vs owned commentary-driven channels; track contracts, revenue/cost if applicable |

## Original fifteen functional responsibilities mapped cleanly
| Original role | Module / independent review |
|---|---|
| 1. Live monitoring/discovery | registry, `source_discoverer`, `live_ingestor` |
| 2. Clip moment identification | audio/visual/chat signal workers + `event_judge` |
| 3. Metadata extraction | source context, rights/author identity, ASR + vision context |
| 4. Editor A | creative edit planning, story, selected effects |
| 5. Editor B | crop/caption/action tracking and alternate render variant |
| 6. Editorial supervisor | `machine_qc`, independent `video_judge`, repair router |
| 7. Captions/titles/hashtags | metadata writer, grounded claims checker |
| 8. YouTube upload | YouTube publish adapter + verifier |
| 9. Instagram upload | Instagram publish adapter + status poll |
| 10. Workflow/API/error agent | deterministic orchestrator, retry policy, queue and alerts |
| 11. Cloud monitoring | OCI SRE probes, cost/resource telemetry, supervisor |
| 12. Storage cleanup | blob lifecycle worker, retention approvals |
| 13. Views collection | first-party official analytics connectors |
| 14. Audience performance analysis | analysis/experiment engine with metric provenance |
| 15. Feedback coordinator | policy version manager, offline evaluations, rollout/rollback |

Model calls are optional tools for 2/3/4/5/6/7/14. There is no reason to force LLM autonomy for 8/9/10/11/12/13; use deterministic workers. Preserve externally observable behavior even when implementation count differs.

## Editor/autonomy preferences
- Modes: `DRAFT_ONLY`, `HUMAN_APPROVAL`, `GUARDED_AUTOPUBLISH` (guarded not default). Post mode may differ by account and source.
- Owner sets style pack, source priorities, languages, captions, time-to-publish budget, cost cap, maximum repair attempts, platform schedule and retention.
- Queue must clearly show why a clip was not emitted (low story score, bad rights, corrupt source, wrong dimensions, quota, pending account scopes, duplicate, deliberate editorial reject).
- Human corrections automatically become *candidate evaluation labels*; they must not immediately retrain policy or leak into validation set.

## Quality ranking and trade-off policy
1. **Non-negotiable:** rights/authorization, security, factual integrity, valid published state, no harmful/corrupt media, no double publication.
2. **Primary optimization:** truly valuable highlights + complete boundaries + editor quality + strong independent review.
3. **Secondary:** freshness, latency, coverage across 15 sources, predictable cost and operational simplicity.
4. **Tertiary:** number of agents/API calls, fancy UI, speculative tools. Cost is still a hard practical constraint, not the overriding quality objective.

## Product invariants
- The same source input + versioned config yields comparable evidence; random LLM decisions recorded and replayable to the limit possible.
- A model's guess cannot grant rights, approve payment, assert API quota, set publish success or silently delete artifacts.
- Exactly once **effect** for publish per account/source/output revision to extent possible: local uniqueness + remote reconciliation; never promise mathematically exactly-once HTTP semantics.
- All human-meaningful cut times use a defined coordinate system (source-relative milliseconds, wall UTC, encoded stream PTS map) and preserve discontinuities.
- No metric called `retention` unless platform actually provides equivalent data; otherwise explicitly `unavailable`.
- No unmeasured claim of 'best model', 'viral', '99.9%' or '15-stream stable'.

## Out of scope or deferred *for initial release*, not deleted from full plan
- Unauthorized collection of stream playback or private Instagram messages, bypassing bot checks, leaked tokens; never build these as fallbacks.
- Universal content ownership transfer or copyright guarantees from creative edits.
- Training large foundation models from scratch.
- True automatic earnings / guaranteed platform monetization.
- High-cost generative lip sync and B-roll in initial media quality gates unless a measured use case improves actual gaming clips. Keep as optional candidates.
- 15 simultaneous full recompression workloads on an assumed free ARM VM without capacity measurements.

## Release outcomes, not calendar promises
**P0 demo-independent working path:** one full authorized video → actual reviewable vertical output; **P1:** one authorized live → clips and integrity evidence; **P2:** verified test-account posting + analytics; **P3:** 2 then 5 active feeds; **P4:** 15 actively processed sources and 24/7 guarded autonomy on proven scalable capacity. Every phase must pass quality and security gates. A staged first build does *not* authorize cutting final scope.
