from prepare import ROOT,OUT,ORIG,INPUT,PREVIEW
import pymupdf as fitz
import json,hashlib,shutil

sources={x['filename']:x for x in json.loads((OUT/'sources.json').read_text(encoding='utf-8'))}
selections=[('EXT01','iras-self-billing.pdf',[1,2]),('EXT02','pdflib-invoice.pdf',[1]),('EXT03','apha-invoice.pdf',[1]),('EXT04','canada-receipts.pdf',[4]),('EXT05','missouri-po.pdf',[1,2]),('EXT06','nts-guide.pdf',[97]),('EXT07','revenue-bills.pdf',[25,26]),('EXT08','dhl-blank.pdf',[1])]
items=[]
for did,name,numbers in selections:
    src=fitz.open(ORIG/name); out=fitz.open()
    for n in numbers: out.insert_pdf(src,from_page=n-1,to_page=n-1)
    path=INPUT/(did+'.pdf');out.save(path);out.close()
    items.append({'id':did,'filename':path.name,'group':'external','source_pages':numbers,'transform':'page selection only; original content and annotations preserved','origin':sources[name]})
for did,base in [('OCR01','EXT01'),('OCR02','EXT06')]:
    original=next(x for x in items if x['id']==base);src=fitz.open(INPUT/(base+'.pdf'));out=fitz.open()
    for page in src:
        pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
        dst=out.new_page(width=page.rect.width,height=page.rect.height);dst.insert_image(dst.rect,stream=pix.tobytes('png'))
    out.save(INPUT/(did+'.pdf'));out.close()
    items.append({**original,'id':did,'filename':did+'.pdf','group':'derived_scan','parent':base,'transform':'200% rasterization of the selected pages, no text layer; not an independent public document'})
for n in range(1,7):
    did=f'AP{n:03}'; src=ROOT/'evidence'/(did+'.pdf');shutil.copyfile(src,INPUT/src.name)
    items.append({'id':did,'filename':src.name,'group':'baseline','source_pages':[1],'transform':'original fixture unchanged','origin':{'title':did+' 기존 합성 증빙','kind':'기존 6문서 합성 기준점','url':None,'filename':src.name,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()}})
for entry in items:
    p=INPUT/entry['filename'];entry['input_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    d=fitz.open(p); entry['input_pages']=len(d);entry['text_layer_chars']=[len(x.get_text().strip()) for x in d];entry['image_counts']=[len(x.get_images()) for x in d]
    for i,page in enumerate(d,1):page.get_pixmap(matrix=fitz.Matrix(1.3,1.3),alpha=False).save(PREVIEW/(entry['id']+f'-p{i}.png'))
(OUT/'input-manifest.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'documents':len(items),'external':8,'derived_scans':2,'baseline':6},ensure_ascii=False))
