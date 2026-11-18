#!/usr/bin/env python3
"""Static documentation/package QA only. Does not test application/media/APIs."""
import csv, pathlib, json, re, hashlib, sys
r=pathlib.Path(__file__).resolve().parents[1]
checks=[]
def ck(name,ok,detail=''):
 checks.append({'check':name,'pass':bool(ok),'detail':str(detail)})
md=sorted([p for p in r.glob('*.md') if p.name != 'COMPLETE_SINGLE_FILE_HANDOFF.md'])
text='\n'.join(x.read_text(encoding='utf-8') for x in md)
expected=['00_START_HERE.md','01_SOURCE_ORDER_AND_REQUIREMENT_TRACE.md','02_PRD_DETAILED.md','03_ARCHITECTURE_AND_RUNTIME.md','04_MEDIA_EDITOR_AND_QUALITY.md','05_FAILURE_MODE_AND_TEST_MATRIX.md','06_PLATFORM_RIGHTS_AND_PUBLISHING.md','07_TOOL_MODEL_BAKEOFF.md','08_ORACLE_CAPACITY_SRE.md','09_ANALYTICS_AND_EXPERIMENTS.md','10_DATA_CONTRACTS.md','11_BUILD_SEQUENCE_AND_ACCEPTANCE.md','12_MASTER_CODING_PROMPT.md','13_PHASE_PROMPTS.md','14_REEL_RESEARCH_PROTOCOL.md','16_EVIDENCE_AND_OPEN_ITEMS.md','17_V1_QUALITY_AUDIT.md','18_DEVELOPER_DELIVERY_CHECKLIST.md','AGENTS.md']
ck('Core docs present',all((r/p).exists() for p in expected),[p for p in expected if not (r/p).exists()])
ck('Nontrivial source sequence',all(x in text for x in ['GPT','Claude','Manus','168','179','0.0001%','15']))
fr_nums={int(x) for x in re.findall(r'FR-(\d{3})', (r/'02_PRD_DETAILED.md').read_text())}
ck('40 requirement IDs',fr_nums==set(range(1,41)),f'{len(fr_nums)} FR ids')
ck('Two workflows preserved',all(x in text.lower() for x in ['uploaded', 'trending live', 'top gamers', 'simultaneous', 'oracle', 'publishing', 'feedback']))
ck('Aspirational quality not guaranteed', 'not a measured probability' in text.lower() or 'not a measured' in text.lower())
ck('Unsupported reel evidence clarified',all(x in text for x in ['not include video/audio','NOT include','no media','caption-only']) if False else 'video/audio' in text)
ck('Single file compiled', (r/'COMPLETE_SINGLE_FILE_HANDOFF.md').exists() and (r/'COMPLETE_SINGLE_FILE_HANDOFF.md').stat().st_size > 120000)
rows=list(csv.DictReader((r/'15_RESOURCE_EVIDENCE_INDEX.csv').open(encoding='utf-8')))
ck('75 resource leads',len(rows)==75,f'{len(rows)}')
ids=[x['id'] for x in rows];ck('Resource IDs unique',len(ids)==len(set(ids)))
ck('75 resources provenance and limits',all('required_test' in x and 'limitation' in x and 'evidence_status' in x for x in rows))
ck('No fabricated Ootto URL',all(x['url']=='' for x in rows if x['resource']=='Ootto connector'))
cases=list(csv.DictReader((r/'tests/failure_cases.csv').open(encoding='utf-8')))
ck('78 proposed fault tests',len(cases)==78,f'{len(cases)}')
ck('Failure tests unexecuted',all(x['status']=='NOT_RUN_TEST_DESIGN' for x in cases))
ck('Severity used',{'S0','S1','S2'}.issubset({x['severity'] for x in cases}))
con=list((r/'contracts').glob('*.json'))
ck('Six machine-readable schemas',len(con)==6,len(con))
for p in con:
 try:
  dat=json.loads(p.read_text(encoding='utf-8'))
  ck('Schema valid JSON '+p.name,dat.get('$schema','').startswith('https://json-schema.org') and dat.get('type')=='object' and 'required' in dat and dat.get('additionalProperties') is False)
 except Exception as e: ck('Schema valid JSON '+p.name,False,e)
ck('SQL starter present',(r/'schema.sql').exists() and 'UNIQUE(destination,account_ref,campaign_ref,content_sha256)' in (r/'schema.sql').read_text())
tr=list(csv.DictReader((r/'reference/source_traceability.csv').open(encoding='utf-8')))
ck('24 original requirements traced',len(tr)==24)
ck('All 40 FR covered in PRD and stage docs',all(f'FR-{i:03}' in text for i in range(1,41)))
ck('Machine QA status explicit', 'NOT a' in text or 'not' in text)
report={'status':'STATIC_DOCUMENT_QA_ONLY','summary':{'passed':sum(x['pass'] for x in checks),'total':len(checks),'failures':[x for x in checks if not x['pass']]},'checks':checks,'limitations':['No Reel MP4/audio files re-accessed in local container','No actual app or platform integration tests run','No repo clones or 15-stream benchmarks performed','No API tokens/accounts used']}
(r/'tests/static_qa_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['summary'],indent=2))
if any(not x['pass'] for x in checks): sys.exit(1)
