# Gaming Content Intelligence & Automation — Research-to-build handoff
**Dated:** 18 November 2026 (Asia/Kolkata)  
**Status:** Requirements + evidence-informed design; **NOT a completed or deployed product**.  
**Read in order:** `00` → `01_PRD` → `02_ARCHITECTURE` → `03_RESOURCE_MATRIX` → `04_MODEL_AND_TOOL_BAKEOFF` → `05_QA_AND_RISK` → `06_IMPLEMENTATION_ROADMAP` → `07_CODING_AGENT_PROMPTS`.

## What has been retained from the user's discussions
**Original GPT conversation (requirements baseline):**
- Primary **Live Gaming Intelligence**: discover top gamers AND trending live/videos, monitor a *target* of **15 concurrent live feeds**, detect meaningful highlights independently per source, determine **event-based clip duration** (not a hardcoded 30 s), generate polished vertical edits including gamer/gameplay-aware framing, zoom, slow motion, captions and hooks, quality-review, publish to Instagram and YouTube, observe performance and feed data back.
- Secondary **Uploaded Video Intelligence**: accept upload or authorized URL, skip live monitoring, use the SAME downstream pipeline.
- The original 15 “agent roles” are **responsibilities**, not a requirement to deploy 15 autonomous LLMs. The system must work unattended on cloud once validated, with minimal user interaction, notifications, storage hygiene and recoverability. Quality, timing and reliability take priority over artificially minimizing API count. Free/very-low-cost bootstrap on Oracle was requested; reinvest after the system works.
- Make working, permissioned, actual features—not a simulated demo—and produce a complete handoff that a coding agent can follow without inventing requirements.

**Later Claude discussion (engineering constraints and quality emphasis):**
- Concentrate disproportionately on **moment boundary selection, professional editing, rendered-output evaluation, independent supervision and post-publication learning**.
- Move repeated mechanical tasks into deterministic code; use specialized vision/LLM judgment only when evidence justifies it. Typed handoffs, explicit stop conditions, idempotency, error classification, fail-closed publishing, audit logs, budget and retry boundaries.
- Aim for extreme precision and very low error rates; **“0.0001%” is an aspiration, not a demonstrated statistical performance claim**. Evidence-driven gates and labels are required before full automation.

**Manus research (evidence and caveats):**
- Prior audit reports **21 PeakCut test groups passed** on pinned commit `1bef2b48385568c26a798f2ef20152d2b0f531dd`; that is prior **automated test evidence**, not proof of live capture, output quality, posting or 15-stream throughput.
- Instagram export yielded **179 messages**, **168 Instagram shares** and **7 explicit non-Instagram external URLs**, but **NOT video/audio/frame contents**. Consequently “hidden link shown for 0.5 sec”, spoken GitHub URL, images and audio **remain unknown**, not verified. One 50-Reel extraction task paused for credits. The alleged “17 verified sources” and **49 numbered references** in the earlier assessment are different units, not a reconciled list.
- Several original artifacts exist in the user-supplied `shared-conversations-archive.zip`: preserve this archive as the original evidence of record. This new pack does not silently re-create or claim to embed its unrecovered Instagram media.

**Current deadline context:** Rockstar's official GTA VI page currently lists **19 November 2026**, but that does not establish a midnight India release time. This research pack is not proof that 15-stream production readiness can be completed before launch. [Rockstar official page](https://www.rockstargames.com/VI).

## Current decision
**Candidate baseline, not a lock-in:** Evaluate a pinned **PeakCut fork** alongside OpenShorts and SupoClip; harvest only independently useful subsystems (e.g. adaptive crop) from competitors. Keep a replaceable provider interface for ASR, video judge, text model and publishers. Instagram tooling such as Ootto or hosted generative-video services is optional and must not be a core runtime dependency without live tests.

**First proof of end-to-end function:** process one rights-cleared recording through ingest → candidates → human-labelled event boundaries → event-aware crop + captions → two independent QC gates → approval → draft/test-account publish → analytics collection. Then try one authorized live feed. Expand to 2, 5 and 15 after resource/performance evidence. This is a *rollout method*, **not a reduction of the 15-feed product requirement**.

**Key open conditions, with a default until resolved:**
1. Rights to source and derivative distribution: default **creator-owned/uploaded/explicitly authorized** only. A public stream alone is insufficient permission.
2. Instagram/YouTube account scopes, app review, live per-account quotas, public HTTPS hosted media URL for Meta, and actual test uploads are unverified. Default **draft or private and human approval**.
3. Free OCI availability and exact instance capacity have not been measured on the user's tenancy. Default **2 OCPU/12 GB RAM equivalent Always Free allocation** based on current Oracle docs; no promise that it can process 15 active streams. Local CPU decoder, memory, disk and bandwidth benchmarks decide.
4. Revenue/viral performance: no outcome or earnings guaranteed by any of this engineering.

## Evidence labels to use everywhere
- **S = source-provided:** stated in GPT, Claude or Manus artifact; not independently re-verified.
- **D = independently inspected public documentation/repository:** site or README exists/describes capability; **not a live working test**.
- **T = independently executable test passed:** provide environment, commit, inputs, output, timestamps. This pack has **no new production/system T result**.
- **P = production proven:** actual authorized feed/account, repeat runs, measured outcomes. **No source here warrants P.**

## Hard rule for coding agents
Do not confuse `documented` or `prior test passed` with `production proven`. Preserve both workflows, the top-gamers AND trending selection, target 15 feeds, user-controlled publication, detailed monitoring and feedback. Never downgrade the product because a test fails; isolate the failure, record alternative candidates and required cost/capacity, then propose staged mitigation for user approval.
