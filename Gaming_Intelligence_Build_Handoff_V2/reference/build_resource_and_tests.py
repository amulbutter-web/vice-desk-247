import csv,json,hashlib,os,re,collections
from pathlib import Path
root=Path(__file__).resolve().parents[1]
base=root/'legacy'/'resources_v1.csv'
with base.open(newline='',encoding='utf-8') as f: old=list(csv.DictReader(f))
# keep original content as historical leads, and add a fresh research register with more relevant dimensions
new_resources=[
('R043','YouTube quota transition 2025/2026','publisher quota','https://developers.google.com/youtube/data/revision_history','OFFICIAL_DOC','replace 1600-unit blanket assumption','confirm account quotas and 100 uploads/day bucket','official update to upload quota billing', 'FR-022;FR-036','Phase5'),
('R044','YouTube quota endpoint overview','publisher quota','https://developers.google.com/youtube/data/getting-started','OFFICIAL_DOC','gating','read Google Cloud console quota & 429 behavior','100 upload calls/day and 100 search calls/day default separate buckets', 'FR-022;FR-036','Phase5'),
('R045','YouTube videos.insert docs','publisher technical','https://developers.google.com/youtube/data/reference/rest/v3/videos/insert','OFFICIAL_DOC','core','real private OAuth upload + verify remote processing','privacyStatus explicitly set private for tests', 'FR-022;FR-023','Phase5'),
('R046','YouTube unaudited-app private-only rule lifted clarification','publisher policy','https://issuetracker.google.com/issues/572863050','OFFICIAL_DOC','correct outdated claim','review current policy and upload statuses','Oct 2026 official clarification; other compliance still applies', 'FR-022;FR-023','Phase5'),
('R047','Instagram API with Instagram Login changelog','login/scopes','https://developers.facebook.com/docs/instagram/platform/instagram-api/changelog/','OFFICIAL_DOC','core','Instagram Login professional-account app/scopes and test','no Facebook Page needed for THIS flow; not the Facebook Login flow', 'FR-021','Phase5'),
('R048','Meta Instagram Login Postman collection','login/scopes','https://www.postman.com/meta/instagram/folder/1z5vxzu/instagram-api-with-instagram-login','OFFICIAL_DOC','core','verify active product permissions and media path','cannot use consumer accounts', 'FR-021','Phase5'),
('R049','Meta Instagram API Postman overview','Reel media specs and publish','https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api','OFFICIAL_DOC','core','real container processing/media publish/status','specs and API versions may change; account scopes required', 'FR-021;FR-023','Phase5'),
('R050','Twitch Clips endpoints','native live/VOD clips','https://dev.twitch.tv/docs/api/reference/clips','OFFICIAL_DOC','authorized source candidate','test creator/editor scopes + clip duration/source correctness','native 5-60s content cannot cover arbitrary-length event', 'FR-004;FR-006','Phase3'),
('R051','Twitch clip usage guide','native clip behavior','https://dev.twitch.tv/docs/api/clips/','OFFICIAL_DOC','source baseline','async result and download permission test','permissions and clip availability may block', 'FR-006','Phase3'),
('R052','Gemini video understanding','multimodal frames/audio','https://ai.google.dev/gemini-api/docs/video-understanding','OFFICIAL_DOC','video judge trial','compare default static 1fps to dynamic/high-fps inputs','1fps may miss fast gaming and flashed repo URLs', 'FR-007;FR-018;FR-038','Phase1'),
('R053','Gemini current API rate limits','API preflight','https://ai.google.dev/gemini-api/docs/rate-limits','OFFICIAL_DOC','budget/gates','measure exact account/model limits','free tier not assured for all models', 'FR-033;FR-034','Phase1'),
('R054','GitHub original PeakCut','live and uploaded skeleton','https://github.com/haziqahmedqasmi/PeakCut','REPO_DOCUMENTED','baseline alternative','run 21 test groups and game-media E2E on pinned SHA','prior tests are not live quality proof', 'FR-003;FR-004;FR-018','Phase1'),
('R055','OpenShorts open source core','reframing','https://github.com/moha700m/OpenShorts','REPO_DOCUMENTED','candidate component','check smart crop modes with gameplay HUD + license cloud exception','focus on talking heads, no blind source incorporation', 'FR-013;FR-014','Phase1'),
('R056','FujiwaraChoki/SupoClip','VOD clips + feedback','https://github.com/FujiwaraChoki/supoclip','REPO_DOCUMENTED','uploaded workflow/analytics candidate','test actual analytics, render, editing and posting; AGPL','does not handle live streams; AGPL obligations', 'FR-005;FR-027;FR-028','Phase1'),
('R057','cspenn/SupoClip','local clipping + vision options','https://github.com/cspenn/supoclip','REPO_DOCUMENTED','QA and local VLM candidate','Apple Silicon vs OCI ARM package + real VLM test','parakeet-mlx platform mismatch', 'FR-007;FR-018','Phase1'),
('R058','Concat programmable editor','advanced editor','https://github.com/tmenov/Concat-videoeditor','REPO_DOCUMENTED','optional renderer','JSON-RPC and ARM deployment plus actual media benchmark','beta complexity and heavy runtime', 'FR-013;FR-014','Phase1'),
('R059','SupoClip app guide on B-roll','editor inspiration','https://github.com/FujiwaraChoki/supoclip/blob/main/docs/app-guide.md','REPO_DOCUMENTED','optional','measure factual story effect and asset license','stock B-roll can degrade gaming authenticity', 'FR-014','Phase1'),
('R060','MAST paper NeurIPS','agent failure taxonomy','https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html','PRIMARY_RESEARCH','QA taxonomy','map all 14 failure modes to tests','not application-specific error rate', 'FR-019;FR-030','Phase0'),
('R061','MAST code/data','failure case definitions','https://multi-agent-systems-failure-taxonomy.github.io/MAST/','PRIMARY_RESEARCH','engineering pattern','build regression set from taxonomy','benchmark traces != clip results', 'FR-019;FR-030','Phase0'),
('R062','Hallucination Snowball preprint','handoff error propagation','https://arxiv.org/abs/2608.14588','PRIMARY_RESEARCH','QA guidance','typed gates across content transformations','finance domain, not gaming', 'FR-018;FR-030','Phase0'),
('R063','Beyond pass@1 preprint','long-horizon reliability','https://arxiv.org/abs/2603.29231','PRIMARY_RESEARCH','SRE guidance','repeat-run and duration-stratified reliability','domain-dependent, no automatic transfer', 'FR-025;FR-030','Phase0'),
('R064','VideoJudge preprint','video-aware evaluation','https://arxiv.org/abs/2509.21451','PRIMARY_RESEARCH','judge candidate','calibrate real gaming ratings and resources','not a drop-in output editor judge', 'FR-018','Phase1'),
('R065','Anthropic building effective agents','orchestrator vs evaluator optimizer','https://www.anthropic.com/research/building-effective-agents','PRIMARY_GUIDANCE','workflow design','test whether feedback improves edits vs baseline','complexity only when warranted', 'FR-019;FR-033','Phase0'),
('R066','Rockstar GTA VI official project launch','event timing reference','https://www.rockstargames.com/VI','OFFICIAL_DOC','context not system dependency','verify release platform and India unlock separately','date does not establish midnight local unlock', 'FR-001;FR-002','Phase0'),
('R067','Twitch Get Clips Download','authorized clip files','https://dev.twitch.tv/docs/api/reference/clips','OFFICIAL_DOC','source adapter','scope-test portrait/landscape links and expiry','not generic unrestricted media download', 'FR-006','Phase3'),
('R068','YouTube quota and compliance audits','quota extension','https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits','OFFICIAL_DOC','later scalability','test need of quota extension before scale','extra quota subject to audits', 'FR-022;FR-036','Phase7'),
('R069','Oracle Free Tier official details','24/7 allocation','https://www.oracle.com/cloud/free/','OFFICIAL_DOC','bootstrap host','check actual tenancy shape/region availability + ARM64','2 OCPU/12GB equivalent not 15-stream guarantee', 'FR-024','Phase7'),
('R070','Oracle Always Free official documentation','24/7 allocation','https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm','OFFICIAL_DOC','bootstrap reference','cost/volume/network and free tier limits','availability and hardware throughput unknown', 'FR-024','Phase7'),
('R071','OpenRouter model aggregator','fallback models','https://openrouter.ai/docs','PROVIDER_DOC','optional','test structured outputs, privacy, availability/cost','extra broker can increase failure surface', 'FR-033','Phase1'),
('R072','Groq Cloud docs','high-throughput inference','https://console.groq.com/docs/overview','PROVIDER_DOC','candidate API','compare ASR/text limits and task outputs','Groq service is not xAI Grok', 'FR-033','Phase1'),
('R073','xAI developer docs','Grok models','https://docs.x.ai/','PROVIDER_DOC','candidate API','actual video/vision/JSON support by model and pricing','model may be text only for some tasks', 'FR-033','Phase1'),
('R074','DeepSeek API docs','text/structured candidate','https://api-docs.deepseek.com/','PROVIDER_DOC','candidate API','verify text vs visual capability and rate','open-weights vs hosted API not same', 'FR-033','Phase1'),
('R075','FFmpeg documentation','deterministic media compiler','https://ffmpeg.org/documentation.html','OFFICIAL_DOC','core render','media probes/crop/subtitles + security tests','versions/encoders vary by platform', 'FR-013;FR-017','Phase2'),
]
rows=[]
for row in old:
    rows.append({**row,'feature_ids':'','phase':'','evidence_scope':'V1_LEAD','last_rechecked':'NOT_NEWLY_REVERIFIED','verified_by_v2':'NO'})
for id_,resource,role,url,status,disp,test,lim,fr,phase in new_resources:
    rows.append(dict(id=id_,resource=resource,project_role=role,url=url,evidence_status=status,disposition=disp,required_test=test,limitation=lim,feature_ids=fr,phase=phase,evidence_scope='V2_PUBLIC_SOURCE_ORIGINAL_URL',last_rechecked='2026-11-18',verified_by_v2='DOC_VIEW_ONLY'))
cols=list(rows[0])
with (root/'15_RESOURCE_EVIDENCE_INDEX.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
# User did not ask to create an implementation repo; failure cases are test design, not test code that was run.
fails={
'sources':[
('unlicensed stream','Source is public but not authorized','BLOCK before ingest; log creator permission needed','S0'),
('revoked license','Consent revoked after clip preview','STOP pending publish; quarantine release state','S0'),
('private group Reel','Instagram media requires private DM access','Do not bypass or claim extraction','S0'),
('source identity mismatch','Two similar channels/reused usernames','Reject until platform ID verified','S1'),
('trending unavailable','Platform API returns no public trending field','Expose method/unavailable not fake top rank','S1'),
('source reconnect','Source restarts with PTS discontinuity','New epoch, no corrupted stitched clip','S1'),
('clock drift','Source time vs UTC drift > threshold','Record drift and align via source clock','S1'),
('audio/video drift','Stream audio leads video 900 ms','Block or repair sync, rerun QC','S1'),
('last-buffer edge','Highlight starts before ring buffer','Flag missing lead-up, do not pretend complete','S1'),
('wrong source interleave','Two concurrent clips same timestamp','Do not merge across source IDs','S0')],
'detection':[
('silent action','Quiet but visually important clutch/stunt','Detect candidate with visual evidence','S1'),
('loud loading','Streamer screams over loading screen','Reject false-positive without gameplay','S1'),
('chat spam','One user floods chat metrics','Cap outlier effect; avoid fake highlight','S1'),
('ad interruption','Ad changes scenes, speech loud','Exclude or label ad from gameplay candidate','S1'),
('slow tension','Meaningful buildup then payoff over >60 seconds','Capture context not only last 30s','S1'),
('late detection','Trigger comes after peak','Use pre-roll and recovered onset','S1'),
('duplicate event','Two detectors flag overlapping segment','Merge within same source when identical','S2'),
('different streamer same time','Two sources peak at same UTC time','Independent candidate processing','S1'),
('screen UI popup','HUD change without significant gameplay','Do not overreact to trivial UI','S2'),
('multilingual audio','Hindi-English game voice chat','Keep correct named entities/no fabricated ASR','S1')],
'editing':[
('sentence cut','Start mid-critical sentence','Snap only if preserves story semantics','S1'),
('missing consequence','Clip cuts before landing/reaction','Include resolution or reject incomplete','S1'),
('fake chronology','Edit combines nonadjacent events misleadingly','Flag or explicitly label montage','S0'),
('out-of-range time','LLM proposes 200s for 180s media','Reject invalid plan before renderer','S1'),
('overlapping operations','Two incompatible crop intervals','Typed merge conflict prevents render','S2'),
('facecam over HUD','Facecam overlay covers score/minimap','Reposition or reject','S1'),
('tracking loss','Fast moving car leaves cropped frame','Correct ROI/review key interval','S1'),
('subtitle overflow','Multi-line caption clipped by UI controls','Safe area gate fails','S1'),
('ASR hallucinated quote','Video has no quote model invents dialogue','No invented subtitle; use verified audio','S0'),
('slowmo distortion','Slow motion distorts causal action or speech','Reject/evaluate alternate','S1'),
('unlicensed audio','Overlay music has no permission','Block asset and publication','S0'),
('frozen render','Output contains repeated frozen frames','Hard QC fails','S1')],
'quality':[
('black frame','Unintended black frame period after effect','Hard QC fails','S1'),
('AV silence','Accidental silent output where game audio expected','Hard QC fails','S1'),
('codec mismatch','Instagram wrong audio codec','Generate platform-specific variant','S1'),
('final-video unseen','Judge saw transcript only','Cannot mark multimodal QC complete','S1'),
('judge-generator collusion','Same model rubber stamps own edit','Independent calibration/human check','S1'),
('bad QC score threshold','7/10 chosen without calibration','Require actual human-label threshold test','S1'),
('repair loop runaway','QC returns same repair endlessly','Retry capped and escalation','S1'),
('repair regression','Second edit fixes crop but hides dialogue','Rerun full hard and editorial QC','S1'),
('lost provenance','Output lacks source media hash','Reject public release','S0'),
('model refuses media','Video model returns safety refusal','Queue human review, no fake score','S1')],
'publishing':[
('expired IG token','Instagram OAuth expired','Refresh scoped token or stop; no fake post','S1'),
('wrong login flow','Facebook Page requirement applied to Instagram Login','Select correct auth product','S1'),
('wrong account','Uploader posts to different creator account','Block mismatched account ID','S0'),
('IG quota reached','Meta quota endpoint reports none remaining','Delay/queue and notify','S1'),
('IG processing pending','Container created but no final media ID','Keep REMOTE_PROCESSING, not published','S1'),
('YT processing failed','Insert returns id but status rejected','Do not mark published','S1'),
('POST timeout after remote success','Client never sees 200','Reconcile remote before retry; no duplicate','S0'),
('concurrent outbox','Two workers acquire same publish intent','Row-level lease/unique prevents duplicate','S0'),
('rights expired between QC and publish','License revocation after approval','Recheck rights before submit','S0'),
('bad public media URL','Meta cannot fetch signed expiring URL','Repair URL and process after status check','S1')],
'ops':[
('disk full','Capture and renderer writes exhaust disk','Backpressure new intake, preserve pending assets','S1'),
('VM reboot','OCI server restarts at peak','State+media recovered and alerted','S1'),
('API 429 burst','Inference provider rate limited','Backoff, fail safe, maintain QC','S1'),
('provider hallucination','Judge returns fake source fact','Ground verify with video/audio references','S1'),
('SSRF URL','User supplies cloud metadata/private IP','Reject before fetch; revalidate redirects','S0'),
('prompt injection in chat','Chat tells agent reveal secrets','Ignore as data; no shell or secret access','S0'),
('model JSON malformed','LLM emits non-JSON or wrong keys','Schema reject/bounded retry','S2'),
('stale shared memory','Worker refers to prior streamer event','Use durable trace and IDs','S1'),
('background backlog','One active streamer floods candidates','Fair scheduling and bounded queues','S1'),
('missing backup','Snapshot exists but restore not tested','Run restore drill; no readiness claim','S1'),
('budget overrun','API costs escalate under retry loop','Enforce spend caps and alert','S1'),
('OCI ARM incompatibility','Model wheel only supports x86/mac','Fallback compatible model or remote worker','S1')],
'analytics':[
('retention unavailable','Platform exposes views but no per-second retention','Mark unavailable not estimated measured','S1'),
('missing metrics equals zero','403 is stored as zero views','Track denied/unavailable explicitly','S1'),
('freshness bias','1h post compared to 7day post','Age-match windows before conclusions','S2'),
('small sample hype','Three clips used to claim optimal length','No significant conclusion; caution','S1'),
('feedback loop drift','New policy causes silent-event misses','Canary+holdout catches and rollback','S1'),
('data leakage','Gold clips used in training and evaluation','Invalidate test and rerun holdout','S1'),
('global Simpson reversal','Global views increase, one genre decreases','Stratify genre/creator','S2'),
('duplicate metric poll','Concurrent cron inserts duplicate snapshots','Unique snapshot key/transaction','S2')],
'research':[
('caption mistaken for transcript','Reel caption used as full audio','Label caption-only','S1'),
('one-frame URL invented','Model guesses flashed GitHub link with no frame','Leave candidate/unverified','S1'),
('lookalike repo','Search finds similar repo different owner','Do not mark verified until exact identity','S1'),
('AGPL copied','SupoClip code copied without license review','Halt integration pending license decision','S0'),
('Ootto assumed working','MCP endpoint not actually tested','Defer/replace; no fake connector','S1'),
('17 vs 49 confusion','Citation totals treated as same inventory','Separate and reconcile with source','S1'),
]
}
with (root/'tests'/'failure_cases.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['test_id','stage','scenario','stimulus','expected_behavior','severity','evidence_needed','status'])
    k=0
    for stage,group in fails.items():
        for title,stim,expected,sev in group:
            k+=1;w.writerow([f'FT-{k:03}',stage,title,stim,expected,sev,'Test log + source fixture hash + observed output','NOT_RUN_TEST_DESIGN'])
print('resources',len(rows),'test cases',k,'stages', {s:len(v) for s,v in fails.items()})
