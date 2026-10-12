"""Reuse unchanged engine functions. External documents have no fixture accuracy score."""
from pathlib import Path
import sys,json,time,re,hashlib,traceback
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'external-test-output'
sys.path.insert(0,str(ROOT))
import engine as e
from rapidocr import RapidOCR

def write(path,obj):e.write_json(path,obj)
def main():
    if (OUT/'result.json').exists() or any((OUT/'raw').glob('*.raw.json')):
        raise FileExistsError('Previous run evidence exists. Preserve it and choose a fresh OUT directory; raw responses must not be overwritten.')
    manifest=json.loads((OUT/'input-manifest.json').read_text(encoding='utf-8'))
    model=e.available()
    if not model:raise RuntimeError('original qwen2.5:1.5b unavailable; no model substitute')
    code=ROOT/'engine.py';initial_hash=hashlib.sha256(code.read_bytes()).hexdigest()
    raw=OUT/'raw';raw.mkdir(exist_ok=True);ocr=RapidOCR();started=time.perf_counter()
    result={'created_at':e.now(),'model':model,'engine_sha256':initial_hash,'unchanged_engine':True,'evaluation_scope':'External public samples plus explicitly derived scan variants; no operational or held-out accuracy claim','documents':[],'errors':[]}
    responses=[]
    for i,entry in enumerate(manifest):
        did=entry['id'];print(f'[{i+1}/{len(manifest)}] {did} READ + EXTRACT',flush=True)
        try:
            source=e.read_evidence(OUT/'inputs'/entry['filename'],ocr)
            write(raw/(did+'.source.json'),source)
            parsed,response=e.infer(e.EXTRACTION_SYSTEM,e.EXTRACTION_TASK+source['source_text'],e.SCHEMA,900,raw/(did+'.extract.raw.json'))
            responses.append(response);fields=e.ground_fields(parsed,source);attempts=[response]
            failures=[{'field':f['name'],'issue':f['issue']} for f in fields if not f['supported'] and (f['value'] is not None or re.search(re.escape(e.LABELS[f['name']])+r'\s*:',source['source_text'],re.I))]
            if failures:
                repair='Previous attempt failed validation: '+e.canonical(failures)+'. Re-read and produce new JSON, not an explanation. Missing Approved by MUST be null; do not infer it from Created by. All non-null quotes MUST include their field labels.\n'+e.EXTRACTION_TASK+source['source_text']
                parsed,response=e.infer(e.EXTRACTION_SYSTEM,repair,e.SCHEMA,900,raw/(did+'.extract.retry1.raw.json'))
                responses.append(response);attempts.append(response);fields=e.ground_fields(parsed,source)
            doc={**entry,**source,'fields':fields,'checks':[],'draft':None,'review':None,'json_parsed':parsed is not None,'attempt_count':len(attempts),'extract_wall_seconds':round(sum(x['wall_seconds'] for x in attempts),3),'prompt_tokens':sum(x.get('prompt_eval_count',0) for x in attempts),'output_tokens':sum(x.get('eval_count',0) for x in attempts)}
            result['documents'].append(doc)
            print(did,'grounded',sum(f['supported'] for f in fields),'/9','non-null',sum(f['value'] is not None for f in fields),'attempts',len(attempts),flush=True)
        except Exception as ex:
            result['errors'].append({'id':did,'error':str(ex),'traceback':traceback.format_exc(),'no_mock_fallback':True});print('ERROR',did,str(ex),flush=True)
        write(OUT/'partial-result.json',result)
    # Separate populations so source scan derivatives are never counted as duplicate transactions.
    for group in ['baseline','external','derived_scan']:
        docs=[d for d in result['documents'] if d['group']==group];e.control_checks(docs)
        for doc in docs:
            did=doc['id'];print(did,'CONTROL + DRAFT',flush=True)
            sources=[{'id':did+':p1','text':doc['source_text']}]+[{'id':'RCM.'+c['id'],'text':c['procedure']} for c in e.RCM]
            context={'sources':sources,'control_results':doc['checks'],'required_status_sentence':'; '.join(c['id']+'='+c['status'] for c in doc['checks'])+'. Human review required.'}
            write(raw/(did+'.retrieval.json'),context)
            try:
                parsed,response=e.infer(e.DRAFT_SYSTEM,e.canonical(context),e.DRAFT_SCHEMA,150,raw/(did+'.draft.raw.json'));responses.append(response)
                valid,issue=e.verify_draft(parsed,[s['id'] for s in sources],e.canonical(context),doc['checks'])
                doc['draft']={'text':parsed.get('text','') if isinstance(parsed,dict) else response.get('message',{}).get('content',''),'verified':valid,'issue':issue,'wall_seconds':response['wall_seconds']}
            except Exception as ex:doc['draft']={'text':'','verified':False,'issue':str(ex)}
            doc['export_blocked']=any(c['status']=='unknown' for c in doc['checks']) or any(not f['supported'] for f in doc['fields']) or not doc['draft']['verified']
            write(OUT/'partial-result.json',result)
    baseline=[d for d in result['documents'] if d['group']=='baseline']
    result['baseline_evaluation']=e.evaluate(baseline) if len(baseline)==6 else {'error':'not all baseline documents completed'}
    result['summary']={}
    for group in ['baseline','external','derived_scan']:
        docs=[d for d in result['documents'] if d['group']==group];counts=Counter(c['status'] for d in docs for c in d['checks'])
        result['summary'][group]={'document_count':len(docs),'field_count':len(docs)*9,'grounded_fields':sum(f['supported'] for d in docs for f in d['fields']),'nonnull_model_fields':sum(f['value'] is not None for d in docs for f in d['fields']),'parsed_json_count':sum(d['json_parsed'] for d in docs),'draft_verified_count':sum(d['draft']['verified'] for d in docs),'check_statuses':dict(counts),'evidence_blocks':sum(d['export_blocked'] for d in docs)}
    result['model_calls']=len(responses);result['wall_seconds']=round(time.perf_counter()-started,3)
    result['prompt_tokens']=sum(r.get('prompt_eval_count',0) for r in responses);result['output_tokens']=sum(r.get('eval_count',0) for r in responses)
    result['engine_unchanged_at_end']=hashlib.sha256(code.read_bytes()).hexdigest()==initial_hash
    write(OUT/'result.json',result);print(json.dumps(result['summary'],ensure_ascii=False),flush=True)
if __name__=='__main__': main()
