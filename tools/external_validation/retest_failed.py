"""One explicit, recorded retest of a failed request; original failure remains in evidence."""
from pathlib import Path
import json,sys,re,time,urllib.error
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'external-test-output'
sys.path.insert(0,str(ROOT));import engine as e
data=json.loads((OUT/'result.json').read_text(encoding='utf-8'));manifest={x['id']:x for x in json.loads((OUT/'input-manifest.json').read_text(encoding='utf-8'))};started=time.perf_counter()
if any(err.get('retest_attempted') for err in data['errors']):raise RuntimeError('Explicit retest already recorded; preserve evidence rather than overwrite responses.')
initial_draft_failures=sum('wall_seconds' not in d['draft'] for d in data['documents'])
for error in data['errors']:
    error['retest_attempted']=True
    did=error['id'];entry=manifest[did];source=json.loads((OUT/'raw'/(did+'.source.json')).read_text(encoding='utf-8'));attempts=[]
    try:
        filename=did+'.extract.retest.raw.json'
        parsed,response=e.infer(e.EXTRACTION_SYSTEM,e.EXTRACTION_TASK+source['source_text'],e.SCHEMA,900,OUT/'raw'/filename);attempts.append(response);fields=e.ground_fields(parsed,source)
        failures=[{'field':f['name'],'issue':f['issue']} for f in fields if not f['supported'] and (f['value'] is not None or re.search(re.escape(e.LABELS[f['name']])+r'\s*:',source['source_text'],re.I))]
        if failures:
            repair='Previous attempt failed validation: '+e.canonical(failures)+'. Re-read and produce new JSON, not an explanation. Missing Approved by MUST be null; do not infer it from Created by. All non-null quotes MUST include their field labels.\n'+e.EXTRACTION_TASK+source['source_text']
            filename=did+'.extract.retest.retry1.raw.json'
            parsed,response=e.infer(e.EXTRACTION_SYSTEM,repair,e.SCHEMA,900,OUT/'raw'/filename);attempts.append(response);fields=e.ground_fields(parsed,source)
        d={**entry,**source,'fields':fields,'checks':[],'draft':None,'review':None,'json_parsed':parsed is not None,'attempt_count':len(attempts),'selected_response':filename,'extract_wall_seconds':round(sum(a['wall_seconds'] for a in attempts),3),'retest_after_http_failure':True}
        data['documents'].append(d);error['retest_resolved_execution']=True
        print(did,'explicit retest completed',flush=True)
    except Exception as ex:
        error['retest_resolved_execution']=False;error['retest_error']=str(ex)
        if isinstance(ex,urllib.error.HTTPError):error['retest_http_body']=ex.read().decode('utf-8',errors='replace')
        print(did,'explicit retest failed',str(ex),flush=True)
for group in ['external','derived_scan','baseline']:
    docs=[d for d in data['documents'] if d['group']==group];e.control_checks(docs)
    for d in docs:
        if d['draft'] is not None:continue
        did=d['id'];sources=[{'id':did+':p1','text':d['source_text']}]+[{'id':'RCM.'+c['id'],'text':c['procedure']} for c in e.RCM]
        ctx={'sources':sources,'control_results':d['checks'],'required_status_sentence':'; '.join(c['id']+'='+c['status'] for c in d['checks'])+'. Human review required.'}
        e.write_json(OUT/'raw'/(did+'.retrieval.json'),ctx)
        parsed,response=e.infer(e.DRAFT_SYSTEM,e.canonical(ctx),e.DRAFT_SCHEMA,150,OUT/'raw'/(did+'.draft.raw.json'))
        valid,issue=e.verify_draft(parsed,[s['id'] for s in sources],e.canonical(ctx),d['checks']);d['draft']={'text':parsed.get('text','') if isinstance(parsed,dict) else response.get('message',{}).get('content',''),'verified':valid,'issue':issue,'wall_seconds':response['wall_seconds']}
        d['export_blocked']=any(c['status']=='unknown' for c in d['checks']) or any(not f['supported'] for f in d['fields']) or not valid
    counts=Counter(c['status'] for d in docs for c in d['checks']);data['summary'][group]={'document_count':len(docs),'field_count':len(docs)*9,'grounded_fields':sum(f['supported'] for d in docs for f in d['fields']),'nonnull_model_fields':sum(f['value'] is not None for d in docs for f in d['fields']),'parsed_json_count':sum(d['json_parsed'] for d in docs),'draft_verified_count':sum(d['draft']['verified'] for d in docs),'check_statuses':dict(counts),'evidence_blocks':sum(d['export_blocked'] for d in docs)}
data['documents'].sort(key=lambda d:list(manifest).index(d['id']));data['failed_model_requests']=len(data['errors'])+sum(bool(err.get('retest_error')) for err in data['errors'])+initial_draft_failures;data['successful_model_responses']=len(list((OUT/'raw').glob('*.raw.json')));data['model_calls']=data['successful_model_responses']+data['failed_model_requests'];data['wall_seconds']+=round(time.perf_counter()-started,3)
data['request_count_scope']='Verified single initial execution plus at most one explicit retest per failed file, in a fresh raw directory. Counts reconstructed from preserved response files and captured failed stages, not a direct request telemetry ledger.'
data['explicit_retest_scope']='Only failed external request; unchanged model, prompts, schema and grounding; no value substitution. Original HTTP failure retained.'
e.write_json(OUT/'result.json',data)
