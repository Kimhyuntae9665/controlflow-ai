from pathlib import Path
import sys, json, hashlib, requests,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'external-test-output'
sys.path.insert(0,str(ROOT));import engine
specs=[('invoice-sample.xml','https://sdk.myinvois.hasil.gov.my/files/sdksamples/1.0-Invoice-Sample.xml'),('credit-note-sample.json','https://sdk.myinvois.hasil.gov.my/files/sdksamples/1.0-Credit-Note-Sample.json')]
results=[]
for name,url in specs:
    r=requests.get(url,timeout=40);r.raise_for_status();p=OUT/'inputs'/name;p.write_bytes(r.content)
    if name.endswith('.xml'):ET.fromstring(r.content)
    else:json.loads(r.content)
    try:
        source=engine.read_evidence(p,None); outcome={'accepted':True,'error':None,'expected_rejection':False,'mode':source['mode'],'pages':len(source['pages']),'text_chars':len(source['source_text']),'scope':'MuPDF document opening only; no UBL schema, signature, semantic mapping or model extraction validation'}
    except Exception as e:outcome={'accepted':False,'error_type':type(e).__name__,'error':str(e),'expected_rejection':True}
    results.append({'filename':name,'url':url,'sha256':hashlib.sha256(r.content).hexdigest(),'model_calls':0,**outcome})
(OUT/'format-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False))
