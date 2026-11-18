# WHAT IS PROVEN, WHAT IS NOT, AND THE CORRECT NEXT STEP
**Prepared 18 Nov 2026.** This is the anti-hallucination record that must travel with the developer brief. The original owner asked for all nuanced requirements and all usable research: errors happen when one model's confident reply is promoted to engineering truth.

## Supported directly by original project discussions
- Two workflows, top-gamer plus trending discovery, full goal of 15 actively processed concurrent lives, no hardcoded clip duration.
- Source-specific candidates, multiple editor roles/parallel execution, review-and-repair supervisor, both platform publishers, queue/error/infra/storage monitoring, publishing feedback and owner-alerts.
- Low-cost initial cloud, Oracle considered, 24/7 runtime with operator devices off, pursue monetization but no guaranteed outcome.
- Quality, creativity, completeness, correctness, branching and agent failure prevention as highest-priority design principles; '0.0001% category' is aspirational quality mindset.

## Earlier research reports (evidence NOT re-executed here)
- Prior Manus: PeakCut automated test suite reported 21 passing test groups at `1bef2b48385568c26a798f2ef20152d2b0f531dd`. It did NOT test a full real live ingestion → excellent clip → platform publishing → engagement feedback cycle or 15 concurrent streams.
- The user said roughly 117/126 researched Reels; this recollection has not been equated with unique media in the captured export. Previous catalog: 179 messages, 168 Instagram share entries and seven direct non-Instagram URLs. Not 168 videos watched. Video/audio/screen/links not fully captured. Unreconciled duplicated shares and post types may exist.
- Prior Manus source assessment had 49 numbered reference entries, while another share used '17 verified links' language. Current original complete 49-source list and exact reconciled 17 rows were not independently enumerated in this V2. Neither may be labeled 'reverified'.
- TinyFish earlier Claude reply mentioned five reports and approximately 260 source entries. These are third-party reported totals, not a new independently retrieved 260-paper review.

## Current public documentation / repository descriptions checked 18 Nov 2026
1. PeakCut repo: https://github.com/haziqahmedqasmi/PeakCut describes live ingest, clipping and multiple social accounts; this is documented, not runtime proof.
2. OpenShorts: https://github.com/moha700m/OpenShorts describes smart layout, face tracking and hosted/self-hosted distinctions; the `cloud/` licensing carve-out needs careful commercial review.
3. FujiwaraChoki SupoClip: https://github.com/FujiwaraChoki/supoclip describes uploads/VOD (not live) and platform analytics feedback; AGPL-3.0.
4. cspenn SupoClip: https://github.com/cspenn/supoclip and README describe local pipeline, optional VLM and Apple Silicon Parakeet-MLX.
5. Twitch reference: https://dev.twitch.tv/docs/api/reference/clips documents native Create Clip/From VOD and download paths, access scopes and 5–60s published clip duration.
6. Oracle official: https://www.oracle.com/cloud/free/ advertises A1 free 1,500 OCPU-h + 9,000 GB-h monthly; **no benchmark claim**.
7. Google YouTube quota: https://developers.google.com/youtube/data/getting-started describes separate default 100 search calls/day and 100 uploads/day buckets plus 10k shared units; account-specific quotas still need checking.
8. Current YouTube `videos.insert`: https://developers.google.com/youtube/data/reference/rest/v3/videos/insert ; Google official issue clarification https://issuetracker.google.com/issues/572863050 says forced-private restriction for unaudited projects was lifted; safe private tests still prudent.
9. Meta changelog: https://developers.facebook.com/docs/instagram/platform/instagram-api/changelog/ distinguishes Instagram Login without Facebook Page and its permissions from Facebook Login path.
10. Gemini video docs: https://ai.google.dev/gemini-api/docs/video-understanding says default static processing is 1 FPS, with model/mode-dependent alternatives; dense rapid gameplay needs special treatment.
11. MAST paper: https://arxiv.org/abs/2503.13657 / NeurIPS conference version, 14 failure modes, not app success percentages.
12. Hallucination Snowball: https://arxiv.org/abs/2608.14588 (finance domain; do not transfer reported figures).
13. Beyond pass@1: https://arxiv.org/abs/2603.29231 (long-horizon reliability study, not system error guarantee).
14. VideoJudge: https://arxiv.org/abs/2509.21451 (research on multimodal judging, not a gaming editor leaderboard).

## NOT verified in this V2 and required before claiming actual readiness
| ID | Missing proof | Why it matters | How to resolve / owner |
|---|---|---|---|
| O-01 | Raw/accessible 168 share videos/audio and complete Reel catalog in a programmatically readable environment | Cannot extract flashed GitHub links or compare every Reel resource | User provides lawful media or accessible archive; research extractor runs timeline-indexed audit |
| O-02 | Reconciling '17 verified' sources with 49 reference entries | Do not duplicate, omit or misrepresent verified status | Read full original Manus assessment/reference numbering and record separate identities |
| O-03 | Source creator permissions + authorized feed | Determines legal and robust live ingest method | Owner/creator explicitly grant rights/API scopes |
| O-04 | Actual Instagram professional account and correct Login flow scopes | Publishing may be blocked or miswired | Authenticate secured test account and verify actual product/scopes |
| O-05 | YouTube OAuth and live upload quota/status | Can't prove authorized publish | Test private upload and status polling under actual project |
| O-06 | User OCI tenancy/free VM availability and technical performance | 15 processing capability unknown | Verify tenancy/ARM64 environment and benchmark 1/2/5/15 |
| O-07 | Actual price, free limits and payment requirements for each chosen model | Provider selection can become expensive/unstable | Run preflight on intended accounts and budget gate |
| O-08 | PeakCut current branch and pinned code actually pass tests in intended environment | A prior automated test report isn't current E2E proof | Clone at SHA, isolated tests, clean base Docker build |
| O-09 | Human-editor gold labels on diverse GTA/other gaming scenes | No trustworthy clip quality/recall metric | Collect rights-cleared fixtures and dual editor ratings |
| O-10 | Verified Ootto MCP endpoint and exact capabilities | Cannot rely on guessed Insta/YT adapter | Identify vendor, actual auth/schema/privacy, test on test account; otherwise defer |
| O-11 | Meta daily publishing quota for owner account / account-specific terms | 50/100 claims conflict historically | Read `content_publishing_limit` current endpoint and enforce limit |
| O-12 | Cross-platform originality/monetization eligibility | Business revenue not guaranteed | Rights/monetization eligibility review and tracked revenue evidence |
| O-13 | Production input/output real-world latency, throughput, cost and uptime | No 15-load or near-live claims proven | Repeated objective benchmarks with cost/soak evidence |
| O-14 | Independent visual judge human agreement / creative superiority | Two models could reinforce each other's errors | Blinded matched footage, actual video review and holdout measurement |
| O-15 | Full real-media Clip/Upload and verified metrics closed loop | Product not running yet | Execute Phases 2–6 with owned media and accounts |

## Decision policy / no unnecessary blocking
The implementation engineer can proceed with drafting schemas, local unit tests, licensed component experiments, mock platform adapters and rights-cleared fixtures without all credentials. Only ask owner for critical account/permission/purchase/live-publication decisions. Missing 168 media prevents *per-Reel audiovisual claims*, not all engineering research. Missing OCI verification prevents a free 15-stream guarantee, not the designed 15-stream target.
