from pathlib import Path
import hashlib, json, requests, concurrent.futures
import pymupdf as fitz

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'external-test-output'
ORIG=OUT/'originals'; INPUT=OUT/'inputs'; PREVIEW=OUT/'previews'
for p in [ORIG,INPUT,PREVIEW]: p.mkdir(parents=True,exist_ok=True)
SOURCES=[
 ('iras-self-billing.pdf','https://www.iras.gov.sg/media/docs/default-source/uploadedfiles/pdf/self-billing---samples-of-tax-invoice5cc6.pdf','IRAS 자가발행 송장 2종','영문 / SGD / 다중 페이지 표 / 공개 예시'),
 ('dhl-blank.pdf','https://www.dhl.com/content/dam/dhl/local/gb/dhl-global-forwarding/documents/pdf/gb-dgf-commercial-invoice-template.pdf','DHL 상업송장 빈 양식','영문 / 빈 양식 / PDF 문자 인코딩 점검'),
 ('pdflib-invoice.pdf','https://www.pdflib.com/fileadmin/cookbooks/PDFlib/results/invoice_pdfa2a.pdf','PDFlib 판매 송장','영문 / EUR / 제품 표 / 개발사 공개 예시'),
 ('apha-invoice.pdf','https://assets.publishing.service.gov.uk/media/67aca1d62b19f423678324b9/guidance-sample-invoice-scrapie__1_.pdf','영국 APHA 비용 청구 송장','영문 / GBP / 구매주문 참조 / 정부 예시'),
 ('canada-receipts.pdf','https://www.ised-isde.canada.ca/site/measurement-canada/sites/default/files/attachments/2022/V-27-eng.pdf','캐나다 연료 구매 영수증','영문 / 영수증 / 정부 예시'),
 ('missouri-po.pdf','https://samii.mo.gov/sites/g/files/zuston446/files/media/pdf/2022/07/SamplePurchaseOrder_9.22.16.pdf','미주리 구매주문서','영문 / 구매주문서 / 주 정부 예시'),
 ('nts-guide.pdf','https://www.nts.go.kr/comm/nttFileDownload.do?fileKey=e3ba086209818a4543d9eef7fd1c5d97','국세청 전자세금계산서 예시','한국어 / 전자세금계산서 안내서의 발급 화면'),
 ('revenue-bills.pdf','https://www.revenue.ie/en/starting-a-business/documents/revenue-guidance-understanding-your-bill.pdf','아일랜드 에너지 청구서','영문 / 이미지·텍스트 혼합 / 공급사 제공 공개 예시'),
]
def download(s):
    name,url,title,kind=s; p=ORIG/name
    if not p.exists():
        r=requests.get(url,timeout=80); r.raise_for_status()
        if not r.content.startswith(b'%PDF'): raise ValueError(f'{name}: not PDF {r.headers.get("Content-Type")}')
        p.write_bytes(r.content)
    d=fitz.open(p)
    text='\n'.join(x.get_text() for x in d)
    if "can't process your request" in text or 'permission to view this webpage' in text: raise ValueError('access error PDF')
    data={'filename':name,'url':url,'title':title,'kind':kind,'pages':len(d),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
    print(json.dumps(data,ensure_ascii=False),flush=True)
    if name in ['nts-guide.pdf','canada-receipts.pdf','missouri-po.pdf']:
        (ORIG/(name+'.text.txt')).write_text('\n'.join(f'\nPAGE {i+1}\n'+x.get_text() for i,x in enumerate(d)),encoding='utf-8')
    return data
def main():
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for f in concurrent.futures.as_completed([pool.submit(download,s) for s in SOURCES]):
            try: results.append(f.result())
            except Exception as e: print('DOWNLOAD FAILURE',str(e),flush=True)
    (OUT/'sources.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
