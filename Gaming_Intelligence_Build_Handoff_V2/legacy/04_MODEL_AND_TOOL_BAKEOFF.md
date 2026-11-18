# Model, editor and source-adapter comparison protocol
## Rule
Never choose the model because its marketing says “best”, it's on GitHub or a Reel claims it is free. Run the **same blinded, labelled fixtures** and publish both quality and marginal compute/call cost. Separate **Grok (xAI)** from **Groq (inference provider)**.

## Roles to test
| Job | Candidate options | What counts as evidence |
|---|---|---|
| Audio transcription | PeakCut sherpa-onnx, faster-whisper, WhisperX, Groq hosted ASR if available | word error + timestamp error on loud English/Hindi/Hinglish and game slang; ARM64 feasibility, RTF and cost |
| Candidate judgement | Gemini video understanding, xAI vision-capable model, supported open model | high recall on events, rare visual-only game moments, hallucinated event rate, cost and p95 latency |
| Edit planning / metadata | Gemini text, DeepSeek JSON model, Groq-hosted model, OpenRouter | schema pass, factual title consistency, captions, non-invented content and cost |
| Final multimodal QC | a **different model family**, where possible, than editor; human review reference | agreement with calibrated editors, *false approvals* (critical), crop/subtitle visual errors detected |
| Rendering | PeakCut rendering stack, OpenShorts crop selection, Concat API, FFmpeg baseline | cropping retains relevant gameplay/facecam; precise cut boundaries; determinism, render time |
| Live ingest | creator-provided recording/feed, supported native Twitch Clips API, PeakCut source adapter where permitted | source rights, connection success, gap rate, PTS sync, event preservation, reconnect behavior |

## Fixture set (must be owned/authorized)
- **30 videos** minimum for initial challenge set, split 10 talk-heavy, 10 action-heavy without speech, 5 chaotic split-screen/facecam, 5 multilingual/Hinglish. At least 10 include **no notable highlight**, to measure false positives.
- Label 3–5 time intervals per highlight with `build-up`, `peak`, `resolution`, and `must-not-cut-inside` boundaries, plus visibility of game UI/facecam and profanity/music/licensing notes. Use **two humans** for a stratified subset; adjudicate disagreements and record them.
- Keep a **holdout set** untouched while tuning models; near-live captures from **two permissioned streams** as second benchmark.

## Comparison scoring (decision framework, not measured results)
- Critical gates: publishing authorization, no unbounded errors/retries, output decodes, no severe crop truncation, no hallucinated event claim, no source rights failure.
- Weighted utility among gate-pass candidates: **35% highlight completeness/precision**; **25% edit/crop/subtitle quality**; **15% final-review false-approval rate**; **10% p95 time to ready**; **10% resource/call cost**; **5% maintainability/LICENSE/security**. Record raw metric alongside weighted total.
- Any critical gate failure => **not eligible for unattended release**, regardless of score.
- For deployed 15-stream target: compare ingest-only monitor overhead vs simultaneous ASR/render, record per-stream and total CPU%, RAM, RSS, disk writes, network ingress/egress, backlog and dropped segments. Use admission controller and fair queues.

## Acceptance experiment design
1. Seed reproducible source fixtures and human labels; all tools use same files and stage boundary.
2. Run known pinned commits and settings 3 times; record model version, API pricing date, region, CPU ISA, memory and duration.
3. Calculate recall, precision, complete-event rate, temporal boundary MAE, subtitle WER/timing error, crop violations, false approvals, remote posting success and p95 latency.
4. Compare paired clips blindly. If OpenShorts reframing beats PeakCut on gaming/HUD, adopt a portable crop adapter; if not, keep core simpler. If no high-confidence winner, route ambiguous cases to human.
5. Store representative fails and add regression fixtures before moving to next stage. **No statement of 'X is best' until numbers exist.**

## Pricing / quota reality check
- Oracle official 2026: **2 OCPU / 12 GB equivalent** Always Free A1 budget, not guaranteed allocation or 15-stream capacity. ARM build/ASR compatibility must be tested.
- Gemini free API access is limited by model and account rate tiers. Developer pricing and caps change; inspect actual free model availability and live quota before choosing.
- xAI API, DeepSeek API and Groq hosted inference are **not the same as free self-hosting**; free usage, if any, must be verified in the user's account. Locally running large weights on a small ARM CPU often loses the desired speed and quality.
- External keys discovered on public GitHub must never be used. Obtain legitimate API tokens and configure secrets manager or root-only environment file.

## Baseline experiment log template
`run_id | fixture | rights_id | source_type | commit | model_id | prompt_version | scorer | CPU/RAM/GPU | duration | tokens/cost | boundary_MAE | complete_event | precision/recall | crop_fail | subtitle_fail | false_approval | publishing_remote_verified | notes`
