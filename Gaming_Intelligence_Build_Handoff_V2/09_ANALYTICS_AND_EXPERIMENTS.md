# PERFORMANCE INTELLIGENCE, ATTRIBUTION, FEEDBACK AND CONTROLLED LEARNING

## Why this is a core product, not a dashboard afterthought
The original GPT concept assigns roles 13–15 to analytics collection, analyzing which portion of a clip works, and feeding changes back to cutting/editing/scheduling. Later Claude discussion repeatedly named views analysis as one of the five most quality-critical responsibilities. Therefore performance analysis must influence the system **through gated, measurable updates**—never just display raw views, and never blindly chase trending hashtags.

## Data to capture at editorial decision time
Store event source, creator, game, language, category, story type, source signal values, context/boundary times, selected final clip duration, format/voice/crop style, ASR/model/renderer version, QC scores, human override reason, output/hash and thumbnail/title/description/hashtags. For each platform post, store platform/account ID, upload mode, publish UTC, age of source at publish, media ID, failure/retries, approval mode, documented rights and geography if legitimately available. Do not record personal chat logs when counts are enough.

## Metrics sourced from provider endpoints
Collect views/plays, reach/impressions, watch duration/average watch percentage, completion/retention curves, likes, comments, shares, saves, new followers, CTR and earnings **only if that exact metric is exposed and authorized** for that platform/account/media type. Store field `availability=unavailable|denied|delayed|reported`, `metric_definition`, window, units, API version, account and retrieval timestamp. Never map missing to zero or pretend Instagram always provides per-second retention.

**Example snapshot strategy:** 1h, 6h, 24h, 72h and 7d after confirmed publication where quota and API access allow; differences in API lag, view normalization and sample size documented. Platform-dependent timing and incomplete ingestion may require fewer windows. Avoid comparing views of a 1-hour-old post to 7-day totals of another.

## Attribution and performance comparison
- Correct for media age, creator baseline reach, game/topic popularity, posting window, platform, geography, organic promotion, follower count, posting frequency, format and changes in platform distribution. Views are **outcome proxies**, not direct proof the chosen edit caused virality.
- Track clip-level watch rate, views normalized against creator/channel historical baseline, engagement per qualified view, velocity by elapsed hours, percentiles not just mean, confidence interval, unique creator and source diversity.
- When segmented view/retention curve is unavailable, report a **hypothesis** about the strong portion from editorial analysis; label no actual viewer drop-off data present.
- Monitor novelty and originality. Overproduction can dilute distribution or trigger platform restrictions, so objective is **value per approved clip**, not indiscriminate volume.
- Track costs and gross margin for creator-clipping-service scenarios. User's ₹40k–₹60k monthly goal is a business aspiration, not a forecast or deliverable guarantee.

## True feedback loop
1. **Observe** authorized platform metrics plus user labels and explicit QC results.
2. **Aggregate** with versioned, source-specific feature tables; require sufficient data/uncertainty.
3. **Hypothesize** a change: e.g. retain 3 more seconds before racing payoff, increase game HUD crop weight, change hook style, reduce caption crowding, adjust audio trigger when silent clutch false negatives high.
4. **Experiment** using pre-registered objective and source-/topic-stratified holdout. Log randomization, sample size and identity of control/treatment.
5. **Offline evaluate** on locked human-labeled clips for safety/quality; don't train on the same examples used to judge success.
6. **Shadow and canary deploy** low-risk policy, preserve rollback pointer; compare to prior model with matched conditions.
7. **Promote** only if improvement is credible and hard gates/regression tests still pass. Otherwise rollback and log failed hypothesis.

## Multi-objective optimization / guardrails
A high-view clip that is factually misleading, violates rights or repeatedly loses silent important events is NOT 'best'. Use constrained optimization: hard rights/security/publish rules; optimize human editorial pass, event recall/precision and viewer experience; minimize latency and cost under budget. Ranking score can be a configurable weighted model but its components and weights must be inspectable. Keep long-term creator diversity; avoid always selecting the most followed creator simply because their historic views dominate.

## Tests and evaluation
- Negative control: metrics API returns missing/zero/403/expired token; system distinguishes absence from literal zero.
- Quota/billing: avoid aggressive polling if account limits low; preserve next poll time.
- Simpson's paradox: global improvement may hide degradation for quiet-action game category; stratify.
- Data leakage: editor sees validation set labels? invalidate experiment / rotate holdout.
- Race: two metrics jobs write same post snapshot; unique `(post_id,metric,window,captured_at)` safeguards.
- Retention claim: API offers only `views`, model invents `second_12_dropoff`; must reject as unsupported.
- Feedback validity: new policy triggers more false positives and boosts views just by overposting; fail quality gate.
- Offline-to-online drift: model changed after fine-tuning; canary + rollback if production clip quality deteriorates.
- Cultural/language coverage: subtitle names/words correct across game voice chat and accents; human stratified review.

## Dashboard outcome panels
1. Event quality funnel: ingested hours, candidate count, labeled true highlights, bounded clips, rendered pass, machine QC fail, video QC fail, approved, published confirmed and reasons at each transition.
2. Performance cohorts: by creator/game/platform/time/clip story archetype and source freshness.
3. Reliability: stalled sources, queue age, error rates, p95 processing/publishing latency, alerts, retries and blocked duplicate attempts.
4. Research: current experiment, treatment, minimum sample, observed effect, uncertainty, status, next decision.
5. Money/resources: compute/API spend vs cap, storage and retention, revenue if available, account rate limits and publication rights expiration.
