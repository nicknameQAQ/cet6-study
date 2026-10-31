"""Generate the word/IPA-only edition and a self-contained writing workbook."""
import sys,json,re,hashlib,shutil,collections,os
from pathlib import Path
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'六级备考成果';D=R/'数据';OUT=R/'学习资料';QA=R/'核验/2026-10-20修订'
sys.path.insert(0,str(D/'python_libs'));sys.stdout.reconfigure(encoding='utf8')
import pymupdf as fitz
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph,PageBreak,Spacer,KeepTogether,Table,TableStyle,CondPageBreak
from PIL import Image,ImageDraw,ImageFont
import revise_vocabulary_pdfs as v
from reference_provenance import build_audit
from writing_replacements import build_data
from writing_expansion_oct20 import build_expanded

def load(n):return json.loads((D/n).read_text(encoding='utf8'))
def save(n,a):(D/n).write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')

def archive_previous():
 target=R/'历史版本/2026-10-20修订前';target.mkdir(parents=True,exist_ok=True)
 files=[OUT/'04_写作与翻译专项册.pdf',R/'使用说明.txt',D/'pdf_manifest.json',D/'验收报告.json']+[R/n for n in ['六级平板日常学习包.zip','六级平板完整资料包.zip','六级统计数据与复算脚本.zip']]
 for p in files:
  if p.exists() and not (target/p.name).exists():shutil.copy2(p,target/p.name)

def quick_edition():
 if (D/'阅读配句修订配置.json').exists():
  from make_reading_editions import quick_edition as current_quick
  return current_quick()
 rows=load('core_words_enriched1500.json');assert len(rows)==len({r['word'] for r in rows})==1500
 path=OUT/'06_核心词汇1500速记_仅单词与英音.pdf';c=Canvas(str(path),pagesize=A4,pageCompression=1)
 c.setTitle('核心词汇1500速记 - 单词与英音');c.setAuthor('六级学习资料整理')
 width,height=A4;locations=[]
 for start in range(0,1500,50):
  page=start//50+1
  if start%100==0:
   bookmark=f'v{start//100+1:02}';c.bookmarkPage(bookmark);c.addOutlineEntry(f'{start+1:04}-{start+100:04}',bookmark,0)
  for j,row in enumerate(rows[start:start+50]):
   x=40+(j//25)*266;y=height-57-(j%25)*29
   word=row['word'];ipa=row['ipa_uk'];ww=pdfmetrics.stringWidth(word,'IPABold',12);iw=pdfmetrics.stringWidth(ipa,'IPA',12)
   c.setFillColor(colors.black);c.setFont('IPABold',12);c.drawString(x,y,word)
   c.setFont('IPA',12)
   if ww+8+iw<=249:c.drawString(x+ww+8,y,ipa)
   else:c.drawString(x,y-13,ipa)
   locations.append(dict(word=word,ipa_uk=ipa,page=page,rank=start+j+1))
  c.setFont('IPA',9);c.setFillColor(colors.HexColor('#64748b'));c.drawRightString(width-40,26,str(page));c.showPage()
 c.save();save('1500词速记索引.json',locations)
 return dict(file=str(path.relative_to(ROOT)),title='1500词速记：仅单词与英音',kind='quick_vocabulary',pages=30)

ST={
 'body':ParagraphStyle('OctBody',fontName='CN',fontSize=12,leading=17,spaceAfter=6,wordWrap='CJK'),
 'en':ParagraphStyle('OctEN',fontName='IPA',fontSize=12,leading=17,spaceAfter=5),
 'small':ParagraphStyle('OctSmall',fontName='CN',fontSize=10.5,leading=14,spaceAfter=4,wordWrap='CJK',textColor=colors.HexColor('#566274')),
 'h1':ParagraphStyle('OctH1',fontName='CNBold',fontSize=19,leading=27,spaceAfter=10,keepWithNext=True,wordWrap='CJK'),
 'h2':ParagraphStyle('OctH2',fontName='CNBold',fontSize=14,leading=20,spaceBefore=5,spaceAfter=7,keepWithNext=True,wordWrap='CJK'),
 'label':ParagraphStyle('OctLabel',fontName='CNBold',fontSize=12,leading=17,spaceAfter=4,keepWithNext=True,textColor=colors.HexColor('#24596b')),
 'title':ParagraphStyle('OctTitle',fontName='CNBold',fontSize=27,leading=37,spaceAfter=20),
}
def P(t,style='body',markup=False):return Paragraph(t if markup else escape(str(t)).replace('\n','<br/>'),ST[style])
def H(t,key,level=0):
 p=P(t,'h1' if level==0 else 'h2');p.nav=(t,level,key);return p
def purpose(g):
 a=g['base']
 if a in ['think','believe','in my opinion','agree with','say','state']:return '表达观点'
 if a in ['because of','as a result','cause','lead to','be related to','result','affect','influence','make people aware of','make something better']:return '说明原因与影响'
 if a in ['different','on the other hand','even though','compared with','instead of']:return '比较与让步'
 if a in ['important','be important for','good','bad','healthy','valuable','enough','fair','special','advantage','ability','experience','easy','accurate','careful','clear','poor','old','be good at','be able to']:return '评价程度与能力'
 if a in ['try to','do something about','take part in','work together','deal with','protect','save','reduce','keep','build','limit','support','spend money on','provide somebody with something','get ready for','hand down']:return '提出措施'
 return '描述事实与活动'

def essay_pages():
 mapping={};state=False
 with fitz.open(OUT/'04_写作与翻译专项册.pdf') as doc:
  for level,title,pn in doc.get_toc():
   if level==1 and title.startswith('写作主题'):state=True
   elif level==1 and title.startswith('翻译主题'):state=False
   m=re.match(r'^(\d{4}-\d{2}-\d)\s',title)
   if state and level==2 and m:mapping[m[1]]=pn
 assert len(mapping)==39,len(mapping)
 return mapping

def replacements_edition(provenance):
 data=build_expanded(build_data());source_papers=load('writing_analysis.json');pages=essay_pages()
 from bs4 import BeautifulSoup
 texts={p['session']+'-'+p['suite']:' '.join(x.get_text(' ',strip=True) for x in BeautifulSoup((ROOT/p['web_source']).read_text(encoding='utf8'),'html.parser').select('#essay > p')) for p in source_papers}
 for g in data['groups']:
  g['function']=purpose(g);found=[]
  for p in source_papers:
   sid=p['session']+'-'+p['suite']
   if p['theme']!=g['theme']:continue
   expression=next((x for x in [g['base'],g['alternative']] if re.search(r'(?<![A-Za-z])'+re.escape(x)+r'(?![A-Za-z])',texts[sid],re.I)),None)
   if expression:found.append(dict(id=sid,expression=expression,url=provenance['writing',sid]['reference_url'],pdf_page=pages[sid],source_type='第三方范文中的表达观察；不是自编例句出处'))
  g['essay_observations']=found[:2]
 story=[P('写作同义替换与改写','title'),P('独立扩充版 · 140组指导 · 64道练习 · 2026-10-20','label'),P('保留原100组与32道练习；新增40组、32道练习、8个主题段落改写与16类常见误用。按8个主题学习，也可用用途索引查找。正文例句、改写与练习均为自编材料。范文观察另注明第三方来源，不计入真题频次。'),P('有些表达会改变程度、侧重点或范围。本册明确说明这些变化；不要求每句都换成更长的词。优先练准确、自然、能独立写出的表达。'),PageBreak(),H('目录','contents')]
 chapters=[('先检查意思与结构','method')]+[(t,'theme-'+str(i)) for i,t in enumerate(data['themes'],1)]+[('8个主题段落改写','paragraphs'),('16类常见误用','traps'),('按用途查表达','function-index'),('64道练习：先做题','exercises'),('集中答案与成立条件','answers')]
 for title,key in chapters:story.append(P(f'<link href="#{key}" color="#24596b">{escape(title)}</link>',markup=True))
 story.extend([PageBreak(),H('先检查意思与结构','method')])
 for a,b in [
  ('意义','替换后仍在说同一件事吗？相关不等于因果，意识提高不等于问题解决。'),
  ('程度','保留may/can/should、some/most/all等限制；important与essential、reduce与minimise有强弱差异。'),
  ('对象','谁做事，谁受影响，谁被替换？先画清主语和宾语，再调整句型。'),
  ('搭配','核对介词、可数性、to do/doing与词性；不用词长来代替语法检查。'),
  ('题目约束','原题要求照抄首句时，首句必须遵守原卷要求。可在自己写的后续句中练习替换。')]:story.append(P(a,'label'));story.append(P(b))
 story.append(P('每次15分钟：选3组 → 遮住改写句口头改写 → 完成2题 → 把其中1组写进自己的短段落。次日只复查写错的结构。无需一次背完140组。'))
 story.append(P('参考范文观察仅说明某个表达在第三方范文中出现，不证明该改写被官方认可，也不承诺使用某词即可获得特定分数。','small'))
 links=[]
 for ti,theme in enumerate(data['themes'],1):
  story.extend([PageBreak(),H(f'主题{ti:02} {theme}',f'theme-{ti}')])
  groups=[g for g in data['groups'] if g['theme']==theme]
  story.append(P('本主题条目：'+' · '.join(g['id'] for g in groups),'small'))
  for g in groups:
   block=[H(g['id']+' '+g['base']+' → '+g['alternative'],g['id'],1),P(g['kind']+'替换 · '+g['function']+(' · 本次新增' if g.get('added_in') else ''),'small'),P('语义与使用条件：'+g['distinction']),P('基础句（自编）','small'),P(g['before'],'en'),P(g['chinese_before']),P('改写句（自编）','small'),P(g['after'],'en'),P(g['chinese_after']),P('常见误用：'+g['misuse'])]
   for o in g['essay_observations']:
    tag=f'对照范文 {o["id"]} p{o["pdf_page"]}'
    block.append(P(tag+' · '+o['expression'],'small'));links.append(dict(text=tag,target='04_写作与翻译专项册.pdf',target_page=o['pdf_page']))
   story.append(KeepTogether(block));story.append(Spacer(1,8))
 story.extend([PageBreak(),H('8个主题段落改写','paragraphs'),P('以下均为自编段落。先理解内容，再比较哪些词值得换、哪些原句应保留。改写不补充虚构数据或个人经历。')])
 for i,p in enumerate(data['paragraphs']):
  if i:story.append(PageBreak())
  story.extend([H(p['id']+' '+p['theme'],p['id'],1),P('基础段（自编）','label'),P(p['before'],'en'),P('改写段（自编）','label'),P(p['after'],'en'),P('中文意思','label'),P(p['chinese']),P('逐处检查','label'),P(p['review']),P('迁移练习：保留本段逻辑，换成自己的主题与例子；核对may/can/should及主语关系。','small'),Spacer(1,40)])
 story.extend([PageBreak(),H('16类常见误用','traps')])
 for t in data['traps']:
  story.append(KeepTogether([H(t['id']+' '+t['title'],t['id'],1),P('错误或意义失真：'+t['wrong']),P('可用表达或处理：'+t['correct']),P(t['explanation'],'small'),Spacer(1,12)]))
 story.extend([PageBreak(),H('按用途查表达','function-index'),P('点击编号回到指导条目；主题分类与用途分类可以交叉使用。','small')])
 for name in ['表达观点','说明原因与影响','比较与让步','提出措施','评价程度与能力','描述事实与活动']:
  story.append(H(name,'function-'+str(len(story)),1))
  for g in [g for g in data['groups'] if g['function']==name]:story.append(P(f'<link href="#{g["id"]}" color="#24596b">{g["id"]} {escape(g["base"])} → {escape(g["alternative"])}</link>','small',True))
 story.extend([PageBreak(),H('64道练习：先做题','exercises'),P('每个主题8题。按提示改写；若提示改变了程度、范围或侧重点，需写明变化，不能只判断语法。允许符合语义条件的其他答案。答案集中放在后面。')])
 for ti,theme in enumerate(data['themes'],1):
  if ti>1:story.append(PageBreak())
  story.append(H(theme,'exercise-theme-'+str(ti),1))
  for e in [e for e in data['exercises'] if e['theme']==theme]:story.append(KeepTogether([P(e['id']+' '+e['prompt'],'en'),P(e['chinese']),P('使用提示：'+e['hint'],'small'),Spacer(1,28)]))
 story.extend([PageBreak(),H('集中答案与成立条件','answers')])
 for ti,theme in enumerate(data['themes'],1):
  if ti>1:story.append(PageBreak())
  story.append(H(theme,'answer-theme-'+str(ti),1))
  for e in [e for e in data['exercises'] if e['theme']==theme]:story.append(KeepTogether([H(e['id']+' 参考答案','answer-'+e['id'],1),P(e['answer'],'en'),P(e['answer_chinese']),P('成立条件与辨析：'+e['explanation']),P(f'<link href="#{e["replacement_id"]}" color="#24596b">回看指导 {e["replacement_id"]}</link>','small',True),Spacer(1,10)]))
 path=OUT/'07_写作同义替换独立扩充版.pdf';doc=v.Doc(path,'写作同义替换与改写 · 独立扩充版');doc.build(story)
 with fitz.open(path) as pdf:
  actual=[]
  for pn,page in enumerate(pdf,1):
   for link in links:
    if link['text'] in page.get_text():actual.append(dict(link,page=pn))
 v.remote_links(path,actual)
 save('writing_replacement_expanded.json',data)
 return dict(file=str(path.relative_to(ROOT)),title='写作同义替换与改写：独立扩充版',kind='writing_replacements',pages=doc.page)

def verify_and_render(revisions):
 QA.mkdir(parents=True,exist_ok=True);errors=[];checks=[];sheets=[];font=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',16)
 for m in revisions:
  path=ROOT/m['file'];doc=fitz.open(path);batch=[];sheet=0
  def flush():
   nonlocal sheet
   if not batch:return
   sheet+=1;im=Image.new('RGB',(1440,1980),'#e8ecf0');draw=ImageDraw.Draw(im)
   for j,(thumb,pn) in enumerate(batch):
    thumb.thumbnail((228,299));x=j%6*240;y=j//6*330;im.paste(thumb,(x+6,y+24));draw.text((x+4,y+3),f'p{pn}',font=font,fill='black')
   dest=QA/f'{path.stem}_contact_{sheet:02}.jpg';im.save(dest,quality=90);sheets.append(str(dest.relative_to(ROOT)));batch.clear()
  for pn,page in enumerate(doc,1):
   if '\ufffd' in page.get_text() or '\x00' in page.get_text():errors.append((path.name,pn,'glyph'))
   for block in page.get_text('dict')['blocks']:
    if block['type']!=0:continue
    for line in block['lines']:
     for sp in line['spans']:
      x0,y0,x1,y1=sp['bbox']
      if x0<34 or x1>page.rect.width-30 or y0<33 or y1>page.rect.height-14:errors.append((path.name,pn,'bounds',sp['text'][:70],sp['bbox']))
   for link in page.get_links():
    if link['kind']==fitz.LINK_GOTO and not 0<=link.get('page',-1)<len(doc):errors.append((path.name,pn,'internal link'))
    if link['kind']==fitz.LINK_GOTOR:
     from urllib.parse import unquote
     dest=path.parent/unquote(link['file'])
     if not dest.exists():errors.append((path.name,pn,'remote missing'))
     elif not 0<=link.get('page',-1)<len(fitz.open(dest)):errors.append((path.name,pn,'remote page'))
   pix=page.get_pixmap(matrix=fitz.Matrix(.45,.45),alpha=False);batch.append((Image.frombytes('RGB',(pix.width,pix.height),pix.samples),pn))
   if len(batch)==36:flush()
   if pn in {1,2,3,5,10,len(doc)//2,len(doc)-2,len(doc)}:page.get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False).save(QA/f'{path.stem}_p{pn:03}.png')
  flush();assert doc.get_toc(),path.name
  checks.append(dict(file=m['file'],pages=len(doc),bookmarks=len(doc.get_toc()),links=sum(len(p.get_links()) for p in doc),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
  if m['kind']=='quick_vocabulary':
   extracted=[sp['text'] for page in doc for b in page.get_text('dict')['blocks'] if b['type']==0 for l in b['lines'] for sp in l['spans'] if 'Arial-Bold' in sp['font']]
   expected=[r['word'] for r in load('core_words_enriched1500.json')];assert extracted==expected,('quick word order/count',len(extracted))
  doc.close();print('OCT20_PAGE_QA',path.name,m['pages'],flush=True)
 data=load('writing_replacement_expanded.json')
 with fitz.open(OUT/'07_写作同义替换独立扩充版.pdf') as doc:
  toc=doc.get_toc();headings=[t for _,t,_ in toc]
  assert len([t for t in headings if re.match('R\\d{3} ',t)])==140
  assert len([t for t in headings if re.match('P\\d{2} 参考答案',t)])==64
  assert all(any(t.startswith(p['id']+' ') for t in headings) for p in data['paragraphs'])
  assert all(any(t.startswith(p['id']+' ') for t in headings) for p in data['traps'])
 assert len(load('写作翻译新版对照核验.json')['entries'])==78
 print('OCT20_ERRORS',len(errors),errors[:6],flush=True);assert not errors,errors[:8]
 report=load('验收报告.json');byfile={r['file']:r for r in report['pdf_checks']};byfile.update({r['file']:r for r in checks})
 manifest=load('pdf_manifest.json');report['pdf_checks']=[byfile[m['file']] for m in manifest];report['pdf_files']=len(manifest);report['pages']=sum(m['pages'] for m in manifest);report['rendered_pages']=report['pages']
 report['oct20_revision']=dict(date='2026-10-20',files=[m['file'] for m in revisions],rendered_pages=sum(m['pages'] for m in revisions),errors=errors,contacts=sheets,quick_words=1500,groups=140,word_groups=80,phrase_groups=60,exercises=64,paragraphs=8,traps=16,source_records=78,semantic_independent_review_complete=False,visual_review='pending')
 save('验收报告.json',report);return report

def main():
 archive_previous();provenance=build_audit()
 import revise_writing_translation as writing
 result=writing.generate(include_replacements=False);writing.verify(result)
 new=[quick_edition(),replacements_edition(provenance)]
 manifest=load('pdf_manifest.json');manifest=[m for m in manifest if m['kind'] not in ['quick_vocabulary','writing_replacements']]+new;save('pdf_manifest.json',manifest)
 revised=[next(m for m in manifest if m['kind']=='writing_translation')]+new
 verify_and_render(revised)
 print('OCT20_DONE',json.dumps(revised,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
