"""Render 15 annotated vocabulary volumes and a linked study guide."""
import sys,json,re,hashlib,shutil,os
from pathlib import Path
from xml.sax.saxutils import escape
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'六级备考成果';D=R/'数据';OUT=R/'学习资料';QA=R/'核验'/'1500词修订'
sys.path.insert(0,str(D/'python_libs'));sys.stdout.reconfigure(encoding='utf-8')
import pymupdf as fitz
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph,Spacer,PageBreak,KeepTogether,Table,TableStyle
from PIL import Image,ImageDraw,ImageFont
OLD=R/'脚本/build_pdfs.py'
prefix=OLD.read_text(encoding='utf-8').split('# Produce searchable paragraph-level sources')[0]
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith('W=load('))
ns={'__file__':str(OLD),'__name__':'vocabulary_styles'};exec(compile(prefix,str(OLD),'exec'),ns)
Doc=ns['Doc'];pdfmetrics.registerFont(TTFont('IPA',r'C:\Windows\Fonts\arial.ttf'));pdfmetrics.registerFont(TTFont('IPABold',r'C:\Windows\Fonts\arialbd.ttf'));pdfmetrics.registerFontFamily('IPA',normal='IPA',bold='IPABold',italic='IPA',boldItalic='IPABold')
ST={
 'body':ParagraphStyle('VBody',fontName='CN',fontSize=12,leading=17,spaceAfter=6,wordWrap='CJK'),
 'en':ParagraphStyle('VEnglish',fontName='IPA',fontSize=12,leading=17,spaceAfter=6),
 'small':ParagraphStyle('VSmall',fontName='CN',fontSize=10.5,leading=14,spaceAfter=5,wordWrap='CJK',textColor=colors.HexColor('#566274')),
 'h1':ParagraphStyle('VChapter',fontName='CNBold',fontSize=19,leading=27,spaceAfter=10,keepWithNext=True),
 'h2':ParagraphStyle('VWord',fontName='CNBold',fontSize=18,leading=25,spaceAfter=6,keepWithNext=True),
 'label':ParagraphStyle('VLabel',fontName='CNBold',fontSize=12,leading=17,spaceBefore=5,spaceAfter=4,keepWithNext=True,textColor=colors.HexColor('#24596B')),
 'title':ParagraphStyle('VTitle',fontName='CNBold',fontSize=27,leading=37,spaceAfter=16),
}
def load(n):return json.loads((D/n).read_text(encoding='utf-8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def clean(t):return re.sub('[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]',' ',str(t)).translate(str.maketrans({'−':'-','‐':'-','‑':'-','‒':'-','–':'-','—':'-','∅':'空'}))
def P(t,sty='body',markup=False):
 t=clean(t)
 if not markup:
  t=escape(t).replace('\n','<br/>')
  t=re.sub(r'/([^/<>\n]{1,85})/',lambda m:('<font name="IPA">/'+m[1]+'/</font>') if re.search('[əɜːɪʊʃʒθðŋæɒʌɑɔɛˈˌɡɚɐɹɝʔ]',m[1]) else m[0],t)
 return Paragraph(t,ST[sty])
def H(t,key,level=0):
 p=P(t,'h1' if level==0 else 'h2');p.nav=(t,level,key);return p
def label(t):return P(t,'label')
def save_pdf(path,title,story,kind):
 doc=Doc(path,title);doc.build(story)
 print('BUILD',path.name,doc.page,flush=True)
 return doc,dict(file=str(path.relative_to(ROOT)),title=title,kind=kind,pages=doc.page)
def index_map():
 result={}
 for p in sorted(OUT.glob('05_完整索引_*.pdf')):
  with fitz.open(p) as d:
   for level,w,pn in d.get_toc():
    if level==2:result[w]=dict(file=p.name,page=pn)
 return result
def remote_links(path,links):
 links=list({(x['page'],x['text'],x['target'],x['target_page']):x for x in links}.values())
 with fitz.open(path) as pdf:
  for r in links:
   p=pdf[r['page']-1]
   for rect in p.search_for(r['text']):p.insert_link({'kind':fitz.LINK_GOTOR,'from':rect,'file':r['target'],'page':r['target_page']-1,'to':fitz.Point(0,0)})
  for page in pdf:
   for link in page.get_links():
    if link['kind']==fitz.LINK_GOTOR:
     filename=unquote(link['file']);value=fitz.get_pdf_str(filename)
     pdf.xref_set_key(link['xref'],'A/F/UF',value);pdf.xref_set_key(link['xref'],'A/F/F',value)
  tmp=path.with_suffix('.linked.pdf');pdf.save(tmp,garbage=4,deflate=True)
 os.replace(tmp,path)
def short_item(t):return f"{t['word']}  {t['ipa_uk']}  {t['pos']} {t['meaning']}"
def volume_story(rows,vol,idx):
 tier='进阶与搭配突破' if vol<=10 else '熟词深化与查漏'
 title=f'核心词汇1500 · 第{vol:02d}卷'
 story=[P(title,'title'),P(tier+'  |  '+str(rows[0]['rank'])+'-'+str(rows[-1]['rank'])+'词','label'),P('先看英文自测，再读音标与真题语境。认识、听得出、会使用分别打勾；熟悉且能正确使用的条目可快速跳过。'),P('近义词按义项比较；部分术语使用释义转述，并明确说明不能原位互换。扩展词不计入1500个主词条，也不增加真题频次。'),P('英音为主。公开词表采用较细的音值记录，重音置于重读元音前的写法与学习词典略有差别。多音词另列词性读音。','small'),P('出处页码为PDF物理页码。跨文件跳转需要把完整学习资料放在同一文件夹；日常包未包含全部原文册时可按页码在完整包中查阅。','small'),PageBreak(),H('本卷目录','contents')]
 for j in range(0,len(rows),10):
  g=rows[j:j+10];key='group-'+str(g[0]['rank']);name=f"第{(g[0]['rank']-1)//10+1:03d}组  {g[0]['word']} - {g[-1]['word']}"
  story.append(P(f'<link href="#{key}" color="#24596B">{escape(name)}</link>',markup=True))
 story.append(PageBreak())
 for j,row in enumerate(rows):
  k=row['word'];e=row['example'];v=row['statistics']
  if j:story.append(PageBreak())
  if j%10==0:story.append(H(f"第{(row['rank']-1)//10+1:03d}组  {row['tier']}",'group-'+str(row['rank'])))
  story.append(H(f"{row['rank']:04d}  {k}",'word-'+k,1))
  tag=row.get('context_pos',e['pos'])
  pos={'CD':'num.','CC':'conj.'}.get(tag) or {'N':'n.','V':'v.','J':'adj.','R':'adv.','I':'prep./conj.','M':'modal','D':'限定词'}.get(tag[:1],tag)
  story.append(P('英 '+row['ipa_uk']+'   '+pos+' '+row['meaning']))
  if row['sound_note']:story.append(P(row['sound_note'],'small'))
  story.append(P(f"真题 {v['exam_count']}次 · 覆盖 {v['exam_coverage']}考次 · 2024-2026年 {v['exam_recent']}次 · 参考表达另计 {v['reference_count']}次",'small'))
  story.append(P('题型：'+'；'.join(t+str(v['categories'].get(t,0)) for t in ['听力原文','听力选项','阅读真题','作文题干']),'small'))
  story.append(P('真题搭配：'+' / '.join(x['phrase'] for x in row['collocations'])))
  story.append(label('真题语境 · 完整双语段落'))
  # Full aligned paragraphs avoid incorrectly presenting a paragraph translation
  # as though it translated only the single extracted example sentence.
  en=escape(e['paragraph_en']);pattern=r'(?<![A-Za-z])('+re.escape(e['form'])+r')(?![A-Za-z])';en=re.sub(pattern,r'<b>\1</b>',en,flags=re.I)
  story.append(P(en,'en',True));story.append(P(e['paragraph_zh']))
  src=e['sources'][0];sp=e['paragraph_source'];source_label=Path(sp['file']).name
  story.append(P(f"{src['session']} 第{src['suite']}套 · {e['category']} · {src['locator']}",'small'))
  story.append(P(f"原文页：{source_label} p{sp.get('paragraph_start_page',sp['page'])}",'small'))
  original=src.get('local_pdf_match') or src.get('local_prompt_pdf')
  if original:story.append(P('本地原卷：'+Path(original['file']).name+' p'+str(original.get('page') or original.get('page_range')),'small'))
  story.append(label('近义辨析 / 释义转述'))
  if row['synonyms']:
   for a in row['synonyms']:story.append(P(short_item(a)))
   story.append(P(row['synonym_note']));story.append(P(row['substitution'],'small'))
  elif row.get('paraphrase'):
   t=row['paraphrase'];story.append(P('释义转述','small'));story.append(P(t['english'],'en'));story.append(P(t['chinese']));story.append(P(t['note'],'small'))
  else:story.append(P('本义暂无适合直接替换的常用近义词，以双语语境理解。'))
  story.append(label('形近易混'))
  if row['confusables']:
   for a in row['confusables']:story.append(P(short_item(a)));story.append(P('拼写变化：'+a['spelling_difference'],'small'))
  else:story.append(P('本条未列常见形近易混词。','small'))
  story.append(label('同词根与派生拓展'))
  if row['families']:
   for a in row['families']:story.append(P(short_item(a)));story.append(P(a['relation'],'small'))
  else:story.append(P('未收录已核实的常用派生词；不据拼写相似推断同根。','small'))
  target=idx[k];story.append(P(f"全部出处：{target['file']} p{target['page']}",'small'))
  story.append(P('认识[ ]  听辨[ ]  会用[ ]    次日[ ]  3日[ ]  7日[ ]  14日[ ]','small'))
  story.append(Spacer(1,6))
 story.append(PageBreak());story.append(H('本卷字母索引','alphabet'))
 for r in sorted(rows,key=lambda x:x['word']):story.append(P(f'<link href="#word-{r["word"]}" color="#24596B">{r["word"]}  ·  {r["rank"]:04d}</link>','body',True))
 return title,story
def guide(rows,locations,idx):
 story=[P('六级1500词使用指南','title'),P('公开学习资料','label'),P('按主题阅读学习册，使用跨卷索引核对词汇和出处。')]
 story.append(H('如何使用新版词汇页','cards'))
 for t in ['每词包含英音、词性、词义、真题搭配、完整双语语境和来源位置。较长词条允许跨页，保持正文可读。','近义辨析注明适用义项与结构限制；无可靠单词近义词的术语提供释义转述，并标明不能原位互换。','同根关系与形近关系分开。派生词是另一个词条，不与主词合并词频。拓展词的出现频率不冒充主词频率。','音标中的重音符号指示后续音节或元音重读。公开英音词表的细音值记法与学习词典可能不同；词性变音另行说明。','原句采用完整段落，是为了让英文与中文准确对照。范文、参考译文与自编练习不计入真题正文频次。','PDF正文可搜索、可批注。目录跳转在单个文件内有效；跨文件链接依赖阅读器支持，并需保留同目录文件名。']:story.append(P(t))
 story.append(H('写作100组替换的练法','writing'))
 for t in ['写作册保留39篇范文与39道翻译双语对照、19个主题词库、40个句式和原20道翻译练习。','新增60组单词替换、40组短语替换，按8个作文主题组织；32道新练习单独集中给出答案。','先遮住改写例句，只看基础句和目标表达自己改写；再对照中文检查主语、因果、程度和范围。','important→essential、reduce→minimise等可能增强程度；词更长不意味着表达更准确。','每组新例句均明确标为自编练习。匹配到的已有范文出处用于回到真实主题语境。']:story.append(P(t))
 story.append(H('统计口径与资料来源','method'))
 for t in ['统计范围：2021年至2026年6月的70份六级PDF，共1027个输入页面；192页使用OCR。学习重点为2024-2026年。','保留9153个可靠索引词条；15条编码残缺原句未计入可靠统计。此次词汇扩展不重计或改变原有真题频次。','试卷正文、听力原文、参考范文和参考译文分开计数。相同材料去重后保留各套出处；单复数和时态等屈折变化合并，派生词单列。','扩展资料：ECDICT中英词典、Princeton WordNet词义及派生关系、open-dict-data英音词表。编辑辨析与释义转述已标明，不视作真题原文。','补充音频保留2026年6月两套；其他年份音频仍按原资料文件夹存放。写作与翻译参考表达来自第三方，不是唯一答案。']:story.append(P(t))
 for title,url in [('英音词表与来源许可','https://github.com/open-dict-data/ipa-dict'),('WordNet','https://wordnet.princeton.edu/'),('ECDICT','https://github.com/skywind3000/ECDICT'),('六级成绩解释','https://cet.neea.cn/html1/folder/19081/5124-1.htm')]:story.append(P(f'<link href="{url}" color="#24596B">{title}</link>','small',True))
 story.append(PageBreak());story.append(H('1500词跨卷索引','cross-index'));story.append(P('V01表示第01卷。点击卷页标签可打开对应文件；阅读器不支持时可按卷号和物理页码手动查找。','small'))
 links=[]
 for letter in 'abcdefghijklmnopqrstuvwxyz':
  group=[r for r in sorted(rows,key=lambda x:x['word']) if r['word'].startswith(letter)]
  if not group:continue
  story.append(H(letter.upper(),'letter-'+letter,1));cells=[]
  for i in range(0,len(group),2):
   line=[]
   for r in group[i:i+2]:
    loc=locations[r['word']];tag=f"V{loc['volume']:02d} p{loc['page']:03d}";line.extend([P(r['word'],'en'),P(tag,'small')]);links.append(dict(text=tag,target=loc['file'],target_page=loc['page']))
   if len(line)==2:line.extend([P(''),P('')])
   cells.append(line)
  table=Table(cells,colWidths=[160,89,160,90]);table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),1),('RIGHTPADDING',(0,0),(-1,-1),3),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]));story.append(table)
 story.append(PageBreak());story.append(H('完整出处索引的文件代码','files'))
 for x in load('source_id_catalogue.json'):story.append(P(x['id']+'  '+x['file'],'small'))
 target=OUT/'00_使用指南与备考安排.pdf';doc,m=save_pdf(target,'六级1500词使用指南',story,'guide')
 docpdf=fitz.open(target);bytag={x['text']:x for x in links};actual=[]
 for pn,page in enumerate(docpdf,1):
  for tag in re.findall(r'V\d{2} p\d{3}',page.get_text()):
   if tag in bytag:actual.append(dict(bytag[tag],page=pn))
 docpdf.close();remote_links(target,actual)
 return m
def generate(update_manifest=True):
 QA.mkdir(parents=True,exist_ok=True);rows=load('core_words_enriched1500.json');assert len(rows)==1500
 archive=R/'历史版本'/'1500词修订前';archive.mkdir(parents=True,exist_ok=True)
 for name in ['01_核心词汇_1.pdf','01_核心词汇_2.pdf','01_核心词汇_3.pdf','00_使用指南与备考安排.pdf','04_写作与翻译专项册.pdf']:
  p=OUT/name
  if p.exists() and not (archive/name).exists():shutil.copy2(p,archive/name)
 idx=index_map();locations={};manifest=[]
 for vol in range(1,16):
  group=rows[(vol-1)*100:vol*100];name=f'01_核心词汇1500_第{vol:02d}卷.pdf';path=OUT/name;title,story=volume_story(group,vol,idx);doc,m=save_pdf(path,title,story,'core');manifest.append(m)
  assert doc.page<=150,(vol,doc.page)
  for level,heading,pn in doc.nav:
   match=re.match(r'^\d{4}  (\S+)$',heading)
   if match:locations[match[1]]=dict(file=name,page=pn,volume=vol)
  links=[];pdf=fitz.open(path)
  for pn,page in enumerate(pdf,1):
   text=page.get_text();normal=re.sub(r'\s+','',text)
   for r in group:
    target=idx[r['word']];tag=f"全部出处：{target['file']} p{target['page']}"
    if re.search(re.escape(re.sub(r'\s+','',tag))+r'(?!\d)',normal):links.append(dict(page=pn,text=target['file'],target=target['file'],target_page=target['page']))
   for r in group:
    sp=r['example']['paragraph_source'];fname=Path(sp['file']).name
    start=sp.get('paragraph_start_page',sp['page']);tag='原文页：'+fname+'p'+str(start)
    if re.search(re.escape(tag)+r'(?!\d)',normal):links.append(dict(page=pn,text=fname,target=fname,target_page=start))
  pdf.close();remote_links(path,links)
 assert len(locations)==1500,len(locations);save('core_vocabulary_volume_index.json',locations)
 manifest.append(guide(rows,locations,idx));save('vocabulary_revision_pdf_manifest.json',manifest)
 if update_manifest:
  original=[m for m in load('pdf_manifest.json') if m['kind'] not in ['core','guide']];save('pdf_manifest.json',original+manifest)
  # Move only these known generated old books into the verified archive directory.
  for name in ['01_核心词汇_1.pdf','01_核心词汇_2.pdf','01_核心词汇_3.pdf']:
   p=(OUT/name).resolve();dest=(archive/name).resolve()
   assert p.is_relative_to(OUT.resolve()) and dest.is_relative_to(archive.resolve())
   if p.exists() and dest.exists():p.unlink()
 return manifest
if __name__=='__main__':generate()
