import csv,pathlib
r=pathlib.Path(__file__).resolve().parents[1]
trace=[
('G01','GPT','Two discovery strategies','FR-001;FR-002;FR-003','Discovery lists with platform evidence and timestamps'),
('G02','GPT','Target 15 independently active streams','FR-004;FR-024','Measured 15 active ingest/event work/outputs'),
('G03','GPT','Natural clip length','FR-009;FR-010','Event start/buildup/peak/resolution, constraints separate'),
('G04','GPT','Expert-level creative edits','FR-013;FR-014;FR-015','Editor blind comparison and game HUD checks'),
('G05','GPT','Independent editor supervision','FR-017;FR-018;FR-019;FR-020','Actual video QC, bounded repair'),
('G06','GPT','Metadata and two-platform publishing','FR-016;FR-021;FR-022;FR-023','Real remote IDs and account statuses'),
('G07','GPT','Always-on cloud error infrastructure','FR-024;FR-025;FR-026','Crash, backup, 15-scale and alert evidence'),
('G08','GPT','Analytics as optimization loop','FR-027;FR-028','Metrics provenance, holdout, rollback'),
('G09','GPT','Uploaded video path same pipeline','FR-005;FR-007;FR-017','Owned upload-to-playable-quality clip'),
('G10','GPT','Working system not demo','FR-023;FR-024;FR-030','End-to-end proof and real publisher integration'),
('G11','GPT','15 roles responsibility graph','FR-003;FR-019;FR-025;FR-030;FR-033','Module mapping retained without 15 forced LLMs'),
('C01','Claude','Do not optimize away quality for API saving','FR-007;FR-013;FR-033;FR-034','Model/editor bakeoff quality first'),
('C02','Claude','Five primary difficult jobs','FR-009;FR-014;FR-018;FR-019;FR-028','Five stage audit and quality measures'),
('C03','Claude','Beyond hallucinations and branching','FR-019;FR-025;FR-030','State, handoffs, fault injection'),
('C04','Claude','0.0001% category aspiration','FR-030;FR-033','No fictitious error rates, rigorous tests'),
('C05','Claude','Compare all resources/providers','FR-033;FR-038;FR-039','Experiment-led plugin and provider selection'),
('C06','Claude','Code hard facts model creative judgments','FR-017;FR-019;FR-023','QC hard gates never bypassed'),
('C07','Claude','Research figures scoped','FR-030;FR-039','Evidence-level labels and paper boundaries'),
('C08','Claude','Human approval then calibrated autonomy','FR-020;FR-021;FR-022','Safe publishing controls'),
('M01','Manus','179/168/seven catalog count','FR-038','Caption-only source, no media claims'),
('M02','Manus','50-Reel task paused','FR-038','Keep not completed status'),
('M03','Manus','Prior PeakCut 21 test groups at SHA','FR-039','Rerun on actual environment; no E2E claim'),
('M04','Manus','17 vs 49 source count mismatch','FR-038;FR-039','Reconcile only from original rows'),
('M05','Manus','No authentic Reel MP4/audio frames','FR-038','No hidden link assertion'),
]
with (r/'reference'/'source_traceability.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f); w.writerow(['source_requirement','source_order','intention','mapped_FRs','acceptance_evidence']);w.writerows(trace)
decisions=[
('D01','First demo input','Owned/licensed uploaded video','rights and account not provided','owner authorization to external source','phase0'),
('D02','15 streaming target','Preserve 15 actively analyzed sources','measured capacity required','only owner can reduce product goal','phase7'),
('D03','Initial framework','Choose after PeakCut/OpenShorts/SupoClip bakeoff','licensing, runtime and render metrics','agent can select with proof','phase1'),
('D04','Publishing safety','Draft and manual approved private test','OAuth rights status unknown','owner authorizes real public publish','phase5'),
('D05','Reel hidden links','Unknown unless frame/audio observed','original export lacks media','user supplies lawful media or further evidence','phase0'),
('D06','Instagram login path','Inspect actual account and approved app product','two different Meta paths','owner supplies account/app access','phase5'),
('D07','LLM provider','Task-level tested, configurable model','Grok/Groq/DeepSeek/Gemini variants','agent can compare with approved budget','phase1'),
('D08','OCI shape','Always Free if available and measured','hardware quotas availability unknown','owner authorizes tenancy and paid fallback','phase7'),
('D09','Auto quality threshold','Calibrate after human labels','no demonstrated threshold','owner approves guarded-public automation','phase8'),
('D10','Business model','Preserve creator service and owned channel options','copyright/revenue uncertain','owner selects primary strategy','phase6'),
('D11','Audio/music/assets','Use only licensed/owned','licenses unspecified','owner/licensing confirmation','phase2'),
('D12','Review fixes','Default max 2 automatic repairs','must avoid infinite loops','agent may tune with test proof','phase4'),
]
with (r/'reference'/'decision_register.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['id','decision','safe_default','why_unresolved','requires_owner_action','build_phase']);w.writerows(decisions)
print('trace',len(trace),'decisions',len(decisions))
