# Pre-build quality, reliability and failure-prevention plan
**Intent:** make errors observable, bounded, recoverable and prevented before unattended publishing. No engineering plan guarantees zero failures. Treat errors as domain-specific: false negative highlight, false positive, truncated context, bad crop, mis-caption, invalid upload, duplicate publish, missing metrics, money/rights/security faults.

## 1. What “0.0001%” actually demands
0.0001% incident probability is **one failure in a million eligible operations**. A test set of 100 successful clips cannot demonstrate this. If a random independent test shows *zero failures* in `n` trials, a rough one-sided 95% upper bound on the failure probability is `3/n`; even **3,000,000 zero-failure trials** would only support an upper bound of roughly 0.0001% for a *well-defined binary failure type* and stable operating conditions. Clips, games, models, and platforms are non-IID, so a more realistic practice is to set **separate measurable SLOs for each failure class** and require continuous audit/rollback. Do not collapse subjective editing quality and infrastructure uptime into one fake aggregate percentage.

## 2. Validation gates
| Stage | Deterministic gates | Independent editorial / human checks | Fail path |
|---|---|---|---|
| Ingest | source consent, codec/PTS valid, duration, checksum, no gaps | sample visual/A-V sync audit | block source or reingest |
| Detect | score normalized, valid window, no overlap conflict, provenance | human event recall sample and frame evidence | change detector or hold |
| Cut | start/end in bounds, silence/sentence align, minimum useful context | buildup + climax + resolution complete | bounded re-plan; human review |
| Edit | EDL schema, no crop contradictions, caption safe area, permitted effect | gameplay HUD/facecam visible, pacing and sound intentional | reframe + rerender max 2 attempts |
| Machine QC | ffprobe output, duration, FPS/aspect, loudness, black/freeze frames, no empty captions, perceptual duplicate | accessibility and final playback random audit | discard bad render; no publish |
| Editorial QC | evidence source exists, rubric complete, quality model independent where feasible | watch **rendered** media, compare to source highlights | fail closed to human |
| Publisher | rights, OAuth, quota, account scopes, idempotency, remote status | publishing preview/approval until empirically safe | HOLD, do not blindly retry |
| Analytics | authenticated post ID, metric type/units, sampling time, missing-data flags | audit suspicious step changes | do not change model on stale/incomplete metrics |

## 3. Failure-mode register / executable proof ideas
| Risk | Prevention | Test fixture or injected failure | Release consequence |
|---|---|---|---|
| Source capture without rights | consent/version/expiry record and entitlement check | source with revoked consent | HARD HOLD |
| Public URL redirects into internal network / SSRF | allowed hosts + DNS/IP egress policy + no metadata IP | localhost, link-local redirect, rebinding | HARD BLOCK |
| Incorrect livestream access assumptions | platform API adapter capability checks; permitted route only | denied Twitch editor token; YouTube bot verification | fall back to uploaded authorized asset |
| Stream disconnect loses opening of event | rolling segments + reconnect/backfill marker | drop network 10 seconds at peak | HOLD incomplete window |
| A/V PTS drift | timestamp normalization, ffprobe sync | synthetic shifted audio 700 ms | fail QC |
| Clip starts after hype | pre-roll + human boundaries | sudden peak after silent buildup | reject truncated event |
| Clip stops mid-reaction | post-roll + event end detector | streamer screams then punchline 5 s later | reject incomplete |
| Flashy scene cut mistaken for highlight | use speech/chat/motion signals and review | menu/loading and scene changes | false-positive count |
| Quiet exceptional moment missed | visual candidate fallback | visual-only win, muted mic | false-negative count |
| Multi-language ASR gibberish | language ID + confidence / no forced text | English/Hinglish slang, crowds | hide uncertain text, manual |
| Subtitle time shifted | word-level align plus render diff | captions 400 ms early | QC reject |
| Crop cuts facecam/HUD/crosshair | semantic ROI and safe-zone checks | split-screen multi-entity 16:9 | QC reject |
| Slow motion misrepresents event | edit policy prohibits material distortion | action speed critical to meaning | QC reject |
| Fictitious hype/title/quote | grounded text, evidence pointer, unsupported→null | “million-dollar win” prompt with no evidence | QC reject |
| Malicious stream chat injection | numeric aggregates not raw chat; sanitation | “ignore earlier instructions” in chat | no change to system prompt |
| Prompt injection in captions/source filenames | strict source as data role; tool sandbox | fake system command in transcript | no privileged action |
| JSON plan invalid/out of bounds | Pydantic strict schema, allowlist ops | negative end, NaN, overlapping trims | deterministic error |
| Same model self-marks perfect | independent QC model/rubric + spot audit | intentionally bad EDL submitted | QC must catch |
| Revision infinite loop | supervisor max 2 revisions, time/cost budget | models disagree each pass | human / DEAD_LETTER |
| 2 sources competing for compute | fair scheduler and semaphore limits | 5 heavy videos simultaneously | no source starvation |
| Cloud CPU/RAM exhaustion | admission control + spill queue | constrained 2 OCPU/12GB benchmark | controlled HOLD, no OOM cascade |
| API 429, token expiry | retry-after, jitter backoff, token refresh | quota exhausted mid-job | delayed not discarded |
| Posting race / double publish | unique idempotency key + remote reconciliation | timeout after remote accepted first post | exactly one remote post observed |
| Token or account invalid | preflight and consent-aware reauth | 401 on upload | hold and alert operator |
| Wrong-account upload | immutable account routing and owner approval | two accounts mixed | HARD STOP |
| False “published” result | poll remote media status and persist ID | API accepts but remote processing fails | remain unconfirmed |
| Delete source before recovery | retention, backup and lifecycle states | upload succeeds but metrics fail | source retained as policy |
| Analytics counts mislabeled | units, source field, UTC and freshness | remove retention field from API | NULL, no invented curve |
| Feedback overfits 5 clips | holdout + minimum event count + confidence intervals | random metrics with spuriously high lift | no production update |
| Viral trends change suddenly | drift detection, review sampling | new game/format distribution shift | return to human review |
| Security/secrets exposed | vault/permissions, secret scanning, logs scrub | canary token in debug log | incident severity BLOCKER |
| Licensing conflict after edit | source rights and stock/audio license provenance | third-party sound without reuse license | no post |
| Unavailable API models | provider-level circuit breaker and fallback, quality check | force 503 provider outage | reroute or human HOLD |
| Unauthorized billing spike | per-provider guardrails, hard pause | spike 10x token usage | alert + safe stop |

## 4. KPIs measured from actual labels
- **Selection:** event recall; precision at candidate threshold; event boundary absolute error; complete-event rate; time from event peak to clip-ready (p50/p95); early-cut & late-cut percentages.
- **Edit:** average blinded human quality grade (predeclared 0–4 rubric), crop/safe-zone error, subtitle WER, subtitle sync error, source-to-render continuity, final video decode failure rate.
- **Review:** false-approval rate and false-rejection rate against human-labelled bad/good clips; inter-rater agreement; failure reasons.
- **Publishing/ops:** confirmed posts / approved posts, duplicate remote IDs, 429s, queue age, job recovery after restart, 24h backlog and per-feed stream dropout.
- **Analytics:** % posts with valid snapshots at scheduled checkpoints, field coverage, % unsupported claims, model-update holdout lift with uncertainty.
- **Rights and security:** 0 unauthorized posts (hard target), critical-severity bugs open before launch = 0; incident review included.

## 5. Release gates (proposed thresholds, not observed outcomes)
**Gate 0:** 30+ rights-cleared test videos, at least 10 no-event negatives, labels and source provenance present. All auth/rights/code-scanning unit tests pass.

**Gate 1 (recorded mode):** 100% valid output decodes on fixture set; 0 invalid timestamps and no severe crop clipping in human-reviewed release sample; log actual selection precision/recall and edit quality with uncertainty, not a fabricated numeric guarantee.

**Gate 2 (live single stream):** successful rights-authorized stream ingest, reconnect and segment gap observation, safe source URL, no duplicate candidates, actual end-to-end rendered preview.

**Gate 3 (publish):** private/draft test publish to each platform where permitted, remote ID and final state confirmed, duplicate retry injection passes, quota and account-token behavior recorded. Human must approve each external post until stability is demonstrated.

**Gate 4 (controlled autonomy):** two+ independent human raters for audit subset, preset false-approval ceiling, rolling drift test, emergency switch and manual downgrade to draft mode. No assumption that a handful of good clips proves rare failure absence.

**Gate 5 (15 sources):** 1 → 2 → 5 → 15 load fixture with **real measured** CPU, ARM compatibility, memory, disk, network, API use, queue backlog, stage p95 and cost. Fail if any hard guarantee breaks. Scale hardware/offload workers rather than silently remove features.

## 6. Incident policy
Priority P0: rights leak, wrong-account publish, duplicated external publish, security breach, irreversible data loss → stop publishing immediately, preserve evidence and notify. P1: invalid render, wrong subtitle/crop, lost highlight → isolate stream/job and hold release. P2: model speed/cost drift, delayed analytics → queue and alert; don't improvise unsupported model facts. Every incident generates a regression test, root-cause owner, corrective action and verified closure.
