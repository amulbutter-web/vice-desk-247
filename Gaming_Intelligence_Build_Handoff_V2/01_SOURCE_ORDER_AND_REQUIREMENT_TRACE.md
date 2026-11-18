# SOURCE ORDER, REQUIREMENT PROVENANCE AND CORRECTIONS

## I. ORIGINAL GPT: what was requested, without interpretation shrinkage
The shared GPT conversation is a transcribed voice discussion focused on a **live-gamers video project**, not the earlier unrelated DS, AI-learning, and Instagram access discussions. The owner later explicitly told Claude to skip those prior projects when defining the main product.

**G01 — dual discovery, distinct strategies:** selected top gamers globally (including India/US) **and** most-trending live streams/videos. A live-source registry must allow manual picks AND discovery/ranking. Trending is not synonymous with subscribed sources and cannot be replaced with a static list.

**G02 — 15 is a required full-product capability target:** 15 simultaneous live feeds, with each feed analyzed independently so one streamer cannot cause arbitrary cutting on another stream. Time-sensitive events can trigger multiple clips independently. **Do not relabel this as merely 15 URLs watched and one stream actually processed.** Prove 15 *active ingest + event analysis + workable output throughput* on suitable infrastructure, and benchmark free Oracle separately.

**G03 — event-bounded, dynamic duration:** 30 s / 60 s were examples; capture excitement onset, buildup, peak and resolution. A clip longer or shorter than those examples is acceptable if platform technical limits and editorial justification permit it. Native clip APIs with maximum 60 s cannot alone satisfy all events.

**G04 — editor-grade judgment:** cutting alone is insufficient. Automatic cuts, silence/filler removal when appropriate, timed captions, gamer/facecam zoom, gameplay-object tracking, selective slow motion, pacing, framing, motion and attention dynamics; these examples are **not** exhaustive. Prioritize creative merit over a static template. Do not miscrop game HUD or remove important evidence of the play.

**G05 — independent review / re-edit loop:** editorial supervisors communicate with editors and send specific correction instructions if the output fails. Parallel editing tasks are appropriate where beneficial; use deterministic render and typed edit decisions. Bounded retries rather than endless conversation.

**G06 — metadata and platform publication:** source-level context, reliable title/description/hashtags and publishing to Instagram and YouTube. Both outputs need provenance, idempotency, post-status checks and account-appropriate media specs. A clip must not be called 'published' when the API returned only a pending container.

**G07 — engineering control and self-healing:** workflow/API errors, infrastructure health, storage lifecycle, alerts. Run on cloud even with personal devices powered off. Oracle Free was a preferred bootstrap; it was never proof of enough capacity for 15 full video pipelines.

**G08 — detailed analytics feedback:** obtain real metrics, identify what content patterns performed well, and feed controlled changes back into detection, editing, title and scheduling policies. "Self-learning" must never mean blindly reinforcing views or inventing unexposed retention curves.

**G09 — separate uploaded-file/video-URL mode:** same downstream pipeline without live recording. The owner described it as secondary, not disposable. Good for quality baselines, slow-path work and creator-provided source files.

**G10 — production functionality, not a polished demo:** user expects genuinely working recording, clip production, access-controlled posting and server uptime; development should gather proof rather than claim passing based on mocks.

**G11 — 15 original agent responsibilities:** these are function *roles*, not a demand for 15 distinct model agents. See mapping in PRD. Optimize for modularity, speed, quality and verifiability rather than LLM count.

## II. LATER CLAUDE: what was corrected and strengthened
**C01 — don't optimize away quality to save API calls.** The user explicitly rejected an answer focused on API minimization rather than impact/quality. Multiple paid/free APIs acceptable if justified; compare providers by measured tasks, limits, failure mode, costs.

**C02 — the five critical jobs:** moment cutting/boundaries; polished editing; real-output review; supervisory correction; post-publication analytics. Engineering time should be weighted accordingly.

**C03 — deeper than 'avoid hallucinations'.** The user requested problems from dynamic/multi-agent coordination, branching, parallel windows, stale/missing context, correctness/completeness/precision, premature termination, repeated steps, tool interfaces, confidence and error propagation. Add global invariants, typed handoffs, state versioning, trace IDs and tests at every boundary.

**C04 — '0.0001% category'.** Read as exceptionally high caliber of thought, precision, creativity, research, testing and implementation—not a numeric guarantee. If discussing an error-rate metric, define denominator, independent samples, severity, confidence and realistic test volume; do not conflate.

**C05 — research-first selection.** Evaluate named or discovered repos and model providers, run code, test side-by-side with identical inputs, then choose/compose. PeakCut is a useful candidate but not unchangeable. DeepSeek LLM != DeepSeek mobile app; xAI Grok != Groq inference service.

**C06 — separate human/editor judgement and deterministic measurement.** A model can propose edit decisions and judge actual clips; code verifies inputs, bounds, codecs, keys, stats, permissions, retry counts, jobs, and state.

**C07 — vendor docs and papers are partial evidence.** Earlier Claude and Manus differed on some stats. The current primary source matters, paper domains do not automatically transfer to gaming quality.

**C08 — early human approval, gradually calibrated autonomy.** Real publishing follows verified rights/platform capability and production QC. No imaginary 99.9% guarantee from a short beta.

## III. RESEARCH ARTIFACTS: useful leads, limits, not feature authorities
**M01 — catalog:** the user separately recalled roughly 117/126 researched Reels, while the captured export and prior catalog counted **168 Instagram share entries**; these counts have not been reconciled into distinct watched videos. The prior report counted 179 Instagram export messages, 168 Instagram shares, seven explicit non-Instagram URLs. These are NOT 168 fully watched videos, not proven unique Reels, and not proof of hidden on-screen links.
**M02 — incomplete paused task:** the 'last 50 Reels' extraction was paused for credit exhaustion; do not write '50 full media analyses completed'.
**M03 — PeakCut audit:** prior Manus says 21 test groups passed at pinned SHA; tests covered narrower things than full real-world system. Re-test before fork adoption on current toolchain.
**M04 — 49 references / '17 verified' issue:** a final share labeled 17 sources, while longer report had 49 numbered references. They are different references/claims; no authoritative reconciled 17-row verification was available in the captured report.
**M05 — hidden audiovisual knowledge:** audio, flashes of GitHub handles, one-frame URLs and creator-hidden resources were not extracted from original export. Extraction requires the media itself, lawful access, frame inspection and independently found official/GitHub links, with 'not found' preserved.

## IV. SOURCE CONFLICT RESOLUTION REGISTER
| Conflict | Right treatment |
|---|---|
| '15 agents' vs Claude 'not 15 separate LLMs' | Preserve 15 responsibilities, implement as modular workers + selected reasoning calls; count and type determined by tests |
| 'No limit on clip duration' vs Instagram/YouTube specs, Twitch native clip max 60 s | Event duration unconstrained at planning stage; output adapted to actual destination constraints; no false truncation |
| 'Instant publishing' vs network and QC | Optimize and measure latency without skipping hard quality/rights gates |
| 'Free full-scale 15' vs Oracle 2 OCPU equivalent | Keep 15 full-scale goal, require scalable compute/offload when measured free capacity fails |
| 'Insta not restricted' vs platform copyright/originality | Treat legality, permission, uniqueness and API access as independent platform gates |
| 'Need 50 papers' vs material available | Label studies actually read, distinguish report quotes from independently checked paper methods |
| 'Claude research found 260 sources' vs available evidence | This is a claim in a prior reply, NOT an inventory validated by this package |
| Grok vs Groq | Two unrelated providers; never compare API types as interchangeable |
| 0.0001% ambition vs literal accuracy | Product excellence target; no numerical statistical accuracy guarantee |
| GPT original 'both modes' vs newer recommendation to start recorded input | Staged rollout changes first proof, not final feature scope |

## V. AVOID THESE ASSUMPTIONS
1. The game launch is exactly midnight India time: official Rockstar date alone doesn't verify local unlock timing.
2. 'Most trending' can be obtained through a universally authoritative one-call 'trending lives' API: discovery availability and bias vary by platform.
3. An unverified Instagram/GitHub resource shown in a reel was fetched or tested; the export did not contain the media.
4. All current accounts/API keys exist because prior voice discussion said 'perhaps already connected'.
5. A paper's agent error percentages, an editor's star count or a README's 'AI' is a benchmark result for *this* workload.
6. 'Quality' can be fully inferred from transcript, volume or motion—gaming has silent, visually critical moments.
7. The second independent LLM automatically eliminates correlated errors; calibrate with expert labels, source video and negative controls.
8. A smaller-than-one-percent error ambition can be tested from a few dozen clips.

## VI. BASIC EVIDENCE CLASSIFICATION
USER_SPEC (GPT/Claude), PRIOR_REPORTED (earlier agent/test claims), OFFICIAL_DOC (current provider documentation), REPO_DOCUMENTED (feature described, runtime unproven), TESTED_LOCAL (this build's pinned run with fixture logs), TESTED_AUTHENTICATED (real API + permitted account), BENCHMARKED (repeated labeled jobs with confidence intervals), PRODUCTION_PROVEN (operated real workloads and incidents). In all reports, choose the most restrictive accurate status and include last checked date.
