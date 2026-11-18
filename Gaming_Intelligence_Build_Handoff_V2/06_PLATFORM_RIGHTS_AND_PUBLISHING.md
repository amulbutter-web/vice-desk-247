# PUBLISHERS, OFFICIAL SOURCE ADAPTERS, RIGHTS AND REAL ACCOUNT TESTS
**This is technical planning, not legal clearance.** Creator permission, platform access, derivative/repost rights, music/assets and account ownership are distinct checks. Public availability of a video isn't permission to ingest/repost it. Instagram and YouTube both have originality/copyright rules. Do not substitute unauthorized playback scraping, leaked cookies or bot-check circumvention for permissioned source adapters.

## Source approaches — trade-offs before building
| Source | Authorized mechanism | Benefits | Limits / acceptance |
|---|---|---|---|
| Own local video/creator upload | manual upload + signed creator license/permission | stable, highest test reproducibility | media authenticity, malware/probe/file caps, rights record |
| Creator-authorized live push | creator's permitted RTMP/SRT/recording share | full-context rolling buffer, event >60s possible | implement secure ingest, token rotation, clock drift, reconnect; scope in agreement |
| Twitch native live Clip API | `POST /helix/clips` with `clips:edit` token and allowed broadcaster | native capture, reduced custom capture surface | clips 5–60s, clips enabled, async result; 90s capture window; verify current scopes and replay ability |
| Twitch editor VOD clipping | `POST /helix/videos/clips` as authorized editor/broadcaster | choose VOD offset and current ongoing VOD | native length 5–60s; ability to download needs authorized `editor:manage:clips`/`channel:manage:clips` and available VOD; not a replacement for arbitrary-length events |
| YouTube creator-recorded material | explicitly creator-provided media/authorized feed, creator uploads | good for long-form source | public YouTube player URL alone may not authorize recording or distribution |
| Kick | creator-provided exports/contracted feed or official approved API | platform reach | verify current API/ToS and permissions; do not build core around undocumented playback endpoint |

## Instagram — TWO different login products
**Instagram API with Instagram Login:** professional IG creator/business account; relevant permissions include `instagram_business_basic` and `instagram_business_content_publish`. Meta's changelog says this path does **not** require a Facebook Page; host URL `graph.instagram.com`. Test this exact path, not mixed Graph endpoints.

**Instagram API with Facebook Login:** professional IG account linked to a Facebook Page; different auth/scopes/endpoints. Keep separate configuration and never assume the Page requirement applies to both paths. For third-party accounts, review/Advanced Access requirements can apply; verify current product-specific app access. Sources: https://developers.facebook.com/docs/instagram/platform/instagram-api/changelog/ and https://www.postman.com/meta/instagram/folder/1z5vxzu/instagram-api-with-instagram-login .

**Publishing state:** `REEL_ASSET_READY` → container/create request → container processing → `FINISHED/ELIGIBLE` (exact current Graph response) → media_publish → query returned media status/ID → `PUBLISHED_CONFIRMED`; if a request times out, query remote before any retry. The service needs HTTPS-accessible source video if using `video_url`, valid container/codec/audio/duration, full matching permissions and account cap. Current Meta Postman Reel spec mentions H.264/HEVC, AAC, 9:16 recommended, and limit fields: verify against live product docs/account before hard coding. Source: https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api .

**Quotas:** Older Claude/Manus responses conflict on 50 vs 100 publishes/24h. Query the actual account `content_publishing_limit` and `quota_total`, with cached conservative cap and daily guards. Do not claim it permits 30 uploads/hour per account. Prevent spam/reposts and maintain crediting/originality checks. No unverified assumption that Reel bonuses are available or that creative overlay automatically creates copyright clearance.

## YouTube — quota AND status corrections
As of current official docs, default quotas include **100 `videos.insert` calls/day in a separate uploads bucket**, **100 `search.list` calls/day in a separate search bucket**, and **10,000 units/day for other endpoints**. The newer quota structure supersedes older claims that video insert always consumes 1600 units of one shared bucket. Test actual project quota and API error messages, not assumed global limits. Source: https://developers.google.com/youtube/data/getting-started .

Current `videos.insert` reference specifies media upload and `status.privacyStatus`; explicitly set `private` in safe testing, even if API default changes. Earlier private-only restrictions on unaudited app projects were **officially clarified as lifted in Oct 2026** (Google Issue Tracker 572863050); this is not blanket authorization for harmful/unauthorized uploads or an exemption from other policies. Source: https://developers.google.com/youtube/data/reference/rest/v3/videos/insert and https://issuetracker.google.com/issues/572863050 .

**Verification flow:** OAuth authorized correct YouTube channel → resumable videos.insert with private status → store upload session and returned video ID → query videos.list for status/privacy/processing errors → confirm correct account, title and media → optionally schedule/approve public publish. A video ID alone is **not** final proof it processed successfully. Long videos and Shorts classification require current platform rules; avoid asserting a single permanent length threshold from old sources.

## Publisher outbox and idempotency
Never fire direct publish call from inside edit-loop side effects. Insert durable `publish_intent` with unique `(account_id, source_asset_hash, variant_revision, destination, campaign)` and `content_sha`. State transitions and platform leases protected with DB row locks; account quotas read before enqueue/submit. Upon API ambiguity, `PUBLISH_STATUS_UNKNOWN` holds retry and starts reconciliation; if remote confirms post, link remote ID and finalize. Remote APIs may not support caller-supplied idempotency keys; **local exactly-once intent plus remote reconciliation** is the design, not a guarantee of distributed exactly-once delivery.

**Publish preflight gate:** authorization current, upload consent valid, source and music rights, no forbidden raw repost, content fingerprint distinct, platform file validation, title/credit/AI disclosures when applicable, no hard QC fail, approval state permitted, correct destination account verified, quota remaining, signed URL token not expired, cost/egress within owner budget.

## Revocation/removal policy
If a creator revokes access, disable new capturing and publishing; retain audit minimality and meet contract/legal deletion obligations. Where a post must be removed, log remote deletion outcome, operator notification and backups carefully. Explicitly maintain distinction between copyright clearance and the creator's willingness to let the system automatically publish on an operator's monetized account.

## Minimum real integration acceptance tests
1. One **owned/rights-cleared** private upload on YouTube, correct channel and remote `processed` state.
2. One professional IG account, correct selected login flow, app permissions and one actual private/test-account controlled Reel publish with media ID and availability; no public test content on an unrelated account.
3. Auth expired, rejected scope, quota exceeded, 429, 503, lost timeout after successful remote post, over-sized file, wrong audio codec, bad HTTPS URL, missing permission, duplicate job, AI disclosure/credit flag test cases.
4. Reconcile without duplicate public artifacts; test follow-up `status` after worker crash.
5. Audit all rights decisions, platform API call IDs, source and output hashes and time zone / status.

## Official evidence links
- Twitch clips: https://dev.twitch.tv/docs/api/reference/clips
- Twitch clip guide: https://dev.twitch.tv/docs/api/clips/
- YouTube insert: https://developers.google.com/youtube/data/reference/rest/v3/videos/insert
- YouTube quota: https://developers.google.com/youtube/data/getting-started
- YouTube post-policy clarification: https://issuetracker.google.com/issues/572863050
- Instagram Login changelog: https://developers.facebook.com/docs/instagram/platform/instagram-api/changelog/
- Meta Postman: https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api
