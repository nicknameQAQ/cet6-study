import sys,json,re,collections,hashlib,zipfile,datetime,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'六级备考成果'/'数据';OUT=ROOT/'六级备考成果'/'学习资料';QA=ROOT/'六级备考成果'/'核验';sys.path.insert(0,str(D/'python_libs'));sys.stdout.reconfigure(encoding='utf-8')
import pymupdf as fitz
from PIL import Image,ImageDraw,ImageFont
def load(n):return json.loads((D/n).read_text(encoding='utf-8'))
manifest=load('pdf_manifest.json');expected={str((ROOT/m['file']).resolve()) for m in manifest}
# Only remove stale generated index files, after verifying their absolute paths are inside the output folder.
for p in OUT.glob('05_完整索引_*.pdf'):
 if str(p.resolve()) not in expected and p.resolve().is_relative_to(OUT.resolve()):p.unlink()
reports=[];page_errors=[];glyph_errors=[];link_errors=[];sheets=[]
sheetdir=QA/'逐页版面';sheetdir.mkdir(exist_ok=True)
font=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',16)
cellw,cellh=205,306;cols,rows=6,6;batch=[];global_page=0
def flush_sheet():
 global batch
 if not batch:return
 sheet=Image.new('RGB',(cols*cellw,rows*cellh),'#e6e9ed');draw=ImageDraw.Draw(sheet)
 for j,(thumb,label) in enumerate(batch):
  x=(j%cols)*cellw;y=(j//cols)*cellh;sheet.paste(thumb,(x+(cellw-thumb.width)//2,y+25));draw.text((x+5,y+4),label,font=font,fill='black')
 path=sheetdir/f'pages_{len(sheets)+1:03d}.jpg';sheet.save(path,quality=88);sheets.append(str(path.relative_to(ROOT)));batch=[]
for fi,m in enumerate(manifest):
 p=ROOT/m['file'];doc=fitz.open(p);badpages=[]
 if m['kind']=='index' and len(doc)>150:page_errors.append({'file':m['file'],'issue':'index exceeds150','pages':len(doc)})
 if not doc.get_toc():link_errors.append({'file':m['file'],'issue':'missing bookmarks'})
 for pn,page in enumerate(doc):
  global_page+=1;dic=page.get_text('dict');text=page.get_text()
  if '\ufffd' in text or '\x00' in text:glyph_errors.append({'file':m['file'],'page':pn+1,'issue':'replacement character'})
  if len(text.strip())<10:page_errors.append({'file':m['file'],'page':pn+1,'issue':'empty page'})
  for block in dic['blocks']:
   if block['type']!=0:continue
   for line in block['lines']:
    for span in line['spans']:
     x0,y0,x1,y1=span['bbox']
     # CJK closing punctuation may hang one character outside the 48pt text frame.
     if x0<42 or x1>page.rect.width-35 or y0<35 or y1>page.rect.height-15:
      page_errors.append({'file':m['file'],'page':pn+1,'issue':'out of bounds','bbox':span['bbox'],'text':span['text'][:80]})
  for link in page.get_links():
   if link['kind']==fitz.LINK_GOTO and not (0<=link.get('page',-1)<len(doc)):link_errors.append({'file':m['file'],'page':pn+1,'issue':'invalid goto'})
  pix=page.get_pixmap(matrix=fitz.Matrix(.30,.30),alpha=False);thumb=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
  thumb.thumbnail((cellw-12,cellh-30));batch.append((thumb,f'{fi+1:02d}  p{pn+1}'))
  if len(batch)==cols*rows:flush_sheet()
  if pn in {0,1,len(doc)//2,len(doc)-1} and m['kind'] not in ['index','source_listening','source_reference']:
   page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(QA/f'终稿_{p.stem}_p{pn+1}.png')
 reports.append({'file':m['file'],'pages':len(doc),'bookmarks':len(doc.get_toc()),'links':sum(len(page.get_links()) for page in doc),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 print('QA',fi+1,len(manifest),p.name,len(doc),flush=True);doc.close()
flush_sheet()
core=load('core_words_with_source_pages.json');sents=load('sentences.json');sl={s['id']:s for s in sents};words=load('word_statistics.json')
expected_core=1500 if (D/'core_words_enriched1500.json').exists() else 500
assert len(core)==expected_core and len(load('core_phrases.json'))==100 and len(load('sentence_structures.json'))==40
assert len(load('translation_originals.json'))==39 and len(load('writing_prompts.json'))==39
assert len(load('translation_practice.json'))==20 and len(load('listening_worked_examples.json'))==10
for row in core:
 assert row['example']['id'] in sl and row['word'] in row['example']['lemmata'],row['word']
 assert any(sr.get('generated_pdf',{}).get('sentence_page_verified') for sr in row['example']['sources']),row['word']
 assert row['statistics']['exam_count']==words[row['word']]['exam_count']
for word,v in words.items():assert v['count']==len(v['occurrences']) and v['exam_count']+v['reference_count']==v['count'],word
pagesource=load('句子来源页码核对.json');assert all(r['sentence_page_verified'] for r in pagesource)
audio=[]
for n in (1,2):
 p=ROOT/'补充资料_2026年6月'/f'听力第{n}套.mp3';assert p.exists() and p.stat().st_size>1000000;audio.append({'file':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert audio[0]['sha256']!=audio[1]['sha256'],'audio files duplicated'
result={'pdf_files':len(manifest),'pages':global_page,'rendered_pages':global_page,'contact_sheets':sheets,'pdf_checks':reports,'page_errors':page_errors,'glyph_errors':glyph_errors,'link_errors':link_errors,'core_words_checked':expected_core,'source_sentences_verified':len(pagesource),'word_count_invariants_checked':len(words),'audio':audio,'notes':['PDF字体边界、缺字替代符、书签和内部跳转逐页检查。','逐页渲染联系表供人工版面检查；仅版面通过后再打包。']}
(D/'验收报告.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('QA SUMMARY',json.dumps({k:result[k] for k in ['pdf_files','pages','rendered_pages','core_words_checked','source_sentences_verified','word_count_invariants_checked']},ensure_ascii=False),flush=True)
print('ERRORS',len(page_errors),len(glyph_errors),len(link_errors),flush=True)
if expected_core==1500:
 from verify_vocabulary_revision import verify
 verify()
