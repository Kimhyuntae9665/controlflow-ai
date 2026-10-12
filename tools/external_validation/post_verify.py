from pathlib import Path
from copy import deepcopy
import sys,shutil,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'external-test-output'
sys.path.insert(0,str(ROOT));import engine as e
result=json.loads((OUT/'result.json').read_text(encoding='utf-8'))
assert result['engine_unchanged_at_end']
failed=[err for err in result['errors'] if not err.get('retest_resolved_execution')]
assert len(result['documents'])+len(failed)==16
assert all(err.get('retest_attempted') for err in result['errors'])
manifest={x['id']:x for x in json.loads((OUT/'input-manifest.json').read_text(encoding='utf-8'))}
for err in failed:
    entry=manifest[err['id']]
    assert hashlib.sha256((OUT/'inputs'/entry['filename']).read_bytes()).hexdigest()==entry['input_sha256']
for d in result['documents']:
    assert hashlib.sha256((OUT/'inputs'/d['filename']).read_bytes()).hexdigest()==d['input_sha256']
    selected=OUT/'raw'/d.get('selected_response',d['id']+('.extract.retry1.raw.json' if d['attempt_count']==2 else '.extract.raw.json'))
    raw=json.loads(selected.read_text(encoding='utf-8'));parsed=json.loads(raw['message']['content'])
    # Prove report values are the actual last raw model output, never fixture substitutions.
    assert all(f['value']==parsed[f['name']]['value'] and f['quote']==parsed[f['name']]['quote'] for f in d['fields'])
    if d['group']!='baseline':assert all(c['status']!='pass' or all(next(f['supported'] for f in d['fields'] if f['name']==n) for n in next(x['fields'] for x in e.RCM if x['id']==c['id'])) for c in d['checks'])

isolation=Path(__file__).resolve().parent/'export-isolation'
saved=e.ROOT
try:
    records=[];baseline_export={'id':'AP002','attempted':False}
    for group in ['external','derived_scan','baseline']:
        groupdir=isolation/group;(groupdir/'evidence').mkdir(parents=True,exist_ok=True)
        docs=[d for d in result['documents'] if d['group']==group]
        for name in ['engine.py','make_evidence.py']:shutil.copyfile(ROOT/name,groupdir/name)
        for d in docs:shutil.copyfile(OUT/'inputs'/d['filename'],groupdir/'evidence'/d['filename'])
        e.ROOT=groupdir
        run={'id':'external-test-20261013-'+group+'-'+e.uuid.uuid4().hex[:8],'model':result['model']['name'],'digest':result['model']['digest'],'prompt_hash':'unchanged-engine:'+result['engine_sha256'],'fingerprint':e.source_fingerprint(),'documents':deepcopy(docs),'summary':{},'metrics':{}}
        run['result_fingerprint']=e.result_fingerprint(run);engine=e.Engine();engine.run=run;engine.persist()
        if group!='baseline':
            for d in run['documents']:
                engine.review({'run_id':run['id'],'document_id':d['id'],'decision':'request_info','reviewer':'외부 양식 자동화 QA','note':'공개 예시의 필드 원문 검증이 부족하여 추가 자료 요청. 실제 감사인 검토가 아닌 기능 테스트입니다.'})
                try:
                    engine.export({'run_id':run['id'],'document_ids':[d['id']],'reviewer':'외부 양식 자동화 QA','attestation':True})
                    records.append({'id':d['id'],'actual_export_blocked':False})
                except e.WorkflowError as err:records.append({'id':d['id'],'actual_export_blocked':err.code=='export_blocked','code':err.code,'message':str(err)})
        else:
            ap=next(d for d in run['documents'] if d['id']=='AP002')
            if ap['draft']['verified'] and all(f['supported'] for f in ap['fields']):
                engine.review({'run_id':run['id'],'document_id':'AP002','decision':'confirmed_exception','reviewer':'합성 기준점 자동화 QA','note':'합성 AP002의 발주·입고 1000.00과 청구 1100.00 차이 100.00을 대조한 기능 테스트입니다.'})
                packet=engine.export({'run_id':run['id'],'document_ids':['AP002'],'reviewer':'합성 기준점 자동화 QA','attestation':True})
                exported=json.loads((groupdir/'runs/latest-export.json').read_text(encoding='utf-8'))
                assert exported['population_document_count']==6 and exported['document_ids']==['AP002']
                baseline_export.update(attempted=True,export_succeeded=True,population_document_count=6,response=packet)
    assert all(x['actual_export_blocked'] for x in records)
    (OUT/'export-tests.json').write_text(json.dumps({'isolation':'same Engine.review/export with group-separated test-only ROOTs and fingerprints; original runs are untouched','external':records,'baseline':baseline_export,'execution_failures':[{'id':err['id'],'export_attempted':False,'reason':'No completed extraction run because the model request and explicit retest failed','model_error':err.get('retest_http_body',err['error'])} for err in failed]},ensure_ascii=False,indent=2),encoding='utf-8')
finally:e.ROOT=saved
print('PASS: 16 source hashes, final responses for completed documents,',len(records),'real export rejections,',len(failed),'model execution failure(s); baseline export:',baseline_export)
