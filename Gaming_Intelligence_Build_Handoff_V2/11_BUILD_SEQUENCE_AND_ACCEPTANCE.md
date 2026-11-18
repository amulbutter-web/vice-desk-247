# BUILD SEQUENCE — EXPERIMENTS, DECISION GATES, ARTIFACTS AND ACCEPTANCE
## Operating rule
The user requested the research and engineering plan **before** the full automation. An implementation agent should build after authorized instruction, not silently deploy or post to real accounts based on this document alone. Research is not a substitute for tests. Don't assume a calendar promise; tasks below are sequenced by dependency. Keep all full-product features in the backlog even if early phases use one source.

### Phase 0 — SOURCE FREEZE, PROVENANCE, DECISION REGISTER
**Input:** original GPT and Claude transcripts, all Manus artifacts and the research package. **Do:** inventory source files with hashes, read in required GPT → Claude → Manus order, extract exact user commitments and changes; mark unavailable/contradictory assertions; run current platform/rights/API/price preflight; define owner-auth, budget ceiling and authorized test media. **Deliver:** signed source map, requirements issue tracker, license/rights registry, selected initial fixtures and unverified list. **Gate:** all must-have requirements have IDs and owners. No '17 verified links' claims without reconciled 17 source identities.

### Phase 1 — REPOSITORY AND MODEL BAKE-OFF
**Input:** PeakCut pinned SHA, OpenShorts, the two SupoClip candidates, FFmpeg/scene/ASR and selected video judges. **Do:** inspect licensing/maintainer/code security, run tests in disposable isolated env, sample outputs on same *rights-cleared* gaming footage, measure benchmark. **Deliver:** test logs and data, ranked module-level choices, dependencies, accepted licenses, rejected candidates with reasons, verified cost/quota and model capability list. **Gate:** no full architecture lock-in until a chosen baseline meets basic input/render/QC viability.

### Phase 2 — E2E RIGHTS-CLEARED UPLOADED VIDEO
**Input:** owner-supplied local game footage with labeled events. **Do:** ingest/probe, ASR, visual sampling, candidate scoring, narrative boundaries, creative edit planning, render, machine QC, human/video QC and preview dashboard. **Deliver:** real source and playable vertical MP4s, event/timecode JSON, actual inspected frames, independent human pass/fail, empty-state/no-highlight behavior, rerun consistency and drift data. **Gate:** 20+ labeled cases, no catastrophic rights/codec/clock failures, active coverage of quiet action and extended buildup; improvement comparison to baseline.

### Phase 3 — ONE AUTHORIZED LIVE SOURCE
**Input:** creator-owned/approved live push or official platform native clipping as appropriate. **Do:** buffer with correct pre/post, tolerate disconnects, generate actual candidate event and preview while stream continues, prioritize live over batch with fair resource reservation. **Deliver:** source-to-clip latency distribution, 1–2 hour controlled session logs, permissions, complete event reconstruction after reconnect. **Gate:** output judged on real game events; no arbitrary stream capture assumptions; no cross-source mix-ups.

### Phase 4 — INDEPENDENT QUALITY, EXPERIMENTAL EDITOR V2
**Input:** baseline + alternative crops/judges/effects and human ratings. **Do:** implement machine output gates and actual-video independent judge, record evidence and targeted repair; compare creative variants, improve framing for HUD/facecam and edit narrative. **Deliver:** paired baseline/variant clips, blinded editorial rankings, detailed failure analyses and improvement decision. **Gate:** editor-level improvement on holdout, no new safety regressions; no black/frozen/unreadable release.

### Phase 5 — REAL CONTROLLED PUBLISHING
**Input:** operator-linked professional IG account and YouTube OAuth, documented source rights. **Do:** create intent, prepare platform-specific file, explicit human approval, private/test publishing and poll until confirmed, missing-token/quota tests, remote ambiguity reconciliation. **Deliver:** actual remote IDs, statuses and audit events; screenshots/screenshare only for UI proof when privacy appropriate; no unauthorized public posting. **Gate:** zero simulated publish successes, no duplicate post in crash tests and correct-account verification.

### Phase 6 — METRICS AND CLOSED-LOOP IMPROVEMENT
**Input:** confirmed posts and authorized analytics. **Do:** collect metric availability, age-matched cohorts and clip attributes, offline policy proposal, holdout/canary, feedback loop and explicit rollback. **Deliver:** real dated metrics and definitions, experiment record, change verdict and evidence of no leakage. **Gate:** one measured end-to-end learning example, not merely an analytics dashboard.

### Phase 7 — ORACLE OPERATION AND SCALE
**Input:** actual OCI allocated ARM VM, baseline measured costs. **Do:** Docker/systemd security/restarts/backups/alerts, 1→2→5→15 concurrent rights-cleared streams, source fairness, complete event coverage and stream-quality tests, cost/egress/account quota. **Deliver:** OCI architecture diagram, all benchmarks including failure modes, 24/7 recovery/runbooks, honest scale pass/fail and external workers if needed. **Gate:** do not declare '15-stream operational' until each active feed's ingest/event throughput and the total media queue meet selected objective.

### Phase 8 — GUARDED AUTONOMY, MAINTENANCE, COMPETITIVE EVOLUTION
**Input:** measured QC against unseen clips and stable authenticated accounts. **Do:** shadow decisions, manual sample audits, owner-controlled release policy, canary new models, periodic repo/security and platform change checks, continuous incident review, opt-in additional sources/providers. **Deliver:** recurring reliability/creative outcome dashboards, alerts, recovery drills, safe emergency stop and periodic evaluation reports. **Gate:** owner explicitly accepts auto-publication and its rights/quota/cost configuration. Keep a reversible safe mode.

## Gates by artifact (mandatory deliverable template)
Each phase report should have 1. source files and pinned SHAs, 2. changes and exact code paths, 3. installation commands, 4. tests executed plus logs, 5. measured real-media outputs, 6. pass/fail/skip, 7. security/license/rights, 8. latency/cost/throughput, 9. known issues and rejected alternatives, 10. rollout/rollback and next gate, 11. user approvals required (only if necessary). Do not erase a failing measurement to appear 'complete'.

## Decision boundaries
The agent may choose implementation details that preserve behavior (queue, library, CSS, data adapter). It must seek approval before: paying for a service/VM, connecting live personal accounts, publishing nonprivate content, scraping restricted resources, deciding to drop one of the two modes, dropping the 15 active-stream target, using code with restrictive license incompatible with intended deployment, or substantially reducing quality gates. Optional features like lip-sync/B-roll can be deferred with evidence, not silently promised.

## Acceptance matrix (high-level)
- **Source quality**: stable authorized capture, no known segmentation timestamp overlap/holes without detection.
- **Highlight quality**: an event missed because it was quiet should be detectable in silent-clip fixture tests; a positive must contain at least the essential action and narrative context.
- **Editor quality**: unbiased side-by-side study vs baseline with editor preference and HUD/facecam failure logs.
- **QC reliability**: hard-gate failures never publish; editorial reviewer calibration on human-labeled negatives.
- **Platform honesty**: real remote confirmed status, correct account, scoped rights, no duplicate effects after ambiguous timeout.
- **Operational**: queue recovers after simulated worker restart and loses no approved renders, can restart host while owner devices off.
- **Scalability**: 15 independent source end-to-end test on proven hardware and provider quotas; not assumed free.
- **Learning**: one policy change promoted only through holdout comparison with a rollback.
