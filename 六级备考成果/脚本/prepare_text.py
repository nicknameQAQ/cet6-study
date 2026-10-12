import sys,json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'六级备考成果'/'数据'
sys.path.insert(0,str(DATA/'python_libs'))
sys.stdout.reconfigure(encoding='utf-8')
import fitz
IMG=ROOT/'六级备考成果'/'核验'/'源页'; IMG.mkdir(parents=True,exist_ok=True)
pages=[]; jobs=[]; inventory=[]
paths=[p for p in ROOT.rglob('*.pdf') if ('CET6' in str(p.relative_to(ROOT)) or '六级' in p.name or '六级' in str(p.parent.relative_to(ROOT))) and 'CET4' not in str(p) and '四级' not in str(p) and '六级备考成果' not in str(p)]
for p in paths:
    rel=str(p.relative_to(ROOT)); fid=hashlib.sha1(rel.encode()).hexdigest()[:12]
    m=re.search(r'(202\d)[年.\-](\d{1,2})',rel); session=f'{m[1]}-{int(m[2]):02d}' if m else 'unknown'
    m=re.search(r'第([123一二三])套|[（(]卷([一二三123])[）)]',p.name)
    suite=(m[1] or m[2]) if m else '1'; suite={'一':'1','二':'2','三':'3'}.get(suite,suite)
    kind='解析' if any(k in p.name for k in ['解析','详解','答案']) else '真题'
    d=fitz.open(p); low=0; current=suite
    for i,page in enumerate(d):
        txt=page.get_text('text',sort=True)
        if ('全3套' in p.name or '全三套' in p.name):
            ms=re.search(r'第\s*([123一二三])\s*套',txt[:350])
            if ms: current={'一':'1','二':'2','三':'3'}.get(ms[1],ms[1])
        key=f'{fid}_{i+1:03d}'; item={'id':key,'file':rel,'page':i+1,'session':session,'suite':current,'kind':kind,'text':txt,'method':'text','width':page.rect.width,'height':page.rect.height}
        if len(txt.strip())<80:
            low+=1; item['method']='ocr_pending'
            scale=min(2.5,1950/max(page.rect.width,page.rect.height))
            png=IMG/f'{key}.png'
            if not png.exists(): page.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False).save(png)
            jobs.append({'id':key,'image':str(png),'out':str(DATA/'ocr'/f'{key}.json')})
        pages.append(item)
    inventory.append({'file':rel,'session':session,'suite':suite,'kind':kind,'pages':len(d),'ocr_pages':low,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    print(session,suite,kind,len(d),'OCR',low,flush=True)
(DATA/'ocr').mkdir(exist_ok=True)
(DATA/'pages_raw.json').write_text(json.dumps(pages,ensure_ascii=False),encoding='utf-8')
(DATA/'ocr_jobs.json').write_text(json.dumps(jobs,ensure_ascii=False),encoding='utf-8')
(DATA/'资料清单.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
print('TOTAL',len(inventory),len(pages),'OCR',len(jobs),flush=True)
