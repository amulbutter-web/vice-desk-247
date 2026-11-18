# REPOSITORY / MODEL / API RESEARCH AND BETTER-THAN-BASELINE EXPERIMENTS
**No tool is selected just because a Reel, README, coding assistant or influencer calls it 'best'.** Test the actual component, pinned SHA, license, package/runtime dependencies, CPU/GPU requirement and source integration. Distinguish `REPO_DOCUMENTED`, `PRIOR_TESTED` and `MEASURED_HERE`.

## Critical candidate comparison
| Candidate | Public documented capabilities | Best proposed role | Warning / integration test |
|---|---|---|---|
| [PeakCut](https://github.com/haziqahmedqasmi/PeakCut) | live buffer, URL/file clips, transcription, captioned render, connected accounts, posting/queue | **baseline fork candidate** for end-to-end skeleton, live source orchestration | prior 21 test groups reported, not re-executed in this V2; **no demonstrated video-aware final judge** on actual gameplay; pin known commit then audit moving main; source rights and 15-load unproven |
| [OpenShorts / moha700m](https://github.com/moha700m/OpenShorts) | smart 9:16 layout (TRACK/GENERAL/SPLIT/SCREENCAST), face tracking, word-level subtitles, hooks and effects, local/hosted paths | A/B **smart reframing + layout** vs PeakCut for gameplay/facecam | docs describe self-host core MIT with exception for `cloud/` commercially restricted; **do not import hosted cloud code** for monetized service without license review; dense game HUD may defeat face-centric design |
| [SupoClip / FujiwaraChoki](https://github.com/FujiwaraChoki/supoclip) | video/VOD/upload clips, captions, manual editor, direct posts, **feedback loop documented** | A/B on full uploaded-video product, post analytics and editor workflow | AGPL-3.0, not live streaming; verify actual analytics implementation, tests, deployment and commercial/license consequences before code reuse |
| [SupoClip / cspenn](https://github.com/cspenn/supoclip) | local single-process clipper, optional VLM reranking, face crop, scene/dark QC and extensive tests described | structured tests, VLM reranking and source/text alignment patterns | Apple Silicon `parakeet-mlx` path unsuitable to assume on Oracle ARM Linux; AGPL-3.0; features may be talking-head-centric |
| [Concat](https://github.com/tmenov/Concat-videoeditor) | open native editor + CLI/JSON-RPC/gRPC/MCP and offline models | possible **higher-end effects/project render** engine or human finishing tool | beta, large Rust/GPU engine, API shape and ARM runtime need test; not an automatic live game highlight selection replacement |
| [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | scene boundary detection | scene-change evidence and boundary snapping | scene changes not equivalent to hype or narrative completeness |
| [WhisperX](https://github.com/m-bain/whisperX) | ASR + word timing/diarization options | speech word alignment trial | heavy dependencies and language/GPU constraints; benchmark WER and cost |
| [FFmpeg](https://ffmpeg.org/documentation.html) | media crop/overlay/subtitles/codec/probe/filtergraph | deterministic rendering, final media validation | compiler-generated safe argument arrays, no arbitrary AI shell strings |
| [Ootto connector](https://mcp.so/) | earlier share claimed Insta/YT convenience | **defer** unless exact independently verified provider endpoint/schema/terms found | generic directory URL is NOT the Ootto endpoint; old assessment could not verify it; do not wire authentication to invented link |
| Open Generative AI / Muapi | hosted generation/editing/lipsync lead from Claude discussion | optional future generative or creator-approved asset workflow | not core for authentic near-live highlights; license/privacy/cost/runtime and identity not established by the shared notes |

### Why mixed architectures are likely superior
The original idea benefits from **PeakCut-like live orchestration** + **dedicated event boundary/context module** + **OpenShorts-like adaptive framing** + **SupoClip-like editor/feedback patterns** + **independent video-aware final QC**. But do **not** blindly paste competing licenses together. Prefer adapter implementations based on compatible licenses, clean reimplementations of general techniques, and real-head-to-head measurements. All components need versioned schemas and integration tests.

## Model provider clarification and routing
| Role | Candidates | Required task-level test |
|---|---|---|
| Transcription/word timing | PeakCut local sherpa/Parakeet, faster-whisper, WhisperX, selected hosted ASR | multilingual and game names WER; accuracy near explosions and voice chat; timing drift; OCI ARM64; token cost and worker footprint |
| Audio/gameplay event understanding | Gemini multimodal, alternate vision language models, local vision as capable | silent action recall, narrative completeness, game context correctness, video frame sampling and latency |
| Event boundary planner | Gemini video+audio, alternate video-capable VLM, deterministic boundary modules | source time ms offset error, preserve pre/post, no nonexistent events |
| Edit planner / hook writer | xAI Grok, Gemini, DeepSeek API, Claude/OpenAI, local LLM and open router | JSON validity, constraint fidelity, event truth, creative editor ranking, time/cost/reliability |
| Independent final judge | a **different** video-capable model or blinded rule/video reviewer, human calibrated | hard-negative videos, false passes, inter-rater agreement; don't pick brand with highest unverified leaderboard |
| Workflow/orchestrator | Python/typed workers, durable queue, DB | process failures and correctness tests; no chat agent necessary |

**xAI Grok** and **Groq Cloud** are different; compare pricing and model access separately. **DeepSeek API** and its open-weights models are also different from a hosted DeepSeek app. Verify actual current model supports video inputs: don't send an image/video to a text-only endpoint. Gemini's official video docs note default **1 FPS static sampling**, which can miss quick game events; customizable static FPS/clip intervals and newer agentic processing may be available depending on model. Test exact API model/feature behavior and avoid assuming a single frame/s can detect a half-second flashed link. https://ai.google.dev/gemini-api/docs/video-understanding

## Per-candidate reproducible evaluation protocol
1. Record repo URL, owner, exact SHA/release, LICENSE and dependencies, minimum CPU/GPU/OS and whether public API tools exist. Record README claims as `REPO_DOCUMENTED`.
2. Check issue activity, maintenance, active forks, release patterns, security/SSRF/cookie use and secret handling; do not infer trust only from stars or LinkedIn profiles.
3. Run project test command at pinned SHA in isolated environment. Record exact failures/warnings, not 'tests passed' without logs.
4. Run *the same* 40-ish rights-cleared gaming fixtures and negative controls: source hashes, model inputs, hardware, captions, target output spec; review in blind order against human labels.
5. Measure clip completeness, missed visually important moments, edit-quality preference, HUD/facecam crop, subtitle WER/timing, p95 latency, throughput per dollar, crash recovery, account/publish error coverage.
6. Include package licensing in the **go/no-go**, including transitive models, fonts, music, B-roll, scene footage and AGPL/network-service concerns.
7. Candidate wins its **specific role** only when outcome improves at no disqualifying reliability/license cost; hybrid integration then receives separate re-evaluation.
8. If uncertain, preserve a replaceable interface and add to evidence ledger; do not build dependency around guessed capability.

## Realistic provider API preflight checklist
- Model exact ID/list, vision/video/audio/structured-output support, max input/video size, frame-sampling strategy, latency, response schema, expiration policy.
- Per-account free/paid quota, RPM/TPM, batch limits, 429 Retry-After, region/payment availability, current costs, default safety refusals.
- Sensitive creator media privacy/retention; no unwanted training or leaking raw streams when selecting third-party provider.
- Timeouts, JSON compliance, wrong source timestamps, fabricated links and source quote hallucination on adversarial fixtures.
- Two-provider fallback must preserve output invariants; it isn't useful if it changes factual claims or randomly moves timestamps.

## Newer opportunities that are worth testing, NOT automatically adopting
- **Hierarchical moment scoring:** low-cost broad candidate pass → multimodal narrow review → fine-grained frame-boundary correction; favors meaningful precision without dropping all expensive analysis.
- **Parallel edit-plan proposals:** creative storytelling branch and spatial/caption branch independently, typed merge + conflict detection; possible improved framing and creative coherence.
- **Cross-stream event graph:** cluster same underlying event across different views with synchronized temporal fingerprints and editorial variety; don't assume equal clocks.
- **Source-aware visual cropping:** protect the score/map/mission prompts plus gamer face; a face detector alone is not enough.
- **Per-creator style learning:** retain approved styles and correct language/credit within consent boundaries, but avoid prompt contamination from external chat.
- **Evidence-conditioned dynamic repair:** judge outputs a specific failed interval and allowable operations, not an endless rewrite of whole video.
- **Human-editor active learning:** choose borderline candidates for review and use consented labels to improve recall; protect holdout from contamination.

## Contextual leads not core video system dependencies
General automation MCPs, scraping sites, creator-growth tools, website builders, database locking patterns, and duplicate-payment patterns may be valuable as **implementation patterns** rather than imported runtime dependencies. E.g. database locks and payment idempotency inform publish-outbox concurrency. Every resource needs an explicit mapping to the user's actual pipeline and proof of need, not inclusion because it appeared in a Reel.
