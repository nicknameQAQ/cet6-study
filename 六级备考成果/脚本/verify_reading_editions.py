"""Validate reading scope, exact sentence translations, final PDFs and links."""
import sys,json,re,hashlib,collections
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'六级备考成果';D=R/'数据';QA=R/'核验/2026-10-27修订';QA.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(D/'python_libs'));sys.stdout.reconfigure(encoding='utf8')
import pymupdf as fitz
from PIL import Image,ImageDraw,ImageFont
def load(n):return json.loads((D/n).read_text(encoding='utf8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def norm(t):return re.sub('[^a-z0-9]','',t.lower())
def zh(t):return re.sub('[^\u3400-\u9fff0-9]','',t)

def verify(render=True):
 manifest=load('pdf_manifest.json');revision=load('reading_revision_pdf_manifest.json');changed={m['file'] for m in revision};old=load('验收报告.json');oldchecks={c['file']:c for c in old['pdf_checks']}
 archived=R/'历史版本/2026-10-27修订前';oldcore=json.loads((archived/'core_words_enriched1500.json').read_text(encoding='utf8'))
 core=load('core_words_enriched1500.json');reading=load('reading_words_enriched500.json');selected=load('阅读高频500选词.json');mapping=load('阅读优先配句映射.json');bank=load('阅读优先例句译文.json');chosen=load('阅读优先例句待译.json');W=load('word_statistics.json');rs=load('阅读正文词频统计.json')
 assert len(core)==len({r['word'] for r in core})==1500
 assert [r['word'] for r in core]==[r['word'] for r in oldcore]
 assert len(reading)==len({r['word'] for r in reading})==500
 assert len({r['word'] for r in reading}&{r['word'] for r in core})==336
 assert all(r['example']['reading_body'] for r in reading)
 assert sum(r['example']['reading_body'] for r in core)==1239
 assert set(chosen)<=set(bank)
 assert all(r['statistics']==o['statistics'] for r,o in zip(core,oldcore))
 from prepare_reading_oct27 import body_unit
 units={u['id']:u for u in load('corpus_units.json')};sl={s['id']:s for s in load('sentences.json')}
 for r,p in zip(reading,selected):
  k=r.get('corpus_lemma',r['word']);assert k==p['word'];s=rs[k]
  occ=[o for o in W[k]['occurrences'] if body_unit(units[o['unit']]) and not o['pos'].startswith('NNP')]
  assert len(occ)==s['count']==r['statistics']['exam_count'],k
  assert sum(s['categories'].values())==s['count']
  assert r['ipa_uk'] and r['meaning'] and r['example']['zh']
 assert [r['statistics']['exam_count'] for r in reading]==sorted([r['statistics']['exam_count'] for r in reading],reverse=True)
 source_errors=[];proofs=[];pagecache={(p['file'],p['page']):norm(p['text']) for p in load('pages_with_ocr.json')};pdfcache={}
 for sid,c in chosen.items():
  e=c['sentence'];pr=c.get('proof');passed=None
  if pr and pr.get('generated'):
   sp=pr['generated'];fn=sp['file'];start=sp.get('paragraph_start_page',sp['page'])
   if fn not in pdfcache:
    with fitz.open(ROOT/fn) as doc:pdfcache[fn]=[norm(p.get_text(clip=fitz.Rect(35,40,p.rect.width-30,p.rect.height-43))) for p in doc]
   passed=norm(e['text']) in ''.join(pdfcache[fn][start-1:start+4])
  elif pr:
   fn=pr['source']['file'];start=pr['page_start'];passed=norm(e['text']) in ''.join(pagecache.get((fn,p),'') for p in range(start,pr['page_end']+1))
  else:
   # Phrase-only examples retain the original source; do not promote them to
   # independently page-verified reading-body sentences.
   fn=e['sources'][0]['file'];start=e['sources'][0].get('page');passed=any(norm(e['text']) in pagecache.get((s['file'],s.get('page')),'') for s in e['sources'])
   if not passed:
    loc=next((x for x in load('句子来源页码核对.json') if x['sentence']==sid),None)
    if loc:
     fn=loc['file'];start=loc.get('paragraph_start_page',loc['page'])
     if fn not in pdfcache:
      with fitz.open(ROOT/fn) as doc:pdfcache[fn]=[norm(p.get_text(clip=fitz.Rect(35,40,p.rect.width-30,p.rect.height-43))) for p in doc]
     passed=norm(e['text']) in ''.join(pdfcache[fn][start-1:start+4])
  if not passed:source_errors.append(dict(sentence=sid,file=fn,page=start))
  proofs.append(dict(sentence=sid,source=fn,page=start,english_source_text_matches=bool(passed),translation=bank[sid]['zh'],translation_origin=bank[sid]['origin'],semantic_certification=False))
 save('阅读配句逐句出处核验.json',proofs)
 errors=[];glyphs=[];links=[];checks=[];sheets=[];rendered=0;font=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',16)
 if not render:
  # Reuse images only when every current PDF has the same checked hash and
  # the complete per-volume contact-sheet set from the full render exists.
  for m in revision:
   path=ROOT/m['file'];assert oldchecks[m['file']]['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
   contacts=sorted(QA.glob(path.stem+'_contact_*.jpg'));assert len(contacts)==(m['pages']+35)//36
   sheets.extend(str(p.relative_to(ROOT)) for p in contacts)
  rendered=sum(m['pages'] for m in revision)
 counts={m['file']:m['pages'] for m in manifest}
 for m in manifest:
  path=ROOT/m['file'];sha=hashlib.sha256(path.read_bytes()).hexdigest()
  if m['file'] not in changed:
   assert m['file'] in oldchecks and oldchecks[m['file']]['sha256']==sha,('unchanged PDF changed',m['file'])
   checks.append(oldchecks[m['file']]);continue
  with fitz.open(path) as doc:
   assert len(doc)==m['pages'] and doc.get_toc(),path.name
   if m['kind'] in ['core','reading_core']:assert len(doc)<=150
   if m['kind'] in ['core','reading_core']:
    rows=reading if m['kind']=='reading_core' else core
    volume=int(re.search(r'第(\d+)卷',path.name)[1]);group=rows[(volume-1)*100:volume*100]
    toc={title.split('  ',1)[1]:pn for level,title,pn in doc.get_toc() if re.match(r'^\d{4}  ',title)}
    assert len(toc)==100,(path.name,len(toc))
    for r in group:
     pn=toc[r.get('display_word',r['word'])];page=doc[pn-1].get_text();e=r['example']
     assert norm(e.get('display_text',e['text'])) in norm(page),('example not printed',path.name,r['word'])
     assert zh(e['zh']) in zh(page),('translation not printed',path.name,r['word'])
   batch=[];sheetno=0
   def flush():
    nonlocal sheetno
    if not batch:return
    sheetno+=1;im=Image.new('RGB',(1440,1980),'#e8ecf0');draw=ImageDraw.Draw(im)
    for j,(thumb,pn) in enumerate(batch):
     thumb.thumbnail((228,299));x=j%6*240;y=j//6*330;im.paste(thumb,(x+6,y+24));draw.text((x+5,y+3),str(pn),font=font,fill='black')
    dest=QA/f'{path.stem}_contact_{sheetno:02}.jpg';im.save(dest,quality=88);sheets.append(str(dest.relative_to(ROOT)));batch.clear()
   for pn,page in enumerate(doc,1):
    text=page.get_text()
    if len(text.strip())<10:errors.append(dict(file=m['file'],page=pn,issue='empty'))
    if '\ufffd' in text or '\x00' in text:glyphs.append(dict(file=m['file'],page=pn,issue='replacement character'))
    for b in page.get_text('dict')['blocks']:
     if b['type']!=0:continue
     for line in b['lines']:
      for sp in line['spans']:
       x0,y0,x1,y1=sp['bbox']
       if x0<39 or x1>page.rect.width-30 or y0<18 or y1>page.rect.height-18:errors.append(dict(file=m['file'],page=pn,issue='bounds',text=sp['text'],bbox=sp['bbox']))
       if any(ch in sp['text'] for ch in 'əɜɪʊʃʒθðŋæɒʌɑɔˈˌ') and 'Arial' not in sp['font']:glyphs.append(dict(file=m['file'],page=pn,issue='IPA not embedded in IPA font',text=sp['text']))
    for link in page.get_links():
     if link['kind']==fitz.LINK_GOTO and not 0<=link.get('page',-1)<len(doc):links.append(dict(file=m['file'],page=pn,issue='internal'))
     if link['kind']==fitz.LINK_GOTOR:
      dest=(path.parent/unquote(link['file'])).resolve()
      if not dest.exists():links.append(dict(file=m['file'],page=pn,issue='remote missing',target=str(dest)))
      else:
       total=counts.get(str(dest.relative_to(ROOT)))
       if total and not 0<=link.get('page',-1)<total:links.append(dict(file=m['file'],page=pn,issue='remote page'))
    if render:
     pix=page.get_pixmap(matrix=fitz.Matrix(.45,.45),alpha=False);batch.append((Image.frombytes('RGB',(pix.width,pix.height),pix.samples),pn));rendered+=1
     if len(batch)==36:flush()
     if pn in {1,3,4,10,len(doc)//2,len(doc)}:page.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(QA/f'{path.stem}_p{pn:03}.png')
   flush()
   if m['kind'] in ['quick_vocabulary','reading_quick']:
    source=reading if m['kind']=='reading_quick' else core
    words=[sp['text'].strip() for p in doc for b in p.get_text('dict')['blocks'] if b['type']==0 for l in b['lines'] for sp in l['spans'] if 'Arial-Bold' in sp['font']]
    assert words==[r.get('display_word',r['word']) for r in source],('quick sequence',path.name,len(words))
    for pstart in range(0,len(source),24):
     text=doc[pstart//24].get_text()
     for r in source[pstart:pstart+24]:assert zh(r.get('quick_meaning',r['meaning'])) in zh(text),('quick meaning',r['word'])
   checks.append(dict(file=m['file'],pages=len(doc),bookmarks=len(doc.get_toc()),links=sum(len(p.get_links()) for p in doc),sha256=sha))
  print('READING_QA',path.name,m['pages'],flush=True)
 old.update(pdf_files=len(manifest),pages=sum(m['pages'] for m in manifest),pdf_checks=checks,page_errors=errors,glyph_errors=glyphs,link_errors=links,core_words_checked=1500)
 old['oct27_revision']=dict(date='2026-10-30',files=[m['file'] for m in revision],rendered_pages=rendered,contacts=sheets,source_errors=source_errors,errors=errors+glyphs+links,core_words=1500,reading_words=500,overlap=336,unique_union=1664,core_reading_examples=1239,core_listening_examples=261,phrases=100,translations=len(bank),semantic_independent_teacher_review=False,visual_review='pending')
 # Earlier Chinese paragraph-source matching is superseded for the revised cards.
 old.setdefault('vocabulary_revision',dict(source_errors=[],visual_review='passed'))['current_source_validation']='oct27_revision: English source and sentence-only editorial translation tracked separately'
 old['rendered_pages']=old['pages']
 save('验收报告.json',old)
 print('FINAL_ERRORS',len(errors),len(glyphs),len(links),'SOURCES',len(source_errors),'RENDERED',rendered,flush=True)
 assert not errors and not glyphs and not links,(errors[:3],glyphs[:3],links[:3])
 assert not source_errors,source_errors[:8]
 return old
if __name__=='__main__':verify(render='--no-render' not in sys.argv)
