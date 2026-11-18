# IMPLEMENTATION AGENT DELIVERY CHECKLIST / DEFINITION OF DONE
The person or coding agent who builds this must fill these fields with actual proof. Use as a PR description and release template; do not claim 'complete' by checking conceptual criteria without outputs.

## A. User intent
- [ ] Read GPT project conversation then Claude discussion then Manus artifacts in requested sequence.
- [ ] All G01–G11 / C01–C08 and FR-001–FR-040 linked to code task, tests and owner-visible outcome.
- [ ] Distinguish 15 responsibilities from 15 LLM agents; full 15-stream target never silently dropped.
- [ ] Both live and uploaded-video workflows implemented, not a fake UI.
- [ ] 0.0001% category treated as rigor/aspiration, not an unearned reliability number.

## B. Research and licensing
- [ ] Baseline PeakCut pinned SHA, current license, security and dependency review recorded.
- [ ] Alternatives OpenShorts/SupoClip/others inspected and compared on SAME rights-cleared gaming fixtures.
- [ ] AGPL/commercial carve-outs/model/font/music/B-roll licenses cleared before reuse.
- [ ] Reels knowledge sources have video/audio proof before claiming visible or spoken links.
- [ ] Official API docs, quotas, account rights and current provider capabilities recorded with timestamps.

## C. Creative and video proof
- [ ] Event candidates include silent significant gameplay, not only audio triggers.
- [ ] Natural context boundaries with source PTS; no arbitrary 30 s fixed length.
- [ ] Gameplay and facecam crop preserve relevant HUD/action, even with scene cuts.
- [ ] Word-timed subtitles + audio quality reviewed on actual phone-sized output.
- [ ] Actual rendered video independently checked against source by both deterministic QC and calibrated editorial rubric.
- [ ] Bounded revision and human override; no endless loops.

## D. Security/reliability
- [ ] Source consent and rights checked per source/asset/use/account before capture/publish.
- [ ] IDs, timestamps, schema, durable state, versioned config and logs present.
- [ ] Worker crash/restart and network failure recovery tested; no duplicate post on ambiguous publish timeout.
- [ ] URL SSRF, input validation, secret leak and prompt-injection scenarios tested.
- [ ] Remote status and account identity proven; not success by 'HTTP 200'.
- [ ] Backups, restore, TLS, authentication, alerts, quota caps, disks and kill switch tested.

## E. User goals and scale
- [ ] Owner-approved real test-account publish on both platforms, with actual verified remote IDs.
- [ ] Metrics read via actual platform and unknown/unavailable values preserved.
- [ ] At least one controlled experiment shows valid recommendation/rollback, not invented virality.
- [ ] Run 1/2/5/15 source load test with CPU/RAM/disk/bandwidth, error and latency report; 15 must mean *actively analyzed and viable outputs*.
- [ ] OCI capacity reported honestly; alternatives given if free allocation is insufficient.
- [ ] No unsupported revenue guarantee or private-user scraping.

## F. Submission template
`Phase | commit SHA | rights-cleared fixture IDs | tests run | fail/pass/skip | sample video paths | measured quality | human-editor result | p95 latency | provider/account scopes | license clearance | S0/S1 issues | deployment/rollback | open decisions | next gate`.

**Release outcome must be one of:** `NOT_STARTED`, `RESEARCH_ONLY`, `PROTOTYPE_WITH_EVIDENCE`, `CONTROLLED_LIVE_BETA`, `CONDITIONAL_AUTOMATION`, `PRODUCTION_VALIDATED_15`, with explanation. Do not classify based only on a coding assistant claim.
