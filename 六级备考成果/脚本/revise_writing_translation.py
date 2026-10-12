import sys,json,re,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'六级备考成果';D=R/'数据';OUT=R/'学习资料';QA=R/'核验'/'写作翻译新版';QA.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(D/'python_libs'));sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup
import pymupdf as fitz
from reportlab.platypus import Table,TableStyle,KeepTogether,Spacer,PageBreak,Image as RLImage
from reportlab.lib import colors
from PIL import Image,ImageDraw,ImageFont
OLD=R/'脚本'/'build_pdfs.py'
prefix=OLD.read_text(encoding='utf-8').split('# Produce searchable paragraph-level sources')[0]
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith('W=load('))
ns={'__file__':str(OLD),'__name__':'writing_pdf_styles'};exec(compile(prefix,str(OLD),'exec'),ns)
P,H,cover,build=[ns[k] for k in ['P','H','cover','build']]
def load(n):return json.loads((D/n).read_text(encoding='utf-8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def clean(t):return re.sub(r'\s+',' ',t).strip()
def signature(t):return re.sub('[^a-z0-9]','',t.lower())
def cn_signature(t):return re.sub('[^\u4e00-\u9fff0-9]','',t)
def original_signature(t):return re.sub('[^\u4e00-\u9fffA-Za-z0-9]','',t).lower()
def key(p):return p['session']+'-'+p['suite']
def locator(p):
 s=p['source'];v=f"{p['session']} 第{p['suite']}套 | {Path(s['file']).name} 第{s['page']}页"
 if p.get('web_suite') and p['web_suite']!=p['suite']:v+=f" | 对照来源编为第{p['web_suite']}套"
 return v
def parse_bank(t):return [{'english':a.strip(),'chinese':b.strip()} for line in t.splitlines() for a,b in [line.split('|',1)]]
def forms(w):
 a=[w,w+'s',w+'ed',w+'ing']
 if w.endswith('e'):a.extend([w+'d',w[:-1]+'ing'])
 if w.endswith('y') and len(w)>2 and w[-2] not in 'aeiou':a.extend([w[:-1]+'ies',w[:-1]+'ied'])
 if w.endswith(('s','x','ch','sh')):a.append(w+'es')
 if w.endswith('ies'):a.append(w[:-3]+'y')
 elif w.endswith('s') and not w.endswith(('ss','us','is')) and w!='news':a.append(w[:-1])
 return list(dict.fromkeys(a))
def evaluate(bank,docs):
 rows=[]
 for item in bank:
  p=item['english'].split();head=r'\s+'.join(re.escape(x) for x in p[:-1]);tail='(?:'+'|'.join(re.escape(x) for x in sorted(forms(p[-1]),key=len,reverse=True))+')'
  pattern=re.compile(r'(?<![A-Za-z])'+(head+r'\s+' if head else '')+tail+r'(?![A-Za-z])',re.I);hits=[]
  for d in docs:
   matches=list(pattern.finditer(d['english_text']))
   if matches:hits.append({'id':d['id'],'count':len(matches),'forms':sorted({m[0] for m in matches})})
  rows.append(dict(item,hits=hits,count=sum(x['count'] for x in hits),coverage=len(hits)))
 return sorted(rows,key=lambda x:(bool(x['hits']),x['coverage'],x['count']),reverse=True)
def vocab_table(rows,original=True):
 cells=[[P('单词或短语','small'),P('中文含义','small'),P('对应题目' if original else '用途','small')]]
 for r in rows:
  ids=[h['id'] for h in r['hits']];refs='；'.join(ids[:3])+(' 等' if len(ids)>3 else '')
  cells.append([P(r['english'],'index'),P(r['chinese'],'index'),P(refs if original else '同主题迁移','small')])
 t=Table(cells,colWidths=[210,178,111],repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EEF3F7')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));return t
def paired(pairs,writing):
 story=[]
 for i,pair in enumerate(pairs,1):
  story.append(KeepTogether([P(f'第{i}'+('段 英文原文' if writing else '句 中文原文'),'small'),P(pair['en'] if writing else pair['zh'],'quote' if writing else 'body'),P('中文译文' if writing else '参考英译','small'),P(pair['zh'] if writing else pair['en'],'body' if writing else 'quote'),Spacer(1,8)]))
 return story
def theme_words(story,theme,bank,docs,mode,records):
 rows=evaluate(bank,docs);original=[r for r in rows if r['hits']];extra=[r for r in rows if not r['hits']];records.append({'section':mode,'theme':theme,'paper_ids':[p['id'] for p in docs],'words':rows})
 story.append(H('本主题词汇与短语',1,key=mode+'-bank-'+str(len(records))));story.append(P('原文表达对应本主题'+('题干及参考范文' if mode=='writing' else '参考英译')+'。题号沿用本地原卷，规则词形变化合并匹配。','small'))
 if original:story.append(vocab_table(original))
 if extra:story.append(P('可迁移表达  可用于同主题练习，未在本组文本中逐字出现。','small'));story.append(vocab_table(extra,False))
 return rows
def generate(update_manifest=True):
 banks=load('writing_translation_topic_banks.json');docs_w=[];docs_t=[];audit=[]
 for p in load('writing_analysis.json'):
  html=BeautifulSoup((ROOT/p['web_source']).read_text(encoding='utf-8'),'html.parser');en=[clean(x.get_text(' ',strip=True)) for x in html.select('#essay > p')];zh=[clean(x.get_text(' ',strip=True)) for x in html.select('#essay-zh .wp-trans__para')]
  if key(p)=='2023-03-1' and len(zh)==1:
   t=zh[0];a=t.index('然而');b=t.index('总之');zh=[t[:a],t[a:b],t[b:]]
  assert en and len(en)==len(zh) and all(zh),key(p)
  docs_w.append(dict(p,id=key(p),pairs=[{'en':a,'zh':b} for a,b in zip(en,zh)],english_text=p['prompt']+' '+' '.join(en)));audit.append({'section':'writing','id':key(p),'paragraphs':len(en),'aligned':True,'source':p['web_source']})
 for p in load('translation_originals.json'):
  html=BeautifulSoup((ROOT/p['web_source']).read_text(encoding='utf-8'),'html.parser');en=clean(html.select_one('#translation .tp-para').get_text(' ',strip=True));pairs=[]
  for u in html.select('.tqp-unit'):pairs.append({'en':clean(u.select_one('.tqp-final').get_text(' ',strip=True)),'zh':re.sub(r'^\d+[.]\s*','',clean(u.select_one('.tqp-stem').get_text(' ',strip=True)))})
  same_en=signature(' '.join(x['en'] for x in pairs))==signature(en);same_zh=original_signature(''.join(x['zh'] for x in pairs))==original_signature(p['zh']);mode='sentence' if same_en and same_zh else 'whole';theme,title=banks['translation_themes'][key(p)]
  docs_t.append(dict(p,id=key(p),theme=theme,title=title,pairs=pairs if mode=='sentence' else [{'en':en,'zh':p['zh']}],alignment=mode,english_text=en));audit.append({'section':'translation','id':key(p),'mode':mode,'English_matches_full_reference':same_en,'Chinese_matches_full_original':same_zh,'source':p['web_source']})
 assert len(docs_w)==len(docs_t)==39
 records=[];story=cover('写作与翻译主题对照学习册','39篇作文范文中英对照 39道翻译原文英译对照 按主题整理词汇','先看主题词汇，再读紧邻的原文与译文，最后遮住译文独立复述或翻译。作文按8个主题、翻译按11个主题归类。词汇表区分原文表达和可迁移表达，各题保留年份、套号与原卷页码。\n\n范文及英译为配套第三方参考表达。题目主题和首句的中文另行翻译；不同来源的套号差异单独标明。')
 for number,(theme,bank) in enumerate(banks['writing'].items(),1):
  papers=sorted([p for p in docs_w if p['theme']==theme],key=lambda p:(p['session'],p['suite']),reverse=True)
  if number>1:story.append(PageBreak())
  story.append(H(f'写作主题{number:02d} {theme} 共{len(papers)}题',key='wt-'+str(number)));rows=theme_words(story,theme,parse_bank(bank),papers,'writing',records)
  for p in papers:
   story.append(H(p['id']+' '+p['title'],1,key='w-'+p['id']));story.append(P(locator(p),'small'));story.append(P('题目主题或给定首句 英文','small'));story.append(P(p['prompt'].replace('dressing9','dressing,').strip(),'quote'));story.append(P('题意中文','small'));story.append(P(banks['prompt_translations'][p['id']]))
   if p['form']=='图表描述':
    s=p['source'];pdf=fitz.open(ROOT/s['file']);page=pdf[s['page']-1];words=page.get_text('words');wy=min(w[1] for w in words if w[4]=='Writing');ly=min(w[1] for w in words if w[4]=='Listening');clip=fitz.Rect(35,max(0,wy-18),page.rect.width-35,ly-14);img=QA/f'graph_{p["id"]}.png';page.get_pixmap(matrix=fitz.Matrix(2,2),clip=clip,alpha=False).save(img);pdf.close();story.append(P('原卷题干与图表','small'));story.append(RLImage(str(img),width=499,height=499*clip.height/clip.width))
   story.append(P('写作要求：150至200词。给定首句是否必须照抄请以原题要求为准；图表题先描述图表，材料评论题需评论现象并提出措施。','small'));specific=[r for r in rows if any(h['id']==p['id'] for h in r['hits'])]
   if specific:story.append(P('本题可直接积累：'+'；'.join(r['english']+' '+r['chinese'] for r in specific[:10]),'small'))
   story.append(H('参考范文与中文译文',2,key='w-text-'+p['id']));story.extend(paired(p['pairs'],True))
 for number,(theme,bank) in enumerate(banks['translation'].items(),1):
  papers=sorted([p for p in docs_t if p['theme']==theme],key=lambda p:(p['session'],p['suite']),reverse=True);assert papers,theme;story.append(PageBreak());story.append(H(f'翻译主题{number:02d} {theme} 共{len(papers)}题',key='tt-'+str(number)));rows=theme_words(story,theme,parse_bank(bank),papers,'translation',records)
  for p in papers:
   story.append(H(p['id']+' '+p['title'],1,key='t-'+p['id']));story.append(P(locator(p),'small'));specific=[r for r in rows if any(h['id']==p['id'] for h in r['hits'])]
   if specific:story.append(P('本题重点表达：'+'；'.join(r['english']+' '+r['chinese'] for r in specific[:12]),'small'))
   if p['alignment']=='sentence':story.extend(paired(p['pairs'],False))
   else:story.extend([P('中文原文','small'),P(p['zh']),P('参考英译','small'),P(p['english_text'],'quote')])
   url=f'https://english-exam.lazynote.cn/cet6/sections/{p["session"]}-{p.get("web_suite",p["suite"])}/part-iv/';story.append(P(f'<link href="{url}" color="#2F6B86">查看本题参考英译来源</link>','small',True))
 story.append(PageBreak());story.append(H('附录一 40个句式与中文用法',key='appendix-structures'))
 for i,p in enumerate(load('sentence_structures.json'),1):story.append(KeepTogether([P(f'{i:02d}  '+p['pattern'],'quote'),P(p['note']),Spacer(1,5)]))
 story.append(H('附录二 20句中译英练习',key='appendix-practice'));practice=load('translation_practice.json')
 for i,p in enumerate(practice,1):story.append(KeepTogether([P(f'练习{i:02d} '+p['zh']),P('先独立翻译，答案集中放在后面。','small'),Spacer(1,28)]))
 story.append(PageBreak());story.append(H('附录三 练习答案对照',key='appendix-answers'))
 for i,p in enumerate(practice,1):story.append(KeepTogether([P(f'{i:02d} 中文原句','small'),P(p['zh']),P('参考英译','small'),P(p['answer'],'quote'),P('重点：'+p['concept']+' - '+p['expression'],'small'),Spacer(1,8)]))
 from writing_replacements import build_data
 replacements=build_data();story.append(PageBreak());story.append(H('附录四 写作同义替换100组',key='writing-replacements'))
 story.append(P('60组单词、40组短语，按8个作文主题整理。基础句和改写句均为自编练习，不计入真题词频；每组说明语义、程度和句法变化。存在意义变化的表达作为辨析学习，不能机械换词。'))
 story.append(P('练习顺序：读中文确定意思 → 遮住改写句自己改 → 核对主语、因果、程度、范围和搭配。范文链接仅供观察相同表达的真实语境。','small'))
 for tn,theme in enumerate(replacements['themes'],1):
  if tn>1:story.append(PageBreak())
  story.append(H(f'替换主题{tn:02d} {theme}',1,key='replace-theme-'+str(tn)))
  for r in [r for r in replacements['groups'] if r['theme']==theme]:
   purpose='描述现象与行动'
   if r['base'] in ['important','be important for','good','bad','healthy','valuable','enough','fair','special','advantage','ability']:purpose='说明价值与评价'
   elif r['base'] in ['cause','because of','as a result','lead to','help to','be related to']:purpose='解释因果与关联'
   elif r['base'] in ['different','on the other hand','even though']:purpose='比较与让步'
   elif r['base'] in ['think','in my opinion','agree with']:purpose='表达观点'
   elif r['base'] in ['try to','do something about','take part in','work together','deal with','protect','save','reduce','keep','build']:purpose='提出措施与建议'
   r['function']=purpose;observations=[]
   for p in docs_w:
    if p['theme']!=theme:continue
    matched=next((a for a in [r['base'],r['alternative']] if re.search(r'(?<![A-Za-z])'+re.escape(a)+r'(?![A-Za-z])',p['english_text'],re.I)),None)
    if matched:observations.append({'id':p['id'],'expression':matched,'source':p['source']})
   r['essay_observations']=observations[:2]
   block=[H(r['id']+' '+r['base']+' → '+r['alternative'],2,key='replacement-'+r['id']),P(r['kind']+'替换 · '+purpose,'small'),P('区别与结构：'+r['distinction']),P('基础句（自编）','small'),P(r['before'],'quote'),P(r['chinese_before']),P('改写句（自编）','small'),P(r['after'],'quote'),P(r['chinese_after']),P('常见误用：'+r['misuse'])]
   for o in observations[:2]:block.append(P(f'<link href="#w-{o["id"]}" color="#2F6B86">范文语境：{o["id"]} · {o["expression"]}</link>','small',True))
   story.append(KeepTogether(block));story.append(Spacer(1,10))
 story.append(PageBreak());story.append(H('附录五 32道替换练习',key='replacement-exercises'));story.append(P('每个主题4道。按提示改写英文，并检查中文意思是否改变。答案在下一部分；允许其他符合语义、搭配和语法的表达。'))
 for theme in replacements['themes']:
  story.append(H(theme+' · 练习',1,key='practice-theme-'+str(replacements['themes'].index(theme))))
  for r in [x for x in replacements['exercises'] if x['theme']==theme]:story.append(KeepTogether([P(r['id']+' '+r['prompt'],'quote'),P(r['chinese']),P('使用提示：'+r['hint'],'small'),Spacer(1,32)]))
 story.append(PageBreak());story.append(H('附录六 32道练习答案与条件',key='replacement-answers'))
 for r in replacements['exercises']:story.append(KeepTogether([H(r['id']+' '+r['theme'],1,key='answer-'+r['id']),P(r['answer'],'quote'),P(r['answer_chinese']),P('成立条件：'+r['explanation']),P(f'<link href="#replacement-{r["replacement_id"]}" color="#2F6B86">返回对应辨析 {r["replacement_id"]}</link>','small',True),Spacer(1,10)]))
 save('writing_replacement_guidance.json',replacements)
 target=OUT/'04_写作与翻译专项册.pdf'
 if update_manifest:
  backup=R/'历史版本'/'04_写作与翻译专项册_原词频版.pdf';backup.parent.mkdir(exist_ok=True)
  if target.exists() and not backup.exists():shutil.copy2(target,backup)
 doc=build(target,'写作与翻译主题对照学习册',story,'writing_translation');terms=sum(len(t['words']) for t in records);seen=sum(bool(w['hits']) for t in records for w in t['words']);save('写作翻译新版主题词汇.json',{'themes':records,'topic_expression_entries':terms,'entries_found_in_texts':seen,'transfer_entries':terms-seen});save('写作翻译新版对照核验.json',{'writing_tasks':39,'translation_tasks':39,'writing_themes':8,'translation_themes':11,'entries':audit,'English_and_Chinese_complete':True})
 if update_manifest:
  manifest=load('pdf_manifest.json')
  for m in manifest:
   if m['kind']=='writing_translation':m.update(title='写作与翻译主题对照学习册',pages=doc.page)
  save('pdf_manifest.json',manifest)
 return {'file':str(target.relative_to(ROOT)),'title':'写作与翻译主题对照学习册','pages':doc.page,'terms':terms,'seen':seen}
def verify(result):
 target=ROOT/result['file'];doc=fitz.open(target);errors=[];contacts=[];batch=[];font=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',15)
 def flush():
  if not batch:return
  canvas=Image.new('RGB',(1200,1710),'#e9edf1');dr=ImageDraw.Draw(canvas)
  for j,(im,pn) in enumerate(batch):
   im.thumbnail((190,255));x=(j%6)*200;y=(j//6)*285;canvas.paste(im,(x+5,y+24));dr.text((x+5,y+3),f'p{pn}',font=font,fill='black')
  path=QA/f'contact_{len(contacts)+1:02d}.jpg';canvas.save(path,quality=90);contacts.append(str(path.relative_to(ROOT)));batch.clear()
 alltext=[]
 for i,page in enumerate(doc):
  text=page.get_text();alltext.append(text)
  if '\x00' in text or '\ufffd' in text:errors.append({'page':i+1,'error':'missing glyph'})
  for block in page.get_text('dict')['blocks']:
   if block['type']!=0:continue
   for line in block['lines']:
    for span in line['spans']:
     x0,y0,x1,y1=span['bbox']
     if x0<40 or x1>page.rect.width-34 or y0<35 or y1>page.rect.height-15:errors.append({'page':i+1,'error':'bounds','text':span['text'][:60]})
  for link in page.get_links():
   if link['kind']==fitz.LINK_GOTO and not 0<=link.get('page',-1)<len(doc):errors.append({'page':i+1,'error':'navigation'})
  pix=page.get_pixmap(matrix=fitz.Matrix(.38,.38),alpha=False);batch.append((Image.frombytes('RGB',(pix.width,pix.height),pix.samples),i+1))
  if len(batch)==36:flush()
  if i in {0,1,2,3,9,19,len(doc)//2,len(doc)-2,len(doc)-1}:page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(QA/f'page_{i+1:03d}.png')
 flush();assert not errors,errors[:10];assert doc.get_toc()
 for sid in load('writing_translation_topic_banks.json')['translation_themes']:assert sid in ''.join(alltext)
 report=load('验收报告.json');entry={'file':result['file'],'pages':len(doc),'bookmarks':len(doc.get_toc()),'links':sum(len(p.get_links()) for p in doc),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()};report['pdf_checks']=[entry if x['file']==result['file'] else x for x in report['pdf_checks']];report['pages']=sum(x['pages'] for x in report['pdf_checks']);report['rendered_pages']=report['pages'];report['writing_translation_revision']={'pages':len(doc),'contacts':contacts,'errors':errors,'writing_pairs':39,'translation_pairs':39,'themed_entries':result['terms'],'visual_review':'pending'};save('验收报告.json',report);print('REVISED',json.dumps(result,ensure_ascii=False),'QA_ERRORS',len(errors),'CONTACTS',len(contacts),flush=True)
if __name__=='__main__':verify(generate())
