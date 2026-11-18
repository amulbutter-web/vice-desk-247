# EDITORIAL INTELLIGENCE, REAL CLIP QUALITY AND 0.0001%-CATEGORY ENGINEERING

## The exact quality brief
Treat each candidate as a story/event, not a random high-energy 30-second excerpt. Aim for **capture → comprehension → editorial motivation → professional render → independent verification → response to real audience feedback**. Distinguish game genres (GTA narrative scenes, battle royale clutch, racing close calls, tactical shooter wipe, exploration, character reactions, comedy, cutscenes), because loudness and chat spikes vary. A silent skillful event must be discoverable, and a streamer shouting over an uneventful screen must not automatically become a highlight.

## A. Candidate discovery: coverage before clever scoring
Collect features in aligned time windows: (1) transcription and semantic changes; (2) speech rate and prosody, not only volume; (3) game audio transients and musical context; (4) visual activity, camera movement and salient changes; (5) OCR/game-event UI clues, with confidence; (6) facecam reaction/attention; (7) legal platform chat velocity/emoji aggregation; (8) explicit creator markers or stream events where available; (9) trend/source priority and novelty. A **union of candidates** avoids missing silent impressive moments. Fusion and thresholds are learned on data with real negatives, not fixed guesses. No 'all three signals must spike' rule.

Important failure patterns: stream overlays, donation alerts, intro music, ads, black transitions, UI notifications, spectator-mode scene switches, game HUD popups, background voice chat, streamer shouting unrelated to gameplay, sudden camera cuts, fake excitement and troll chat spikes. Include these as labeled negatives. Avoid raw chat text in the LLM by default; numerical aggregates are often enough. If textual chat is needed for analysis, sanitize and treat it as adversarial data.

## B. Moment timeline and story completeness
Each event evidence packet must include `context_start`, `onset`, `build_up`, `peak`, `resolution`, `context_end`, plus uncertainty intervals for each where detection is fuzzy. The initial candidate may start after the action; **pre-roll** must recover the approach and the **post-roll** must show consequence/reaction. Do not force one clip duration. The edit planner can exclude dead time, but must keep action intelligible and avoid misleading montage. Underlying source ranges remain saved for human comparison.

Boundary rules: check words/phonemes and cut on appropriate silence/beat/scene boundary, but don't over-snap away an important shot; if action is mid-sentence, narrative content wins over pure silence; retain dialogue exchange if essential. Preserve chronological meaning; avoid apparent kill sequence from unrelated time positions. Handle scene or stream discontinuity as a hard warning. Compute cut timing with media PTS and versioned edit decisions, never unconstrained natural-language timestamps.

**Example**: streamer drives toward a stunt for 15s, airborne for 5s, barely lands and laughs for 8s. A simplistic audio peak detector selects 2s of laughter and calls it a viral moment. Correct expected output is a longer event with build-up, airborne stunt, landing and reaction; final length chosen by editor/format, not hard-coded. **Negative example**: excited scream during loading screen; don't clip without meaningful scene context.

## C. Automated editor — allow real creative decisions
Candidate editorial operations, if warranted by evidence:
- **Temporal:** trim, remove dead air, compress wait times while preserving chronology, story chapters, reaction beat, deliberately timed pause, J/L-cuts when audio rights and meaning allow.
- **Spatial:** game-centered crop, picture-in-picture facecam, split layout when multiple panels matter, animated crops/track ROI (face, vehicle, crosshair, on-screen HUD), avoid cutting important game clues and gauges. Gaming footage has more critical spatial cues than talking-head videos.
- **Motion:** subtle pan/zoom, kinetic scaling on action beats, selective slow-motion/replay on meaningful moves, smooth interpolation only when no action distortion is introduced, speed ramps that preserve intelligibility and causality.
- **Typographic:** timed word-level captions, confidence flags for ASR names/game lore, phrase emphasis tied to story, platform-safe areas, accessible color/contrast, multilingual support after accuracy checks; avoid hiding UI text.
- **Audio:** speech clarity, normalize but avoid pumping, peak limiter, correct stream audio/video sync, avoid intrusive SFX or unlicensed music. Silence can be editorially valuable.
- **Narrative:** a truthful hook early where possible; highlight question/answer or setup/payoff; attribution; do not invent an 'ending' or make fake montage facts.
- **Platform variants:** aspect 9:16 (or justified layouts), per-platform output rules, duration, caption safe zones, metadata and platform-specific bitrate/encoding checks.

Planner returns typed edit plan; validation rejects out-of-source time ranges, unsafe graphics, overlapping incompatible operations, unapproved external assets, absent licensing, excessive slowdowns, invalid dependencies and unsatisfiable tracks. **Render with media pipeline, not LLM-generated shell commands.** Evaluate GPU vs CPU effects against OCI resource budget.

## D. Multimodal QC and independent supervision
**Machine QC hard gates (no opinion):** media decoded and final mux complete; correct codecs/container/profile per destination; dimensions, frame rate and duration; no unexpected black/frozen intervals, encoder failure, audible clipping, long unintended silences, A/V drift; source boundary in range; subtitle times visible within real safe overlays; no unsafe cropped text/HUD; file size and hosted URL valid when required; checksum and duplicate check; rights and account permission valid. A failure is a **STOP**, not a reason to ask an LLM to override.

**Human-calibrated editorial review:** compare rendered output with source video/audio and event labels (not transcript alone). Use rubric 0=fail,1=weak,2=acceptable,3=excellent per dimension:
1. Is this genuinely compelling gameplay/context (not mere loudness)?
2. Does the clip begin early enough to explain what is happening?
3. Is the payoff, resolution/reaction complete? Any misleading montage?
4. Are pacing, pauses, cuts and transitions coherent and motivated?
5. Is subject/facecam/object framing correct throughout (HUD/crosshair safe)?
6. Are speech and on-screen captions accurate, timed and readable?
7. Is audio/video/graphics technically professional and platform-safe?
8. Are hook/title/description accurate and worth clicking without misinformation?
9. Would an expert editor voluntarily publish it without rework?
10. Is the creative treatment meaningfully different from a generic auto-caption template?

Rubric must retain evidence, per-dimension reason, source timecode and suggested targeted repair. Store `judge_model`, separate `editor_model`, source/output hashes and full video sampling strategy. Independent reviewer does not certify its own accuracy; compare with human gold labels and test inter-rater agreement. No single weighted score can overrule rights/technical failures or hard safety constraints.

**Example repair routing**: 'At 00:12 the vehicle leaves crop, facecam remains unnecessarily large; reduce facecam inset and shift crop toward vehicle until 00:17; do NOT change opening/ending' → targeted plan revision → rerender → full machine QC + editorial QC. At most two automatic repairs by default; after that show human a concise diff or reject, preserving previous versions.

## E. Benchmark suite: same source, independent blind review
**Fixture matrix (suggested minimum for initial comparisons, not proof of perfection):** 40 rights-cleared clips across 4 game styles; 10 quiet-but-exciting events; 10 noisy false-positive events; 10 long buildup/payoff episodes; 10 multi-speaker/facecam and HUD-sensitive scenes; 10 stream discontinuity or network corruption cases; 10 multilingual or poor ASR, plus 10 exact/near duplicates. A fixture can cover multiple categories, but record coverage; do not pretend 40 clips cover every rarity. At least 2 human editors label event bounds and rank output; adjudicate disagreements.

**Task-level metrics:** detection precision/recall/AP at event IoU thresholds, event onset/end median and p95 error, story completeness rated by editors, silent-highlight recall, false-positive triggers per hour, edit quality preference by blinded raters, crop tracking success, blocked-HUD fraction, subtitle WER and word-alignment error, readability/safe-area pass, technical QC failure rate, regeneration rate, review cost, production latency and E2E completion. Include cost/LLM calls but not as sole winner criterion.

**A/B competitor comparison:** pin repo SHAs, configs and models; feed identical fixed inputs to PeakCut, OpenShorts, SupoClip and selected modular combination. Blind-review random order; report `n` and CI, worst-case failures and examples; inspect AGPL/commercial clauses before porting code. An approach may win editing but lose live processing; adopt *component-level* strengths rather than declare one magic winner.

## F. The 0.0001% aspiration is about discipline
This phrase is not a measured probability. Operationalize as completeness and traceability: every required feature has a test; every AI judgment has structured evidence; every stage has a failure taxonomy; every hard gate fails closed; all top performance candidates get adversarial review; source links have provenance and version; options are compared objectively; every rollback has tested recovery. Don't market '99.9999%' from no data. As a mathematical illustration **only**, observing zero failures in ~3 million independent trials would be needed to place a one-sided 95% upper bound near one failure in a million; the owner's aspiration is not even a literal failure-rate specification.

## G. Test conditions and the first editorial release gate
Before private/test-account publication: capture at least 20 fully labelled, rights-cleared clips with source-window evidence and pass all deterministic export gates; obtain and record independent human reviewer pass/fail and reasons on every clip. Before guarded publishing: expand to meaningful diverse set and review recent unseen holdout clips; require no unresolved catastrophic cuts, no wrong-account or unauthorized posts, and a threshold **agreed after** measured baseline. Never hide low recall by simply making no clips.
