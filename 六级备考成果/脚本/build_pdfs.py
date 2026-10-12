import sys,json,re,collections,math,os,datetime,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'六级备考成果'/'数据';OUT=ROOT/'六级备考成果'/'学习资料';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(D/'python_libs'));sys.stdout.reconfigure(encoding='utf-8')
import pymupdf as fitz
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,PageBreak,KeepTogether,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.sax.saxutils import escape
from bs4 import BeautifulSoup
pdfmetrics.registerFont(TTFont('CN',r'C:\Windows\Fonts\simsun.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('CNBold',r'C:\Windows\Fonts\simhei.ttf'))
def load(n):return json.loads((D/n).read_text(encoding='utf-8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
W=load('word_statistics.json');S=load('sentences.json');SL={s['id']:s for s in S};U=load('corpus_units.json');UL={u['id']:u for u in U};CORE=load('core_words.json');PHRASES=load('core_phrases.json');CONCEPTS=load('translation_concepts.json');WRITING=load('writing_analysis.json');SUMMARY=load('corpus_summary.json')
styles={
'body':ParagraphStyle('Body',fontName='CN',fontSize=13,leading=20,spaceAfter=8,wordWrap='CJK'),
'index':ParagraphStyle('Index',fontName='CN',fontSize=12,leading=17,spaceAfter=4,wordWrap='CJK'),
'small':ParagraphStyle('Small',fontName='CN',fontSize=11,leading=16,spaceAfter=6,wordWrap='CJK',textColor=colors.HexColor('#566274')),
'title':ParagraphStyle('Title',fontName='CNBold',fontSize=25,leading=36,spaceAfter=20,wordWrap='CJK',textColor=colors.black),
'h1':ParagraphStyle('H1',fontName='CNBold',fontSize=18,leading=26,spaceBefore=12,spaceAfter=10,keepWithNext=True,wordWrap='CJK'),
'h2':ParagraphStyle('H2',fontName='CNBold',fontSize=15,leading=22,spaceBefore=10,spaceAfter=6,keepWithNext=True,wordWrap='CJK'),
'quote':ParagraphStyle('Quote',fontName='CN',fontSize=13,leading=20,spaceAfter=8,wordWrap='CJK',textColor=colors.HexColor('#183D58')),
}
def P(text,style='body',markup=False):
 text=str(text)
 text=re.sub('[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]',' ',text)
 text=text.translate(str.maketrans({'−':'-','‐':'-','‑':'-','‒':'-','–':'-','—':'-','⋯':'...'}))
 return Paragraph(text if markup else escape(text).replace('\n','<br/>'),styles[style])
def H(text,level=0,key=None):
 p=P(text,'h1' if level==0 else 'h2');p.nav=(text,level,key or 'k'+hashlib.sha1(text.encode()).hexdigest()[:12]);return p
class Doc(BaseDocTemplate):
 def __init__(self,path,title):
  super().__init__(str(path),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=56,bottomMargin=53,title=title,author='六级真题学习资料',pageCompression=1)
  self.booktitle=title;self.nav=[];self.positions={}
  self.addPageTemplates(PageTemplate(id='main',frames=[Frame(48,53,A4[0]-96,A4[1]-109,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=self.page))
 def page(self,canvas,doc):
  canvas.saveState();canvas.setFont('CN',9);canvas.setFillColor(colors.HexColor('#64748B'))
  canvas.drawString(48,29,self.booktitle[:37]);canvas.drawRightString(A4[0]-48,29,str(doc.page));canvas.restoreState()
 def afterFlowable(self,f):
  if hasattr(f,'nav'):
   text,level,key=f.nav;self.canv.bookmarkPage(key);self.canv.addOutlineEntry(text,key,level,False);self.nav.append((level+1,text,self.page))
  if hasattr(f,'source_key'):self.positions[f.source_key]=self.page
MANIFEST=[]
def build(path,title,story,kind):
 headings=[e.nav for f in story for e in (f._content if isinstance(f,KeepTogether) else [f]) if hasattr(e,'nav') and e.nav[1]==0]
 if headings:
  contents=[P('目录','h1')]+[P(f'<link href="#{escape(key)}" color="#2F6B86">{escape(text)}</link>','index',True) for text,_,key in headings]+[PageBreak()]
  story=story[:4]+contents+story[4:]
 doc=Doc(path,title);doc.build(story);MANIFEST.append({'file':str(path.relative_to(ROOT)),'title':title,'kind':kind,'pages':doc.page});print('PDF',path.name,doc.page,flush=True);return doc
def cover(title,subtitle,intro):return [P(title,'title'),P(subtitle,'small'),P(intro),Spacer(1,12)]
def keysource(s):return s['file']+'#'+s['locator']
def srcshort(s):
 m=(s.get('local_pdf_match') if s.get('match_score',0)>=95 else None) or s.get('local_prompt_pdf');p=s.get('generated_pdf')
 base=m or s
 label=f"{base['session']} 第{base['suite']}套"
 if m:label+=f" {Path(m['file']).name} 第{m['page']}页"
 if s.get('page'):label+=f" PDF第{s['page']}页"
 if s.get('page_range'):label+=' PDF材料页'+','.join(map(str,s['page_range']))
 if p:label+=f"；{Path(p['file']).stem} 第{p['page']}页"
 loc=s['locator'];loc=re.sub(r'Questions (\d+) to (\d+) are based on the (?:conversation|passage|recording) you have just heard\.?\s*播放本篇',r'听力题\1-\2',loc)
 return label+' '+loc
# Produce searchable paragraph-level sources so every online transcript has a stable PDF page locator.
source_page_map={}
for year in range(2021,2027):
 selected=[u for u in U if u['category']=='听力原文' and u['sources'][0]['session'].startswith(str(year))]
 if not selected:continue
 title=f'{year}年听力原文与段落译文';path=OUT/f'来源补充_{year}年听力原文.pdf'
 story=cover(title,'原文与参考译文分段排印','用于核对学习册例句。英文来自公开补充原文；中文为该来源的段落参考译文。当地文件的套号与网络整理版套号可能不同，正文保留来源套号，已匹配的本地解析页另行标明。')
 last=None
 for u in sorted(selected,key=lambda u:(u['sources'][0]['session'],u['sources'][0]['suite'],int(re.search(r'Questions (\d+)',u['locator'])[1]))):
  source=u['sources'][0];chapter=source['session']+' 第'+source['suite']+'套（补充来源套号）'
  if chapter!=last:story.append(H(chapter));last=chapter
  story.append(H(re.sub(r'\s*播放本篇','',u['locator']),1,key=u['id']))
  for pair in u['bilingual']:
   sr=pair['source'];mark=P(sr['locator'].split()[-1]+' 原文','small');mark.source_key=keysource(sr);story.append(mark)
   story.append(P(pair['en'],'quote'))
   if pair['zh']:story.append(P(pair['zh']))
   if sr.get('url'):story.append(P(f'<link href="{escape(sr["url"])}" color="#2F6B86">查看该段公开来源</link>','small',True))
   story.append(Spacer(1,8))
 doc=build(path,title,story,'source_listening')
 for key,page in doc.positions.items():source_page_map[key]={'file':str(path.relative_to(ROOT)),'page':page}
for year in range(2021,2027):
 selected=[u for u in U if u['category'] in ['作文范文','翻译参考译文'] and u['sources'][0]['session'].startswith(str(year))]
 if not selected:continue
 title=f'{year}年写作翻译参考表达来源';path=OUT/f'来源补充_{year}年参考表达.pdf'
 story=cover(title,'参考版本与真题正文分开使用','本册保留第三方参考范文与参考译文的完整英文，供词频索引定位。它们不是官方唯一答案，未计入真题正文词频；各段中文用于理解范文内容或核对翻译任务。')
 for u in sorted(selected,key=lambda u:(u['sources'][0]['session'],u['sources'][0]['suite'],u['category'])):
  sr=u['sources'][0];heading=f"{sr['session']} 第{sr['suite']}套 {u['category']}"
  h=H(heading);h.source_key=keysource(sr);story.append(h);story.append(P(u['text'],'quote'))
  if u.get('bilingual') and u['bilingual'][0]['zh']:story.append(P(u['bilingual'][0]['zh']))
  story.append(P(f'补充来源套号：第{sr.get("source_suite",sr["suite"])}套','small'))
  if sr.get('url'):story.append(P(f'<link href="{escape(sr["url"])}" color="#2F6B86">查看参考版本</link>','small',True))
  story.append(Spacer(1,18))
 doc=build(path,title,story,'source_reference')
 for key,page in doc.positions.items():source_page_map[key]={'file':str(path.relative_to(ROOT)),'page':page}
save('补充原文PDF页码.json',source_page_map)
source_texts={}
for v in source_page_map.values():
 if v['file'] in source_texts:continue
 doc=fitz.open(ROOT/v['file']);source_texts[v['file']]=[re.sub('[^a-z]','',p.get_text().lower()) for p in doc];doc.close()
verified_sentence_pages={}
def sentencepage(s,sr):
 p=source_page_map.get(keysource(sr))
 if not p:return None
 key=(s['id'],keysource(sr))
 if key in verified_sentence_pages:return verified_sentence_pages[key]
 text=re.sub('[^a-z]','',s['text'].lower());pages=source_texts[p['file']];start=p['page']-1;result=dict(p);result['paragraph_start_page']=p['page'];result['sentence_page_verified']=False
 for i in range(start,min(start+5,len(pages))):
  if text in pages[i]:result['page']=i+1;result['sentence_page_verified']=True;break
  if i+1<len(pages) and text in pages[i]+pages[i+1]:result['page']=i+1;result['sentence_page_verified']=True;result['end_page']=i+2;break
 verified_sentence_pages[key]=result;return result
def enrich(sr):
 if keysource(sr) in source_page_map:sr['generated_pdf']=source_page_map[keysource(sr)]
for s in S:
 for sr in s['sources']:
  enriched=sentencepage(s,sr)
  if enriched:sr['generated_pdf']=enriched
for u in U:
 for sr in u['sources']:enrich(sr)
for row in CORE:
 for sr in row['example']['sources']:
  enriched=sentencepage(row['example'],sr)
  if enriched:sr['generated_pdf']=enriched
for row in PHRASES:
 for sr in row['example']['sources']:
  enriched=sentencepage(row['example'],sr)
  if enriched:sr['generated_pdf']=enriched
for v in W.values():
 for occ in v['occurrences']:
  for sr in occ['sources']:
   enriched=sentencepage(SL[occ['sentence']],sr)
   if enriched:sr['generated_pdf']=enriched
save('句子来源页码核对.json',[{'sentence':sid,'source_key':key,**v} for (sid,key),v in verified_sentence_pages.items()])
save('core_words_with_source_pages.json',CORE)
# Register compact source IDs shared by all volumes.
files=sorted({sr['file'] for s in S for sr in s['sources']}|{x['source']['file'] for x in WRITING}|{x['source']['file'] for x in load('translation_originals.json')}|{x['file'] for x in load('资料清单.json')})
FIDS={file:f'F{i+1:03d}' for i,file in enumerate(files)}
save('source_id_catalogue.json',[{'id':FIDS[f],'file':f} for f in files])
def exampleblock(e,word=None):
 text=escape(e['text'])
 if word:
  for form in sorted(W[word]['forms'],key=len,reverse=True):text=re.sub(r'(?<![A-Za-z])('+re.escape(form)+r')(?![A-Za-z])',r'<font name="CNBold">\1</font>',text,flags=re.I)
 story=[P(text,'quote',True)]
 if e.get('zh'):story.append(P(e['zh_type']+'：'+e['zh']))
 for sr in e['sources'][:2]:story.append(P('出处：'+srcshort(sr),'small'))
 return story
def gloss(word):return re.sub(r'\s+',' ',W[word]['meaning'].split('[网络]')[0])[:150] or '专名或术语，释义待核对'
def poslabel(tag):return {'N':'名词','V':'动词','J':'形容词','R':'副词','I':'介词或连接词','M':'情态动词'}.get(tag[:1],tag)
for i,(start,end) in enumerate([] if (D/'core_words_enriched1500.json').exists() else [(0,200),(200,400),(400,500)],1):
 title=f'核心词汇第{i}册';story=cover(title,f'第{start+1}至{end}词 以听辨和语境理解为主','按跨考次复现、2024年至2026年复现和真题词频排序。每天新增10词，熟悉且能听辨的词直接勾选掌握。词频分别标明真题与参考表达，整段译文帮助理解原句所处语境。完整出现位置见字母索引。')
 for row in CORE[start:end]:
  block=[]
  w=row['word'];v=W[w];e=row['example']
  if (row['rank']-1)%10==0:block.append(H(f"第{(row['rank']-1)//10+1}组 第{row['rank']}至{min(row['rank']+9,500)}词"))
  block.append(H(f"{row['rank']:03d}  {w}",1,key='word-'+w));block.append(P(poslabel(e['pos'])+'  '+row['meaning']))
  block.append(P(f"真题{v['exam_count']}次 | 覆盖{v['exam_coverage']}考次 | 2024年至2026年{v['exam_recent']}次 | 参考表达{v['reference_count']}次",'small'))
  block.append(P('题型分布：'+'；'.join(f'{k}{v["categories"].get(k,0)}次' for k in ['听力原文','听力选项','阅读真题','作文题干']),'small'))
  related=sorted({x for g in load('derived_word_families.json') if w in g for x in g if x!=w})
  if related:block.append(P('关联派生词（频次分列）：'+', '.join(related),'small'))
  block.extend(exampleblock(e,w));block.append(P('主动回忆：遮住释义，读懂并复述原句。\n复习：次日[ ] 3日[ ] 7日[ ] 14日[ ]  已掌握[ ]','small'));block.append(Spacer(1,10));story.append(KeepTogether(block))
 build(OUT/f'01_核心词汇_{i}.pdf',title,story,'core')
story=cover('高频短语100条','真题原句 频次与全部出处可追溯','先练连接逻辑、动词搭配和主题表达。词频按实际连续词组匹配，不把没有出现的变体补进频次。be used to等多义结构需要按后接成分判断，避免只记一个中文意思。')
for i,row in enumerate(PHRASES,1):
 block=[H(f'{i:03d}  {row["phrase"]}',0,key='phrase-'+str(i)),P(row['meaning']),P(f"真题{row['count']}次 | 覆盖{row['coverage']}考次 | 2024年至2026年{row['recent']}次",'small')]+exampleblock(row['example'])+[P('回忆中文含义[ ] 从中文写出短语[ ] 放入自己的句子[ ]','small')]
 story.append(KeepTogether(block))
build(OUT/'02_高频短语100条.pdf','高频短语100条',story,'phrases')
# Sentence structures have explicitly defined patterns and count matching sentences, not topic similarity.
patterns=[
('not only ... but also ...',r'not only.*but also','不仅……而且……；并列两部分保持相同语法形式。'),
('there is / are ...',r'\bthere (?:is|are|was|were|has been|have been)\b','用存在句引出现象；后接名词短语。'),
('It is ... to ...',r'\bit is\b.{0,100}\bto\b','用形式主语承接不定式；重点是后面的具体行动。'),
('It is ... that ...',r'\bit is\b.{0,120}\bthat\b','形式主语或强调结构；先判断that从句在句中的作用。'),
('which ...',r'\bwhich\b','定语从句补充说明名词或前面的情况；不要让which指代不明。'),
('that ...',r'\bthat\b','连接宾语从句或定语从句；按原句识别它修饰或补充的内容。'),
('who ...',r'\bwho\b','修饰人的定语从句；主谓一致看先行词。'),
('where ...',r'\bwhere\b','说明地点或情境；区分关系副词与名词性从句。'),
('when ...',r'\bwhen\b','时间或情境从句；不要把所有when都译成时间点。'),
('while ...',r'\bwhile\b','可表示同时发生或对比；按上下文判断。'),
('although ...',r'\balthough\b','让步关系；同一主从句不再重复使用but。'),
('even though ...',r'\beven though\b','尽管……；承认事实后引出另一层判断。'),
('even if ...',r'\beven if\b','即使……；强调假设条件。'),
('if ...',r'\bif\b','条件从句；区分真实条件与虚拟假设。'),
('unless ...',r'\bunless\b','除非……；避免与否定词重复造成意思相反。'),
('as long as ...',r'\bas long as\b','只要……；用于给出明确条件。'),
('because ...',r'\bbecause\b','因为……；后接完整原因从句。'),
('since ...',r'\bsince\b','表示自从或由于；由时态和逻辑判断。'),
('as ...',r'\bas\b','可能引出时间、原因、比较或方式；不要固定译为一个词义。'),
('so that ...',r'\bso that\b','以便或因此……；结合后文判断目的和结果。'),
('rather than ...',r'\brather than\b','而不是……；对应的两部分要平行。'),
('instead of ...',r'\binstead of\b','用……代替……；of后接名词或动名词。'),
('by doing ...',r'\bby [a-z]+ing\b','通过某种行动实现目标；by后用动名词。'),
('without doing ...',r'\bwithout [a-z]+ing\b','在没有做……的情况下；without后用动名词。'),
('with ...',r'\bwith\b','引出背景、伴随因素或资源；with后不要直接接完整谓语句。'),
('one of the ...',r'\bone of the\b','……之一；通常后接可数名词复数。'),
('such as ...',r'\bsuch as\b','列举具体例子；与前面的类别对应。'),
('including ...',r'\bincluding\b','补充列举范围；后接名词短语。'),
('compared with / to ...',r'\bcompared (?:with|to)\b','与……相比；被比较对象保持一致。'),
('be associated with ...',r'\b(?:is|are|was|were|be) associated with\b','与……存在关联；关联不能自动当成因果。'),
('be likely to ...',r'\b(?:is|are|was|were|be) likely to\b','可能会……；用于谨慎表达判断。'),
('be expected to ...',r'\b(?:is|are|was|were|be) expected to\b','预计或被期待会……；区分预测与要求。'),
('be used to ...',r'\b(?:is|are|was|were|be) used to\b','被用于做某事或习惯于某事；后面形式决定意思。'),
('have / has been ...',r'\b(?:have|has) been\b','现在完成时；结合后面成分判断状态、被动或进行。'),
('have / has ...',r'\b(?:have|has)\b','可表示拥有或完成时；先识别词组中的谓语。'),
('be located / situated ...',r'\b(?:is|are|was|were|be) (?:located|situated)\b','位于……；地点介绍中的常用结构。'),
('be known as / for ...',r'\b(?:is|are|was|were|be) known (?:as|for)\b','被称为……或因……而著名。'),
('allow ... to ...',r'\ballow(?:s|ed)?\b.{0,100}\bto\b','使某人能够做……；to前写清动作的执行者。'),
('enable ... to ...',r'\benabl(?:e|es|ed)\b.{0,100}\bto\b','使……能够……；适合描述技术或政策的作用。'),
('help ...',r'\bhelp(?:s|ed)?\b','帮助或有助于……；后接的动作体现具体作用。'),
('make it ... to ...',r'\bmake(?:s)? it\b.{0,80}\bto\b','使做某事变得……；it承接后面的动作。'),
('play a ... role ...',r'\bplay(?:s|ed)? (?:a|an)\b.{0,40}\brole\b','发挥某种作用；把作用和具体领域联系起来。'),
('the more ... the ...',r'\bthe more\b.*\bthe\b','越……越……；用于两个变化之间的关系。'),
('Only by ...',r'\bonly by\b','只有通过……；置于句首时主句通常部分倒装。'),
]
structures=[]
for title,pattern,note in patterns:
 rx=re.compile(pattern,re.I);matches=[s for s in S if rx.search(s['text']) and 8<=len(s['text'].split())<=70]
 if not matches:continue
 ex=max(matches,key=lambda s:10*(s['category']=='翻译参考译文')+4*any(z['session']>='2024-01' for z in s['sources'])-len(s['text'])/80)
 structures.append({'pattern':title,'note':note,'matched_sentences':len(matches),'example':ex})
 if len(structures)==40:break
save('sentence_structures.json',structures)
# Writing and translation workbook.
story=cover('写作与翻译专项册','39道作文题 39道翻译原题 118项中文概念 40个句式','作文按实际题目归类，话题频次与作文形式分别统计。翻译频次来自中文原文；推荐英文表达用于主动练习。近期只出现一次的科技主题也单列学习，避免只背多次出现的宽泛词。')
theme_stats=load('writing_theme_statistics.json');story.append(H('作文主题分布'))
for theme,count in sorted(theme_stats['themes'].items(),key=lambda x:x[1],reverse=True):story.append(P(f'{theme}  {count}题'))
story.append(P('本样本包含13个考次、39道作文题。各主题分类是复习归纳，不表示下一次考试的出题概率。','small'))
story.append(H('作文形式与操作要求'))
for form,count in theme_stats['forms'].items():story.append(P(f'{form}  {count}题'))
story.append(P('给定首句题先核对是否要求照抄首句；图表题先描述总体趋势和关键比较，再评论成就；材料评论题先概括现象，再分析影响并提出措施。'))
story.append(H('逐题主题与论证方向'))
for p in sorted(WRITING,key=lambda p:(p['session'],p['suite']),reverse=True):
 story.append(H(f"{p['session']} 第{p['suite']}套 {p['title']}",1,key='write-'+p['session']+'-'+p['suite']))
 story.append(P('题目内容：'+p['prompt'],'quote'));story.append(P('形式：'+p['form']+'；归类：'+p['theme']))
 directions={'教育学习':'提出学习目标或立场，解释它如何改善理解和实践能力，用具体学习场景支撑，最后给出可执行的行动。','科技数字生活':'讨论技术或数字生活的实际影响，区分收益与风险，举一个使用场景，提出负责任的使用或学习方法。','社会与个人':'围绕个人选择或行为提出观点，解释原因及后果，用可理解的日常场景支撑，再给出行动建议。','社会发展':'说明发展背景及对人的影响，举出可观察的变化，连接个人行动与社会责任。','环境健康':'紧扣题目中的人群和情境，解释健康或自然环境的重要性，举例说明，再提出具体行动。','沟通合作':'说明沟通中的障碍及共同目标，分析合作机制，用团队场景举例，提出倾听、互信或讨论方法。','职业发展':'联系能力要求与职业挑战，讨论知识、实践或心态中的两项，用求职或项目场景支撑。','文化传承':'说明理解传统文化如何建立文化认同，用具体文化体验支撑，再提出学习和交流的方法。'}
 story.append(P('论证方向：'+directions[p['theme']]));story.append(P('出处：'+srcshort(p['source']),'small'))
story.append(H('翻译原文中的概念复现'))
story.append(P('“覆盖考次”统计不同考试月份；“涉及题目”统计该中文表达出现的翻译任务。相近概念分列，例如“提高”和“改善”分别统计。词频按字面匹配，长短词可能在同一句中同时出现。','small'))
for i,c in enumerate(CONCEPTS,1):
 story.append(H(f'{i:03d}  {c["zh"]}',1,key='concept-'+str(i)));story.append(P('可用表达：'+c['english'],'quote'));story.append(P(f"原文{c['count']}次 | 覆盖{c['coverage']}考次 | 涉及{c['tasks']}题 | 2024年至2026年{c['recent']}次",'small'))
 story.append(P('真题原句：'+c['example']['sentences'][0]));story.append(P('出处：'+srcshort(c['example']['source']),'small'));story.append(P('遮住英文写出表达[ ] 在原句中练习[ ]','small'))
story.append(H('40个可迁移句式'))
story.append(P('以下频次是按所列结构在语料中匹配到的句子数，包含参考表达，与单词真题频次不同。结构可以重叠；先理解原句，再迁移到新题目。','small'))
for i,r in enumerate(structures,1):
 story.append(H(f'{i:02d}  {r["pattern"]}',1,key='structure-'+str(i)));story.append(P(r['note']));story.append(P(f"匹配句子{r['matched_sentences']}条 | 本例来源类别：{r['example']['category']}",'small'));story.append(P(r['example']['text'],'quote'));story.append(P('出处：'+srcshort(r['example']['sources'][0]),'small'))
story.append(H('中译英主动训练'))
practice=[]
translation_pairs=[]
for file in (ROOT/'补充资料_2026年6月'/'校对参考').glob('*_part-iv.html'):
 soup=BeautifulSoup(file.read_text(encoding='utf-8'),'html.parser')
 for item in soup.select('.tqp-unit'):
  zh=item.select_one('.tqp-stem');en=item.select_one('.tqp-final')
  if zh and en:translation_pairs.append({'zh':re.sub(r'^\d+[.]\s*','',zh.get_text(' ',strip=True)),'en':en.get_text(' ',strip=True),'file':str(file.relative_to(ROOT))})
for c in CONCEPTS:
 ex=c['example']['sentences'][0]
 if 15<=len(ex)<=100 and ex not in [p['zh'] for p in practice]:
  clean=lambda t:re.sub('[^\u4e00-\u9fff]','',t)
  matches=[p for p in translation_pairs if clean(p['zh'])==clean(ex)]
  if not matches:continue
  practice.append({'zh':ex,'concept':c['zh'],'expression':c['english'],'source':c['example']['source'],'answer':matches[0]['en'],'reference_file':matches[0]['file']})
 if len(practice)==20:break
for i,r in enumerate(practice,1):story.append(H(f'练习{i:02d}',1));story.append(P(r['zh']));story.append(P('先写英文，再检查主谓、时态、冠词、单复数和搭配。','small'));story.append(Spacer(1,35))
story.append(PageBreak());story.append(H('独立答案页 参考译文'))
for i,r in enumerate(practice,1):story.append(P(f'{i:02d}  核心表达：{r["concept"]} - {r["expression"]}'));story.append(P(r['answer'],'quote'));story.append(P('参考原题：'+srcshort(r['source']),'small'))
save('translation_practice.json',practice)
story.append(H('每周作文任务'))
story.append(P('每周从对应主题选一道真题，先独立完成150至200词，再用下面清单自检。避免把题目改写成自己熟悉但不相关的话题。'))
for week,theme in enumerate(['职业发展','科技数字生活','教育学习','环境健康','沟通合作','社会与个人','社会发展','文化传承'],1):story.append(P(f'第{week}周  {theme}：先列立场、两个论据和一个例子，再完成正文。'))
story.append(P('自检：回应题目[ ] 满足首句要求[ ] 150至200词[ ] 段落逻辑清楚[ ] 例子支持观点[ ] 主谓时态正确[ ] 搭配自然[ ]'))
build(OUT/'04_写作与翻译专项册.pdf','写作与翻译专项册',story,'writing_translation')
# Preserve the user's themed bilingual revision when rebuilding the whole package.
import runpy
writing_revision=runpy.run_path(str(ROOT/'六级备考成果'/'脚本'/'revise_writing_translation.py'))['generate'](update_manifest=False)
MANIFEST[-1].update(title=writing_revision['title'],pages=writing_revision['pages'])
# Listening and reading drill workbook uses actual, paired transcript / option evidence.
story=cover('听力与阅读专项册','听辨 定位 同义替换与错误原因','先独立做题，再把原文与选项对照。练习单位是一篇材料及它的题目，记录具体证据和错误原因；不靠反复看懂解析来判断自己已经掌握。')
story.append(H('听力每天35分钟'))
for t in ['独立听一篇并完成题目，记录答案与把握程度。','按意群重听，写出卡住的短语和句子。','核对原文，把错因分为词不认识、声音没识别、逻辑没跟上、同义替换没识别或注意力中断。','合上原文再听，最后跟读2至3遍；次日不看原文复听。']:story.append(P(t))
story.append(H('按题号核对原文与选项'))
listening_examples=[];selected_sets=set()
for u in sorted(U,key=lambda u:(u['sources'][0]['session'],u['sources'][0]['suite']),reverse=True):
 if u['category']!='听力原文' or u['sources'][0]['session']<'2024-01':continue
 sr=u['sources'][0];session=sr['session'];suite=(sr.get('local_pdf_match') or sr)['suite'];rm=re.search(r'Questions (\d+) to (\d+)',u['locator'])
 if (session,suite) in selected_sets:continue
 if not rm:continue
 lo,hi=int(rm[1]),int(rm[2]);options=[]
 for s in S:
  if s['category']!='听力选项':continue
  for z in s['sources']:
   qm=re.search(r'题(\d+)',z['locator'])
   if z['session']==session and z['suite']==suite and qm and lo<=int(qm[1])<=hi:options.append(s);break
 if not options:continue
 listening_examples.append((u,options));selected_sets.add((session,suite))
 if len(listening_examples)==10:break
for i,(u,options) in enumerate(listening_examples,1):
 sr=u['sources'][0];story.append(H(f'精练{i:02d}  {sr["session"]} 题号材料对照'))
 rm=re.search(r'Questions (\d+) to (\d+)',u['locator']);lo,hi=int(rm[1]),int(rm[2])
 story.append(P(u['locator'],'small'));story.append(P('先在原文中寻找选项对应表达；分别标明原词复现、同义替换、信息相反或原文未提及。'))
 selected=u['bilingual'][:3]
 for pair in selected:story.append(P(pair['en'],'quote'));story.append(P(pair['zh']))
 soup=BeautifulSoup((ROOT/sr['file']).read_text(encoding='utf-8'),'html.parser')
 for qnum in range(lo,min(lo+2,hi+1)):
  question=soup.select_one(f'#q-{qnum}')
  if question:
   for opt in question.select('[data-pdh-letter]'):story.append(P(f'题{qnum} 选项{opt["data-pdh-letter"]}  '+opt.get_text(' ',strip=True),'index'))
 story.append(P('我的证据句：________________________________\n原文表达与选项表达：________________________\n错因与下次要做的动作：______________________','small'));story.append(P('本材料完整原文：'+srcshort(sr),'small'))
story.append(H('信号词与逻辑变化'))
for phrase,note in [('however / but / yet','听到转折后，注意后文是否改变前面的判断。'),('because / due to / as a result','区分原因与结果，不把两者互换。'),('for example / such as','例子通常用于支撑观点；判断题目问的是例子还是主旨。'),('not / hardly / rarely / no longer','留意否定范围与程度，尤其在长句中。'),('first / then / finally','把多个步骤或观点按顺序记下来。')]:story.append(P(phrase,'quote'));story.append(P(note))
story.append(H('易混表达的听辨动作'))
for line in ['research、researcher、researchers：听辨词尾，判断说的是研究还是研究人员。','economic、economical：前者通常与经济有关，后者强调节省。','affect、effect：结合句子位置判断动词或名词，不只凭近似发音猜意思。','increase、decrease：关注变化方向，避免听到同一词尾就忽略前缀。','used to、be used to、be used to do：结合前面的be和后面的动词形式判断。']:story.append(P(line))
story.append(H('10道同义替换与错项分析示例'))
worked=[]
for u,options in listening_examples:
 sr=u['sources'][0];soup=BeautifulSoup((ROOT/sr['file']).read_text(encoding='utf-8'),'html.parser');rm=re.search(r'Questions (\d+) to (\d+)',u['locator']);lo=int(rm[1]);q=soup.select_one(f'#q-{lo+1}')
 if not q:continue
 pairs=q.select('.rp-pair');loc=q.select_one('.rp-locate-en');answer=q.select_one('.rp-ans');choice=q.select_one('.lqp-correct')
 if not loc or not answer or not choice:continue
 story.append(H(f'{sr["session"]} 补充来源第{sr["suite"]}套 第{lo+1}题',1));stem=q.select_one('.rp-stem-en')
 if stem:story.append(P(stem.get_text(' ',strip=True),'quote'))
 story.append(P('答案原文：'+loc.get_text(' ',strip=True),'quote'));loczh=q.select_one('.rp-locate-zh')
 if loczh:story.append(P(loczh.get_text(' ',strip=True)))
 story.append(P('参考答案：'+answer.get_text(strip=True)+'  '+choice.get_text(' ',strip=True)))
 for pair in pairs:
  orig=pair.select_one('.rp-pair-orig');opt=pair.select_one('.rp-pair-opt');why=pair.select_one('.lqp-pair-why')
  if orig and opt:story.append(P(orig.get_text(' ',strip=True)+'  <=>  '+opt.get_text(' ',strip=True),'quote'))
  if why:story.append(P(why.get_text(' ',strip=True)))
 for bad in q.select('.rp-verdict.is-bad')[:2]:story.append(P('错项：'+bad.get_text(' ',strip=True),'small'))
 story.append(P('来源：'+sr['file']+f' #q-{lo+1}；参考解析来自该整理版。','small'));worked.append({'session':sr['session'],'suite':sr['suite'],'question':lo+1,'source':sr['file']})
save('listening_worked_examples.json',worked)
story.append(H('阅读每天25分钟'))
for line in ['仔细阅读：先抓问题中的主体和限制条件，再定位证据句；比较原文与每个选项的范围、程度、因果和主体。','匹配阅读：给题干圈出独特信息，先匹配容易定位的段落，再处理概括或替换表达。','选词填空：先判断词性、句子结构和搭配，再比较词义；保留原始空格，不把参考答案当成原题。','复盘：每道错题写一句证据与一句排除理由。']:story.append(P(line))
story.append(H('阅读长句拆解'))
read_examples=load('read_examples.json');annotations=load('reading_annotations.json')
for i,s in enumerate(read_examples,1):
 story.append(H(f'长句{i:02d}',1));story.append(P(s['text'],'quote'));story.append(P('先自行标主语、谓语、从句和逻辑关系。'));story.append(P('主干：'+annotations[i-1]['main']));story.append(P('修饰与逻辑：'+annotations[i-1]['detail']));story.append(P('中文理解：'+annotations[i-1]['meaning']));story.append(P('出处：'+srcshort(s['sources'][0]),'small'));story.append(Spacer(1,16))
story.append(H('错题复盘记录'))
for i in range(1,5):story.append(P(f'记录{i}  日期______ 试卷______ 题号______\n我的答案______ 正确答案______\n证据句____________________________________\n错误原因__________________________________\n下次动作__________________________________'));story.append(Spacer(1,12))
story.append(H('音频目录'))
for p in sorted(ROOT.rglob('*.mp3')):
 rel=str(p.relative_to(ROOT))
 if ('CET6' in rel or '六级' in rel or '补充资料_2026' in rel) and not ('CET4' in rel or '四级' in rel):story.append(P(rel,'small'))
story.append(P('本册不标未经核实的时间戳。2026年6月两套MP3位于补充资料文件夹；对应原文按相同补充来源的套号查找。','small'))
build(OUT/'03_听力与阅读专项册.pdf','听力与阅读专项册',story,'listening_reading')
# Complete dictionary index: one original context plus ALL occurrence locations, grouped without dropping positions.
indexstory=cover('完整词频与出处索引','按字母查找 真题与参考表达分别统计','频次是词形还原后的次数；同一位置出现多次以次数标明。来源代码对应使用指南中的资料目录。选词填空例句保留空格，原题选项或题干不足以形成完整句子时按原始片段展示。逐次出现的句子ID和词位保存在结构化数据中。')
def locations(v):
 groups=collections.defaultdict(lambda:collections.Counter())
 for occ in v['occurrences']:
  seen=set()
  for sr in occ['sources']:
   p=sr.get('generated_pdf');fid=FIDS[sr['file']]
   if p:
    page='补充PDF'+str(p['page']);loc=sr['locator'].split()[-1]
   else:page='p'+(','.join(map(str,sr['page_range']))+'(材料范围)' if sr.get('page_range') else str(sr.get('page') or '-'));loc=sr['locator']
   loc=re.sub(r'\s+','',loc);key=(fid,page,loc)
   if key in seen:continue
   seen.add(key);groups[(fid,page)][loc]+=1
   alias=sr.get('local_pdf_match')
   if alias and sr.get('match_score',0)>=95:
    alias_key=(FIDS[alias['file']],'p'+str(alias['page']),'对照补充段'+alias['locator'])
    if alias_key not in seen:seen.add(alias_key);groups[(alias_key[0],alias_key[1])][alias_key[2]]+=1
 result=[]
 for (fid,page),counts in sorted(groups.items()):
  refs='、'.join(f'{k}×{c}' for k,c in counts.items())
  result.append(f'{fid} {page} {refs}')
 return '；'.join(result)
last=''
for i,w in enumerate(sorted(W)):
 initial=w[0].upper()
 if initial!=last:indexstory.append(H(initial,key='letter-'+initial));last=initial
 v=W[w];h=P(w+'  '+gloss(w),'index');h.nav=(w,1,'idx-'+hashlib.sha1(w.encode()).hexdigest()[:12]);h.keepWithNext=True;indexstory.append(h)
 indexstory.append(P(f"真题{v['exam_count']}次；覆盖{v['exam_coverage']}考次；近三年{v['exam_recent']}次；范文{v['categories'].get('作文范文',0)}次；译文{v['categories'].get('翻译参考译文',0)}次",'small'))
 indexstory.append(P('题型：'+'；'.join(f'{k}{v["categories"].get(k,0)}次' for k in ['听力原文','听力选项','阅读真题','作文题干'] if v['categories'].get(k,0)),'small'))
 occ=v['occurrences'];best=min(occ,key=lambda o:(SL[o['sentence']]['category'] in ['作文范文','翻译参考译文'],abs(len(SL[o['sentence']]['text'])-130)))
 indexstory.append(P('原句或原始片段：'+SL[best['sentence']]['text'],'index'))
 indexstory.append(P('全部出处：'+locations(v),'index'));indexstory.append(Spacer(1,7))
 if i%1500==0:print('INDEX entries',i,flush=True)
temp=ROOT/'六级备考成果'/'核验'/'完整索引合并中间稿.pdf';doc=Doc(temp,'完整词频与出处索引');doc.build(indexstory)
full=fitz.open(temp);toc=full.get_toc();firstletters=[(page-1,title) for level,title,page in toc if level==1]
start=0;part=1
while start<len(full):
 end=min(start+149,len(full));eligible=[p for p,_ in firstletters if start+70<=p<end]
 if end<len(full) and eligible:end=max(eligible)
 if end<=start:end=min(start+149,len(full))
 out=fitz.open();out.insert_pdf(full,from_page=start,to_page=end-1)
 localletters=[(title,page-start+1) for lv,title,page in toc if lv==1 and start<page<=end]
 coverpdf=ROOT/'六级备考成果'/'核验'/f'index_cover_{part}.pdf'
 coverstory=cover(f'完整词频索引第{part}卷','可搜索 可批注 完整出处分组展示','从下列字母入口或PDF书签进入正文。若本卷是某字母的续卷，请直接搜索单词。来源代码对应使用指南末尾的资料目录；补充PDF页码对应同年原文或参考表达来源册。')
 for label,page in localletters:coverstory.append(P(f'{label}  第{page}页','h2'))
 coverdoc=Doc(coverpdf,f'完整词频索引第{part}卷');coverdoc.build(coverstory)
 cp=fitz.open(coverpdf);out.insert_pdf(cp,start_at=0);coverpages=len(cp);cp.close()
 for label,page in localletters:
  for rect in out[0].search_for(f'{label}  第{page}页'):out[0].insert_link({'kind':fitz.LINK_GOTO,'from':rect,'page':page-1})
 subtoc=[[1 if lv==1 else 2,title,page-start+coverpages] for lv,title,page in toc if start<page<=end]
 if subtoc and subtoc[0][0]==2:subtoc.insert(0,[1,'字母索引续卷',1])
 if subtoc:out.set_toc(subtoc)
 for pn,page in enumerate(out):
  if pn<coverpages:continue
  page.add_redact_annot(fitz.Rect(page.rect.width-85,page.rect.height-44,page.rect.width-40,page.rect.height-18),fill=(1,1,1));page.apply_redactions()
  page.insert_text((page.rect.width-66,page.rect.height-29),str(pn+1),fontsize=9,fontname='helv',color=(.39,.45,.55))
 chars=[title for lv,title,page in toc if lv==1 and start<page<=end]
 inherited=[title for lv,title,page in toc if lv==1 and page<=start]
 firstchar=inherited[-1] if inherited else (chars[0] if chars else 'A')
 suffix=firstchar+'-'+(chars[-1] if chars else firstchar)
 path=OUT/f'05_完整索引_{part:02d}_{suffix}.pdf';out.set_metadata({'title':f'完整词频索引第{part}卷','author':'六级真题学习资料'});out.save(path,deflate=True);out.close()
 MANIFEST.append({'file':str(path.relative_to(ROOT)),'title':f'完整词频索引第{part}卷','kind':'index','pages':len(out) if not out.is_closed else end-start+coverpages,'source_page_start':start+1});print('INDEX PDF',part,end-start+coverpages,flush=True);start=end;part+=1
full.close()
# Public guide: no personal scores or individual study schedule.
story=cover('六级资料使用指南','公开学习资料','按主题阅读学习册，使用完整索引核对出处。')
story.append(H('统计口径与资料检查'))
for line in [f"共读取{SUMMARY['pdf_files']}份PDF、{SUMMARY['pdf_pages']}页；192页使用OCR，其中3页是额外修复中文编码。",f"共有39道作文、39道翻译；补充原文含23套独立听力、161篇听力材料。首轮精选500词、100短语、118项中文概念和40个句式。",f"有效词条{len(W)}个；词典未覆盖、拼写可疑或专名未确认的词形另列待核对，不补造释义。",f"另外{SUMMARY.get('quarantined_sentences',0)}条含残缺字形的原句已暂时移出可靠词频，原始内容和出处保留在待核对清单。",'真题词频包含听力选项、听力原文、阅读正文及选项、作文实际主题内容；参考范文和参考译文另计。常见考试指令不进入真题词频。','单词合并屈折词形，派生词保持独立。缩写否定和人称助动词在统计中展开，展示原句保持原样。','同一位置重复出现的词按次数记录。完全相同的整篇材料才合并，普通选项或短句相同不自动当成试卷重复。','补充参考表达来自明确标记的第三方整理版，不能视为官方唯一答案。中文概念按原题统计，不把编者英译用词偏好算成中文考点频率。','页码均指PDF文件从第1页开始的物理页码。来源为网页的词句同时提供生成的补充原文PDF页码；本地解析匹配位置另行保留。少数无法确认单页的原始句子按材料页范围标注。']:story.append(P(line))
story.append(H('作文主题与翻译复现概览'))
for theme,count in sorted(theme_stats['themes'].items(),key=lambda x:x[1],reverse=True):story.append(P(f'{theme}：{count}道作文'))
story.append(P('翻译跨考次出现较多的字面表达：'+'、'.join(c['zh'] for c in CONCEPTS[:15])+'。高频宽泛词要配合近年的人工智能、远程医疗、电子商务、养老等具体表达学习。'))
story.append(H('全部来源代码目录'))
story.append(P('索引中的F代码对应下列文件。p表示原始PDF页码；“补充PDF”表示同年来源补充册的页码。听力原文、范文、译文分别查对应来源补充册。','small'))
for file in files:
 story.append(P(FIDS[file]+'  '+file,'index'))
story.append(H('待核对与排除记录'))
unknown=load('待核对词形.json')
story.append(P(f'词典未覆盖的词形{len(unknown)}种，共{sum(unknown.values())}次。它们可能是专名、新词、编码或OCR问题，不能全部当作错误拼写。完整清单在数据目录。','small'))
story.append(P('较常见的待核对词形：'+'、'.join(list(unknown)[:40]),'small'))
build(OUT/'00_使用指南与备考安排.pdf','六级资料使用指南',story,'guide')
save('pdf_manifest.json',MANIFEST)
if (D/'core_words_enriched1500.json').exists():
 from revise_vocabulary_pdfs import generate as generate_vocabulary_revision
 updated=generate_vocabulary_revision(update_manifest=False)
 MANIFEST=[m for m in MANIFEST if m['kind'] not in ['core','guide']]+updated
 save('pdf_manifest.json',MANIFEST)
print('DONE PDFs',len(MANIFEST),'pages',sum(p['pages'] for p in MANIFEST),flush=True)
