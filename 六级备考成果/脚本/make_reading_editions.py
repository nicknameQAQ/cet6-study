"""Rebuild current sentence cards, phrase cards and compact word/IPA/meaning PDFs."""
import sys,json,re,copy,os,hashlib,csv
from pathlib import Path
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'六级备考成果';D=R/'数据';OUT=R/'学习资料'
sys.path.insert(0,str(D/'python_libs'));sys.stdout.reconfigure(encoding='utf8')
import pymupdf as fitz
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak,Spacer,Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
import revise_vocabulary_pdfs as v
def load(n):return json.loads((D/n).read_text(encoding='utf8'))
def save(n,a):(D/n).write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')

def quick_edition(rows=None,reading=False):
 rows=rows or load('core_words_enriched1500.json');expected=500 if reading else 1500
 assert len(rows)==len({r['word'] for r in rows})==expected
 name='09_阅读高频500速记_词音义.pdf' if reading else '06_核心词汇1500速记_词音义.pdf'
 title='阅读高频500速记' if reading else '核心词汇1500速记'
 path=OUT/name;c=Canvas(str(path),pagesize=A4,pageCompression=1);c.setTitle(title+'：单词、英音、中文义');c.setAuthor('六级学习资料整理')
 width,height=A4;locations=[]
 enstyle=ParagraphStyle('QuickEN',fontName='IPA',fontSize=12,leading=14)
 cnstyle=ParagraphStyle('QuickCN',fontName='CN',fontSize=12,leading=15,wordWrap='CJK')
 for start in range(0,len(rows),24):
  pn=start//24+1;key='page-'+str(pn);c.bookmarkPage(key)
  block=rows[start:start+24];c.addOutlineEntry(f"{block[0]['rank']:04d}-{block[-1]['rank']:04d} {block[0].get('display_word',block[0]['word'])}",key,0)
  c.setFillColor(colors.HexColor('#24596b'));c.setFont('CNBold',13);c.drawString(44,height-35,title+' · 词 / 英音 / 中文义')
  for j,r in enumerate(block):
   x=44+(j//12)*266;top=height-55-(j%12)*61;w=245
   word=r.get('display_word',r['word']);ipa=r['ipa_uk'];meaning=r.get('quick_meaning',r['meaning'])
   ep=Paragraph('<b>'+escape(word)+'</b>  '+escape(ipa),enstyle);_,eh=ep.wrap(w,100)
   cp=Paragraph(escape(meaning),cnstyle);_,ch=cp.wrap(w,100)
   assert eh+ch<=58,('quick overflow',word,eh,ch,meaning)
   ep.drawOn(c,x,top-eh);cp.drawOn(c,x,top-eh-ch-3)
   locations.append(dict(rank=r['rank'],word=word,ipa_uk=ipa,meaning=meaning,page=pn))
  c.setFillColor(colors.HexColor('#64748b'));c.setFont('CN',9)
  c.drawString(44,31,'阅读频次排序；可与1500重合' if reading else '保持详解版顺序；中文为简明释义')
  c.setFont('IPA',9);c.drawRightString(width-40,31,str(pn));c.showPage()
 c.save();save('阅读500速记索引.json' if reading else '1500词速记索引.json',locations)
 return dict(file=str(path.relative_to(ROOT)),title=title+'：词音义',kind='reading_quick' if reading else 'quick_vocabulary',pages=(len(rows)+23)//24)

def source_lines(e):
 src=e['sources'][0];sp=e['paragraph_source'];start=sp.get('paragraph_start_page',sp['page']);end=sp.get('page_end',sp.get('end_page',start))
 return [f"{src['session']} 第{src['suite']}套 · {e.get('source_display_locator',e['category']+' · '+src['locator'])}",f"原文页：{Path(sp['file']).name} p{start}"+(f'-{end}' if end!=start else '')]

def phrases_edition():
 rows=load('core_phrases.json');assert len(rows)==100
 old=next(m for m in load('pdf_manifest.json') if m['kind']=='phrases');path=ROOT/old['file']
 story=[v.P('高频短语 · 单句对照','title'),v.P('100条 · 保留原频次 · 阅读句优先','label'),v.P('每条只展示对应英文句子与这一句的中文参考译文，不再附整段。来源含阅读正文、听力原文或原题表达，逐条标明。译文为整理者编写或校订，非官方答案。'),v.P('词频沿用原短语统计口径；本次只调整例句展示。详尽出处见数据包 phrase_statistics.json 对应短语的 occurrences，句子、页码与原文来源保留。','small'),PageBreak(),v.H('目录','contents')]
 for j in range(0,100,10):
  key='group-'+str(j);story.append(v.P(f'<link href="#{key}" color="#24596B">第{j//10+1:02d}组 · {escape(rows[j]["phrase"])} - {escape(rows[j+9]["phrase"])}</link>',markup=True))
 for j,r in enumerate(rows):
  if j%2==0:story.append(PageBreak())
  if j%10==0:story.append(v.H(f'第{j//10+1:02d}组','group-'+str(j)))
  h=v.P(f'{j+1:03d}  {r["phrase"]}','h2');h.nav=(r['phrase'],1,'phrase-'+str(j));story.append(h)
  story.append(v.P(r['meaning']));story.append(v.P(f"真题 {r.get('exam_count',r.get('count',0))}次 · 覆盖 {r.get('exam_coverage',r.get('coverage',0))}考次 · 近三年 {r.get('exam_recent',r.get('recent',0))}次",'small'))
  e=r['example'];story.append(v.P(e.get('display_text',e['text']),'en'));story.append(v.P(e['zh']))
  for s in source_lines(e):story.append(v.P(s,'small'))
  story.append(v.P('认识[ ]  会用[ ]    次日[ ]  3日[ ]  7日[ ]  14日[ ]','small'));story.append(Spacer(1,12))
 _,m=v.save_pdf(path,'高频短语：100条单句中英对照',story,'phrases');return m

def reading_volumes():
 rows=load('reading_words_enriched500.json');idx=v.index_map();manifest=[];locations={}
 for vol in range(1,6):
  group=rows[(vol-1)*100:vol*100];path=OUT/f'08_阅读高频500_第{vol:02d}卷.pdf'
  title,story=v.volume_story(group,vol,idx,book_label='阅读高频500');doc,m=v.save_pdf(path,title,story,'reading_core');assert doc.page<=150
  manifest.append(m)
  for _,heading,pn in doc.nav:
   match=re.match(r'^\d{4}  (\S+)$',heading)
   if match:locations[match[1]]=dict(file=path.name,page=pn,volume=vol)
  links=[]
  with fitz.open(path) as pdf:
   for pn,page in enumerate(pdf,1):
    text=re.sub(r'\s+','',page.get_text())
    for r in group:
     t=idx[r.get('corpus_lemma',r['word'])];tag=f"全部出处：{t['file']}p{t['page']}"
     if re.search(re.escape(tag)+r'(?!\d)',text):links.append(dict(page=pn,text=t['file'],target=t['file'],target_page=t['page']))
  v.remote_links(path,links)
 assert len(locations)==500,len(locations);save('reading_vocabulary_volume_index.json',locations)
 return manifest

def write_notes():
 text='''# 阅读配句与词音义版说明（2026年10月30日）

原1500主词条与顺序不变，1239词改配阅读正文原句，261词因无可用清晰阅读句保留标明来源的听力原句。每条只对照该句的中文，不再套用整段解释。100个短语也改为单句对照。

06册增加中文简明释义；09册是阅读500词的词音义速记。08册五卷是相同500词的详细词条，按阅读正文出现次数排序，包含常见基础词。500词中336词与原1500重合，共1664个不同主词，不是新增500个生词。扩展词不虚增主词或频次。

阅读统计范围是2021年至2026年6月语料中的阅读正文。排除题干、选项、指令、解析及参考范文，不补入选词填空答案。沿用已有去重语料和屈折归并，另存阅读专用频次。全部出处总索引保留原全题型口径，不能把其中总次数当阅读次数。

旧词元specie混入的原始词形species在阅读册校正显示为species（物种），原始次数和位置不增加；查旧总索引时按specie定位。其他保留原统计的词元口径，如learning等词汇化形式另列。OCR字形校订只影响展示，原文、统计与校订记录分别保留。

阅读例句按原卷文字层或已有OCR进行归一文本比对；听力回查已生成补充原文页。文字匹配只能证明来源，不是语义准确性认证。中文主要为整理者依据英文编写或校订的参考译文；少数听力单句沿用第三方后经复核。没有提供或冒充官方译文、官方题目解析。

范文与翻译题的第三方来源、39篇作文和39道翻译双语对照保持原有标记；写作替换仍独立为07册。详细来源说明见《范文译文与分析来源说明.md》。本次发现的“600 millionaires”已校为“600位百万富翁”，而不是“6亿名”。所有译文仍应结合原文理解，未声称完成教师逐条审定。

推荐先用06或09快筛不会的词，再按相同排序和书签查01或08详解。详解每10词一组，速记每页24词。两个词库有重合，可只复习个人错词，避免重复背。
'''
 (R/'阅读配句与词音义版说明.md').write_text(text,encoding='utf8')
 ul={u['id']:u for u in load('corpus_units.json')};sl={s['id']:s for s in load('sentences.json')};stats=load('阅读正文词频统计.json')
 with (D/'阅读高频500全部出处.csv').open('w',encoding='utf-8-sig',newline='') as f:
  wr=csv.writer(f);wr.writerow(['阅读排名','词条','阅读次数','覆盖考次','近三年次数','原始词形','句子ID','英文原句','考次','套号','原PDF文件','PDF页码','阅读题型','正文位置'])
  for r in load('reading_words_enriched500.json'):
   s=stats[r.get('corpus_lemma',r['word'])]
   for o in s['occurrences']:
    u=ul[o['unit']];loc=u['locator'] if u['locator'].startswith('段落') else '正文'
    for src in o['sources']:wr.writerow([r['rank'],r['word'],s['count'],s['exam_coverage'],s['recent'],o.get('source_form',o['form']),o['sentence'],sl[o['sentence']]['text'],src['session'],src['suite'],src['file'],src.get('page'),u['subtype'],loc])
 with (R/'复算说明.md').open('a',encoding='utf8') as f:
  if 'make_reading_editions.py' not in (R/'复算说明.md').read_text(encoding='utf8'):f.write('\n\n阅读配句版：运行 make_reading_editions.py；它使用已存且可追溯的阅读配句数据，重建原1500、100短语、两份词音义速记及阅读500五卷。首次从原始计数复算依次运行 prepare_reading_oct27.py、assemble_reading_oct27.py，再按 enrich_vocabulary.main 的 input_name/output_names 参数生成候选1664，运行 assemble_reading_oct27.py --commit。不要直接用阅读解析代替逐句翻译。\n')

def generate():
 from assemble_reading_oct27 import commit
 commit();core=v.generate();new=[phrases_edition(),quick_edition()]+reading_volumes()+[quick_edition(load('reading_words_enriched500.json'),True)]
 manifest=[m for m in load('pdf_manifest.json') if m['kind'] not in ['phrases','quick_vocabulary','reading_core','reading_quick']]+new
 save('pdf_manifest.json',manifest);save('reading_revision_pdf_manifest.json',core+new);write_notes()
 old=(OUT/'06_核心词汇1500速记_仅单词与英音.pdf').resolve();arch=R/'历史版本/2026-10-27修订前'/old.name
 if old.exists() and arch.exists() and old.is_relative_to(OUT.resolve()):old.unlink()
 print('READING_EDITION_DONE',len(core+new),'changed PDFs',flush=True)
 return core+new
if __name__=='__main__':generate()
