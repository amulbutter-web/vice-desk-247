# Resource and Instagram-reel research register
**Interpretation:** `Source lead` is NOT proven multimedia content; `Docs inspected` is NOT a successful feature test; `prior test` belongs to the **previous Manus report**, not a test run for this pack. Matrix also supplied as `resources.csv` for sorting.

## Evaluation and potential combinations
| Tool / resource | Best-fit use | Current status | Decision and integration boundary |
|---|---|---|---|
| **PeakCut** | near-live rolling capture + candidate selection + queue + web + social connectors | Public repository inspected; prior Manus 21/21 test groups on 17 Nov 2026 pinned commit (not reproduced here) | **Lead baseline candidate**. Compare live capture quality, permissions and EDL extensibility. Fork pinned SHA only after own tests |
| **OpenShorts** | per-scene crop selection: tracking, split-screen, gameplay overlay, captions, preview | Public README, untested here | **Compare for editor subsystem**; either adopt a proven isolated crop module or borrow validated patterns with license check; never assume hosted tools are free/unlimited |
| **SupoClip** (`FujiwaraChoki` + `cspenn` are different repositories) | offline video→short pipeline, word captions and alternate architecture | Two similarly named repositories found; not tested | **Experiment**: preserve repo identity and target architecture (one uses Apple Silicon local ASR). Do not confuse implementations |
| **Concat-videoeditor** | sophisticated timeline/edit API, keyframes, effects, MCP/JSON-RPC | Repo docs inspected; GPU/native Rust setup complex | **Defer core dependence**; investigate EDL interoperability once deterministic FFmpeg renderer works |
| **MakeMyClip/editor** | local editable transcript/timeline + exports + MCP | Repo docs inspected | Optional offline operator/editor interface; gameplay visuals need separate tests |
| **PySceneDetect** | detect scene changes for pre-segmentation/continuity | Repo/docs inspected | **Trial** on gaming videos. Scene cuts are NOT highlights; helpful source of boundary candidates, not quality evidence |
| **WhisperX / faster-whisper / PeakCut sherpa-onnx** | ASR and word-aligned subtitles | Docs inspected, no accuracy test | Bake off multilingual gaming speech/slang + CPU/ARM efficiency; prefer proof on own fixtures |
| **FFmpeg/ffprobe** | bounded cutting, sample extraction, loudness, render, output QC | Mature tool, expected runtime | **Core**; verify codecs and timestamp correctness on target VM |
| **Twitch Helix Clips API** | authorized native live clip creation, VOD clip, download endpoints, creator/editor scopes | Official docs inspected | **Try before custom capture where applicable**; clip duration constraint and creator authorization must be accommodated |
| **Gemini video understanding** | video-aware candidate and final-output judge | Official model/pricing docs inspected | **Video candidate**, not default best. Evaluate false positives, temporal detail, unavailable free limits |
| **xAI Grok API** | alternate visual/text judge where API supports input modality | Official pricing docs inspected | Compare empirical clip quality/latency/cost; no assumption it's superior to Gemini |
| **DeepSeek API / open weights** | efficient JSON textual metadata, alt editor narrative, optional vision on supported model | Official docs inspected; API and local weights have different cost/security | **Text-specialist trial**; validate actual model's JSON, vision, latency and local hardware fit |
| **Groq inference** | fast ASR and text inference option (different company from **Grok/xAI**) | Provider option in PeakCut; free quotas account-specific | Secondary provider trial; verify limits inside own account |
| **OpenRouter** | fallback/routing for compatible models | Provider listed in PeakCut README | Only after privacy, availability, cost, auth and output-contract test |
| **Open Generative AI / Muapi** | optional generated b-roll/video enhancements, lip-sync | Prior Manus says not a live source/ingest foundation | **Defer** unless measurable quality uplift and rights/cost check |
| **Ootto MCP / Instagram assistant** | possible hosted Instagram connector | Prior Manus could not verify auth/schema/self-hostability/cost | **Park**. Not a dependency without actual documented API schema and test call |
| **Meta Instagram publishing/insights** | OAuth, Reels upload, status, quota, media insights | Official documentation & prior conflicting quota reports | **Core gate** once verified on actual professional account. Query live quota; don't hardcode “50” vs “100” |
| **YouTube Data API** | upload, authenticated channel status, metrics | Official docs inspected; audits/settings may differ | **Core gate**; validate per-account privacy, upload quotas, media IDs and returned post state |
| **OCI Always Free** | initial 24/7 lightweight orchestration, small workers | Official current docs inspected | Start ONLY after capacity & ARM64 test; move render/ASR off-host or upgrade if necessary |
| **TinyFish / Manus older reports** | evidence leads for failure taxonomy, LLM judges, Instagram terms | Prior research only; not all 260 cited sources independently checked here | Use as search bibliography; validate claim-specific original papers before relying on numerical rates |
| **MAST multi-agent failure taxonomy** | termination, role drift, repetition and verification failure modes | Original paper metadata inspected | Apply as design checklist, not a direct prediction of this project's failure probability |
| **Anthropic: Building effective agents** | composable workflows, in-between gates | Original research page inspected | Use deterministic flow where possible; targeted model calls where necessary |
| **VideoJudge research** | calibrated multimodal evaluator methodology | Paper inspected | Design inspiration only. Model benchmark scores cannot substitute for labelled GTA clips |

## Combined design patterns worth testing
1. **PeakCut live ingest + OpenShorts adaptive framing + FFmpeg render + independent multimodal QC**: high-impact candidate. Contract boundary = timestamped EDL, not shared mutable media state.
2. **Twitch official clip or creator feed + PeakCut rolling buffer**: choose route based on authorization, event duration and reliability. Native Twitch short clips are constrained compared with custom event-sized cuts.
3. **PySceneDetect scene boundaries + sound/chat/motion detector + Gemini/Grok video judge**: improves candidate recall *hypothesis*. Evaluate against manually tagged peaks; avoid using visual scene cuts alone.
4. **ASR benchmark + sentence/silence alignment + video event judge**: test start/end precision and whether build-up/resolution are preserved.
5. **Meta/YouTube insights + immutable clip-feature DB + experiment assignment**: investigate hooks/crops/length in a statistically controlled way, rather than letting an LLM invent causal trends.
6. **Reel research intake + explicit URL/creator evidence + GitHub metadata verification**: turn leads into reproducible research notes; do not guess missing links from unseen videos.

## What the Instagram archive *does and does not* contain
Prior catalog report: **179 messages**, of which **168 Instagram shared posts/Reels**, and **7 explicit non-Instagram URLs**; it saved message text, captions, owner handles, timestamps, hashtags, explicit resource links and music credits where present. **It did not contain Reel MP4s, full speech audio, displayed frames, images or hidden comment/DM/bio target links**. A separate 50-Reel Manus task paused when its credits expired. The six-shares archive reproduces the earlier reports, and an overall note states the direct consolidated Manus brief was only partly accessible. Treat **all 168 media-based claims as requiring visual/audio inspection** before calling them verified. Do not assert 168 links equal 168 distinct useful tools.

### Reel validation spec (for an authorized copy of each video)
- Store Instagram URL, share timestamp, uploader, media ID, public/consent status, caption language and linked metadata.
- Extract audio transcript with 100–250 ms word-level alignment where feasible; log ASR model and confidence; source language.
- Extract screen frames densely enough for transient repo names/URLs (e.g., 5 FPS sample; increase around flash windows), run OCR or multimodal vision, timestamp each candidate string; **5 FPS is an experiment, not a guarantee**.
- Normalize candidate domain/repo owner+name; search GitHub and compare README, license, commits, source directory, stars/date **as corroboration, not identity proof by itself**.
- Mark link provenance `caption`, `audio`, `OCR_at_12.4s`, `official-site`, `inferred-unverified`, `failed-access`. Reject hallucinated repo URLs.
- Verify only public, legitimate links; do not bypass paywalls, authentication, private messages or “comment X” requirement if content is not otherwise public.
- Categorize: `core`, `upgrade-candidate`, `research-only`, `not-for-project`, `inaccessible`, `duplicate`; connect each useful item to one named PRD requirement and test.

**Reel evidence ledger status today:** catalog counts and prior summary verified *from the source documents*, not individual video frames. A truly verified **all-Reel audiovisual ledger remains blocked by missing video/audio**; do not treat this new pack as having completed that specific task.

## Research quality and wording
Previous source titles mention “17 shared sources” and a **49-reference** project assessment; neither is a validated 17-item list of distinct build assets. Source citation ≠ executable compatibility. Where the earlier source PDF/report or linked reel was unavailable, this document preserves the uncertainty.
