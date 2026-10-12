"""Validate every revised page, all 1500 source examples, and portable links."""
import sys,json,re,hashlib,collections,os
from urllib.parse import unquote
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'六级备考成果';D=R/'数据';OUT=R/'学习资料';QA=R/'核验/1500词修订';QA.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(D/'python_libs'));sys.stdout.reconfigure(encoding='utf-8')
import pymupdf as fitz
from PIL import Image,ImageDraw,ImageFont
def load(n):return json.loads((D/n).read_text(encoding='utf-8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def norm(t):return re.sub('[^A-Za-z0-9]','',t).lower()
def normzh(t):return re.sub('[^\u4e00-\u9fff0-9]','',t)
def verify():
 manifest=load('pdf_manifest.json');old=load('验收报告.json');oldchecks={r['file']:r for r in old['pdf_checks']};checks=[];errors=[];glyph=[];linkerrs=[];sheets=[];allpages=0;rendered=0;font=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',16)
 revisions=[m for m in manifest if m['kind'] in ['core','guide','writing_translation']]
 pagecounts={m['file']:m['pages'] for m in manifest}
 for number,m in enumerate(manifest):
  path=ROOT/m['file'];sha=hashlib.sha256(path.read_bytes()).hexdigest()
  if m not in revisions:
   assert oldchecks[m['file']]['sha256']==sha,m['file'];checks.append(oldchecks[m['file']]);allpages+=m['pages'];continue
  doc=fitz.open(path);allpages+=len(doc);batch=[];sheetno=0;prefix=path.stem
  def flush():
   nonlocal sheetno
   if not batch:return
   sheetno+=1;canvas=Image.new('RGB',(1440,1980),'#e8ecf0');dr=ImageDraw.Draw(canvas)
   for j,(im,pn) in enumerate(batch):
    im.thumbnail((228,299));x=j%6*240;y=j//6*330;canvas.paste(im,(x+6,y+24));dr.text((x+5,y+3),f'p{pn}',font=font,fill='black')
   file=QA/f'{prefix}_contact_{sheetno:02}.jpg';canvas.save(file,quality=88);sheets.append(str(file.relative_to(ROOT)));batch.clear()
  if m['kind']=='core':assert len(doc)<=150,(m['file'],len(doc))
  assert doc.get_toc(),m['file']
  for pn,page in enumerate(doc,1):
   text=page.get_text();rendered+=1
   if len(text.strip())<10:errors.append(dict(file=m['file'],page=pn,reason='empty'))
   if '\ufffd' in text or '\x00' in text:glyph.append(dict(file=m['file'],page=pn,reason='missing glyph'))
   for b in page.get_text('dict')['blocks']:
    if b['type']!=0:continue
    for line in b['lines']:
     for sp in line['spans']:
      x0,y0,x1,y1=sp['bbox']
      if x0<40 or x1>page.rect.width-33 or y0<34 or y1>page.rect.height-14:errors.append(dict(file=m['file'],page=pn,reason='bounds',text=sp['text'][:90],bbox=sp['bbox']))
   for link in page.get_links():
    if link['kind']==fitz.LINK_GOTO and not 0<=link.get('page',-1)<len(doc):linkerrs.append(dict(file=m['file'],page=pn,reason='internal link'))
    if link['kind']==fitz.LINK_GOTOR:
     target=(path.parent/unquote(link['file'])).resolve()
     if not target.exists():linkerrs.append(dict(file=m['file'],page=pn,reason='missing remote',target=str(target)))
     else:
      rel=str(target.relative_to(ROOT));count=pagecounts.get(rel)
      if count and not 0<=link.get('page',-1)<count:linkerrs.append(dict(file=m['file'],page=pn,reason='remote page',target=rel))
   pix=page.get_pixmap(matrix=fitz.Matrix(.45,.45),alpha=False);batch.append((Image.frombytes('RGB',(pix.width,pix.height),pix.samples),pn))
   if len(batch)==36:flush()
   if pn in {1,3,4,6,len(doc)//2,len(doc)-4,len(doc)}:page.get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False).save(QA/f'{prefix}_p{pn:03}.png')
  flush();checks.append(dict(file=m['file'],pages=len(doc),bookmarks=len(doc.get_toc()),links=sum(len(p.get_links()) for p in doc),sha256=sha));doc.close();print('PAGE_QA',prefix,m['pages'],flush=True)
 # Every headword keeps an original sentence and an aligned whole paragraph.
 rows=load('core_words_enriched1500.json');assert len(rows)==len({r['word'] for r in rows})==1500
 W=load('word_statistics.json');SL={s['id']:s for s in load('sentences.json')};sources={};source_audit=[];locations=load('core_vocabulary_volume_index.json');proof_errors=[]
 for r in rows:
  k=r['word'];e=r['example'];assert e['id'] in SL and k in e['lemmata'],k
  assert r['statistics']['exam_count']==W[k]['exam_count'] and r['ipa_uk'],k
  assert r['synonyms'] or r.get('paraphrase'),('missing semantic support',k)
  assert e['text'] in e['paragraph_en'],('sentence paragraph',k)
  sp=e['paragraph_source'];fn=sp['file']
  if fn not in sources:
   d=fitz.open(ROOT/fn);sources[fn]=[p.get_text(clip=fitz.Rect(35,40,p.rect.width-30,p.rect.height-43)) for p in d];d.close()
  pages=sources[fn];start=sp.get('paragraph_start_page',sp['page']);found=None
  for end in range(start,min(start+4,len(pages))+1):
   joined=' '.join(pages[start-1:end])
   if norm(e['paragraph_en']) in norm(joined) and normzh(e['paragraph_zh']) in normzh(joined):found=end;break
  if found is None:proof_errors.append(dict(word=k,sentence=e['id'],source=fn,start=start))
  source_audit.append(dict(word=k,sentence=e['id'],source=fn,page_start=start,page_end=found,bilingual_text_matches=found is not None,study_file=locations[k]['file'],study_page=locations[k]['page']))
 replacement=load('writing_replacement_guidance.json');assert len(replacement['groups'])==100 and sum(r['kind']=='词' for r in replacement['groups'])==60 and len(replacement['exercises'])==32
 assert len(load('writing_analysis.json'))==39 and len(load('translation_originals.json'))==39
 assert all(r['example_origin'].startswith('自编') for r in replacement['groups'])
 assert len(load('写作翻译新版对照核验.json')['entries'])==78
 save('1500词原文逐条核验.json',source_audit)
 old.update(pdf_files=len(manifest),pages=allpages,pdf_checks=checks,page_errors=errors,glyph_errors=glyph,link_errors=linkerrs,core_words_checked=1500)
 old['vocabulary_revision']={'newly_rendered_pages':rendered,'contact_sheets':sheets,'source_examples':1500,'source_errors':proof_errors,'word_groups':60,'phrase_groups':40,'replacement_exercises':32,'core_volumes':15,'visual_review':'pending'}
 old['rendered_pages']=allpages;save('验收报告.json',old)
 print('REVISION_QA',json.dumps({'files':len(manifest),'new_pages':rendered,'layout':len(errors),'glyphs':len(glyph),'links':len(linkerrs),'source_errors':len(proof_errors)},ensure_ascii=False),flush=True)
 assert not errors and not glyph and not linkerrs,(errors[:4],glyph[:4],linkerrs[:4])
 assert not proof_errors,proof_errors[:6]
 return old
if __name__=='__main__':verify()
