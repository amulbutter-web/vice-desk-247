# INSTAGRAM REELS — FULL KNOWLEDGE EXTRACTION VS WHAT THE ARCHIVE ACTUALLY PROVES
## Key source audit
The user also recalled researching about **117/126 Reels**. That estimate has not been reconciled with the export item counts or media uniqueness. The preserved Manus catalog reportedly contains **179 messages**, of which **168** were Instagram post/reel shares and **seven** were explicit outside-Instagram URLs. Some duplicates or post-vs-Reel distinctions may remain; *168 shares* does not automatically mean 168 distinct videos. Manus's own notes admit that caption/owner/hashtag/music/typed-link metadata were recovered, while the archive did not include video/audio files. Another attempt to pull the latest 50 Reels was paused because credits were exhausted. The title '17 verified links' in a different Manus share is not reconciled with the separate 49 numbered citations in its long assessment. No honest agent can reconstruct a flashed one-frame GitHub URL from a caption-only export.

The project owner wants analysis **as if a human actually watched/listened**: spoken content, subtitles, flashes on a screen, screenshots, app demo behavior, hidden URL hints, code/repos/plugins and image captions—then browser/GitHub/official docs validation—*without requiring comment/DM bait*. This is a research ingestion requirement, not permission to bypass account privacy or protected downloads.

## Media access and rights triage
Start with the user's own exported/saved media or permitted public media sources and current platform terms. Log `media_available`, `access_method`, `consent_or_license`, `restrictions`, `media_sha256`, `duration`, source share ID and working file. If no media file exists, stop video/audio inference; retain only caption-derived leads. No account takeover, cookies stolen from browsers, private group scraping without rights or bypassing restrictions. If creator withholds a link, try independent official name/repository search and label it as a *candidate*, not the recovered hidden exact link.

## Extraction workflow for an actually obtained Reel
1. Record canonical Reel/post ID, share/message ID, timestamp, creator handle, caption, declared audio attribution and first-party URL; distinguish video from carousel/image-only posts.
2. Preserve source bytes/sha256 and metadata/ffprobe/duration. Keep media alongside appropriate rights, retention rules and processing logs.
3. ASR transcript with timecodes (not caption-as-transcript), language/code-switching and confidence. Cross-check technical names by replay, not by model plausibility.
4. Scene/slide segmentation. OCR frames at a rate appropriate to flashes, not just default 1 FPS. Dense frame sampling of short passages can spot half-second URLs, but OCR still requires manual verification of ambiguous characters. Record exact frames `start/end ms`, crops and OCR confidence. Use multiple modalities where applicable.
5. Human-visible video description: tools being demonstrated, UI sequences, sound/music, logo/brand, command snippets, image/transient contents and safety/privacy notices. Do not make unsupported audio claims from silent caption metadata.
6. Extract explicit URLs and candidate `owner/repo` names, API/MCP/provider references, code commands and tool versions. For briefly shown URL, store screenshot/frame evidence; for spoken names record audio timestamp.
7. Verify identity independently on GitHub official repo URL, README, LICENSE, current owner, recent commit, archived/unmaintained status, exact linked asset, deployment prerequisites, fees and rights. Record repo SHA/date and `identity_confidence`. A generic repo with similar name is not the same resource.
8. Map useful resource to one or more FR IDs with *concrete possible connection*, pros/cons, compatible interfaces, value hypothesis, direct alternative, integration/test cost, evidence level and license blockers.
9. Run a reproducible task-level test with rights-cleared gaming footage when it is a deployable tool. If merely a conceptual tip, write an executable local test or reasoned applicability note; do not claim the video tool worked.
10. Return JSON/CSV and brief human-readable summary per share. Link rows to a unique media object and preserve unresolved leads; sort by urgency/relevance, not popularity alone.

## Extraction fields (recommended)
`share_message_id,source_platform,canonical_reel_url,video_id,creator_handle,source_export_time,media_available,media_sha256,raw_caption,caption_explicit_urls,transcript_segments,visible_text_frames,visible_url_candidates,spoken_names,tools_and_claims,verified_official_urls,verified_github_owner_repo,git_commit_or_release,license,project_FR_links,evidence_modality,evidence_timecode,evidence_artifact_ref,verification_method,verification_status,test_status,objective_win_risk,adoption_decision,notes`.

**Allowed verification statuses**: `CAPTION_ONLY`, `MEDIA_OBSERVED`, `IDENTITY_CANDIDATE`, `IDENTITY_VERIFIED`, `REPO_DOCUMENTED`, `TESTED_ISOLATED`, `TESTED_ON_PROJECT_FIXTURE`, `REJECTED`, `INACCESSIBLE`, `NOT_APPLICABLE`. Do not set `TESTED` after just opening a web page. Store independent `project_relevance_score` separate from `evidence_confidence`.

## Frame-level screenshot criterion
A flashed GitHub name qualifies as `OBSERVED_FRAME` only if the log includes local frame timestamp and retained crop proving the exact string. If the screenshot merely hints at a username, search on GitHub and mark resulting links `candidate_needs_visual_confirmation`. A repo star count is volatile; compare approximate timeframe without assuming close star count proves identity. No claims to reverse private comment/DM-only URLs.

## Evaluation/ranking for our project
Each resource: (a) directly helps authorized live ingest, (b) moment quality, (c) editing polish, (d) visual QC, (e) publishing/access, (f) analytics feedback, (g) reliability/ops, (h) testing/evaluation, (i) irrelevant or inferior. Promote if expected measurable benefit exceeds licensing/complexity cost; otherwise keep as documented optional candidate. **Not just PeakCut, not just APIs**: e.g. crop algorithms, voice/video evidence, durable queue, editor effects, metrics, bot/automation interfaces and safety tests are in-scope if they actually contribute.

## Exact open gap
The original ZIP (owned by the user) is the source of record for caption catalog. This V2 package does not include authentic 168 MP4s or a newly completed per-Reel audiovisual audit; those were absent from accessible captured artifacts. Prior assistant commentary saying 'all 179 records read' must not be restated as all audiovisual content read. When full catalog access is restored, regenerate an itemized `reel_knowledge_catalog_v2.csv` rather than backfilling imaginary frame URLs.
