import sys,json,re,csv,hashlib,collections,unicodedata,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'六级备考成果'/'数据'
sys.path.insert(0,str(DATA/'python_libs'));sys.stdout.reconfigure(encoding='utf-8')
import nltk
from nltk.stem import WordNetLemmatizer
from bs4 import BeautifulSoup
from rapidfuzz.fuzz import ratio,partial_ratio
nltk.data.path.insert(0,str(DATA/'nltk_data'))
WN=WordNetLemmatizer()
TOK=re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?(?:-[A-Za-z]+)*")
def norm(t):
 t=unicodedata.normalize('NFKC',t).replace('’',"'").replace('‘',"'").replace('\u00ad','')
 t=re.sub(r'(?<=[A-Za-z])-\s*\n\s*(?=[a-z])','',t)
 return re.sub(r'\s+',' ',t).strip()
def letters(t):return re.sub('[^a-z]','',t.lower())
def save(name,x): (DATA/name).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
dictionary={}
with (DATA/'ecdict.csv').open(encoding='utf-8-sig',newline='') as f:
 for row in csv.DictReader(f):
  w=row['word'].lower()
  if re.fullmatch(r"[a-z]+(?:-[a-z]+)*",w):dictionary[w]=row
save('dictionary_metadata.json',{'source':'https://github.com/skywind3000/ECDICT','entries':len(dictionary),'purpose':'词典义与词形参考，不替代语境判断'})
pages=json.loads((DATA/'pages_raw.json').read_text(encoding='utf-8'))
for p in pages:
 if p['method']=='ocr_pending':
  o=json.loads((DATA/'ocr'/f"{p['id']}.json").read_text(encoding='utf-8-sig'))
  recognized='\n'.join(x['text'] for x in o['lines'])
  recognized=re.sub(r'Transl\s*ation','Translation',recognized)
  if len(p['text'].strip())>=80 and 'Translation' in p['text'] and 'Translation' in recognized:
   p['text']=p['text'].split('Translation')[0]+'Translation\n'+recognized.split('Translation')[-1];p['method']='text+OCR Chinese'
  else:p['text']=recognized;p['method']='Windows OCR'
save('pages_with_ocr.json',pages)
byfile=collections.defaultdict(list)
for p in pages:byfile[p['file']].append(p)
units=[];prompts=[];translations=[];issues=[];paragraph_no=collections.Counter()
def addunit(category,text,sources,**kw):
 if not text.strip():return
 units.append({'category':category,'text':norm(text),'sources':sources,**kw})
def source(p,locator):
 return {k:p[k] for k in ['file','page','session','suite','method']}|{'locator':locator}
def collect_main(group):
 state='';sub='';para='';q='';buff=[];refs=[];skip=False
 def flush():
  nonlocal buff,refs
  if buff:
   cat={'listening':'听力选项','reading':'阅读真题'}.get(state)
   if cat:addunit(cat,' '.join(buff),list({json.dumps(x,ensure_ascii=False):x for x in refs}.values()),subtype=sub,locator=para or (f'题{q}' if q else '正文'))
  buff=[];refs=[]
 for p in group:
  text=p['text']
  text=unicodedata.normalize('NFKC',text)
  # Generic examination instructions are removed before paragraph reconstruction.
  text=re.sub(r'Directions\s*:.*?(?:centre\s*\.|center\s*\.|Answer\s*Sheet\s*[12]\s*\.)','',text,flags=re.S|re.I) if state!='writing' and 'Writing' not in text[:350] else text
  for raw in text.splitlines():
   line=raw.strip()
   if not line:continue
   compact=re.sub(r'\s+','',line)
   newstate=None
   if re.search(r'\bWriting\b',line) and ('Part' in line or re.fullmatch(r'Writing\s*(?:\([^)]*\))?',line)):newstate='writing'
   elif 'ListeningComprehension' in compact:newstate='listening'
   elif 'ReadingComprehension' in compact:newstate='reading'
   elif re.search(r'\bTranslation\b',line) and ('Part' in line or re.fullmatch(r'Translation\s*(?:\([^)]*\))?',line)):newstate='translation'
   if newstate:
    flush();state=newstate;sub='';para='';q='';skip=False;continue
   if state not in ['reading','listening']:continue
   if 'Directions:' in line or 'Directions :' in line:flush();skip=True
   if skip:
    if re.search(r'centre\s*\.|center\s*\.|Answer\s*Sheet\s*[12]\s*\.',line,re.I):skip=False
    continue
   if any(k in line for k in ['You may not use any','You should write','Answer Sheet','Questions ','全国只','内容与','www.','http','微信','扫码','六级','CET','真题','分钟']):continue
   if re.match(r'^(?:Part\s*[IVX]+|Section\s+[ABC]|Passage\s+(?:One|Two))\b',line,re.I):
    flush()
    if 'Section' in line:sub=norm(line)
    if 'Passage' in line:sub=norm(line)
    para='';continue
   if len(re.findall('[\u4e00-\u9fff]',line))>5:continue
   if re.fullmatch(r'\d+\s*',line):
    if 1<=int(line)<=55:flush();q=line
    continue
   if not re.search('[A-Za-z]{2}',line):continue
   if re.match(r'^\d+[.]\s*[A-D][)）]',line) or re.match(r'^[A-O][)）]',line):
    flush()
    qm=re.match(r'^(\d+)[.]',line)
    if qm:q=qm[1]
    parts=re.split(r'(?:^|\s)([A-O])[)）]\s*',line)
    if len(parts)>1:
     for j in range(1,len(parts)-1,2):
      frag=parts[j+1].strip()
      if frag:addunit('听力选项' if state=='listening' else '阅读真题',frag,[source(p,f'题{q} 选项{parts[j]}' if q else f'选项{parts[j]}')],subtype=sub,locator=f'题{q} 选项{parts[j]}')
     continue
   qm=re.match(r'^(\d{1,2})[.]\s*(.+)',line)
   if qm and 1<=int(qm[1])<=55:
    flush();q=qm[1];para=f'题{q}';line=qm[2]
   pm=re.match(r'^\[?([A-P])[)\]]\s*(.*)',line)
   if pm and state=='reading' and ('Section B' in sub):
    flush();para=f'段落{pm[1]}';line=pm[2];q=''
   if not line:continue
   buff.append(line);refs.append(source(p,para or (f'题{q}' if q else sub or '正文')))
 flush()
 # Prompts and Chinese translation originals are kept independently from lexical exam text.
 grouped=collections.defaultdict(list)
 for p in group:grouped[p['suite']].append(p)
 for suite,ps in grouped.items():
  full='\n'.join(p['text'] for p in ps)
  chunks=re.split(r'Listening\s*Comprehension',full,flags=re.I)
  writing=chunks[0]
  if 'Writing' not in writing:writing=full[:2400]
  m=re.search(r'(?:begins? with (?:the )?sentence|begin with (?:the )?sentence)\s*[“"](.+?)(?:[”"]\s*You can|[”"]\s*You should|\s*You can)',norm(writing),re.I)
  if m:prompt=m[1]
  else:
   m=re.search(r'Directions\s*:\s*(.+?)(?:You should write|Write your|You are required|Part\s*II)',norm(writing),re.I)
   prompt=m[1] if m else norm(writing)[:900]
  wp=next((p for p in ps if 'Writing' in p['text']),ps[0])
  prompts.append({'session':ps[0]['session'],'suite':suite,'prompt':prompt,'task':norm(writing)[:2000],'source':source(wp,'作文题目')})
  addunit('作文题干',prompt,[source(wp,'作文题目')],subtype='Writing',locator='题目')
  for pi,p in enumerate(ps):
   if 'Translation' in p['text']:
    tail=re.split(r'\bTranslation\b',p['text'])[-1]
    if pi+1<len(ps):tail+='\n'+ps[pi+1]['text']
    zh=[]
    for line in tail.splitlines():
     if len(re.findall('[\u4e00-\u9fff]',line))>=4 and not any(k in line for k in ['六级','微信','扫码','真题','答案','年6月英语']):zh.append(line.strip())
    if zh:translations.append({'session':p['session'],'suite':suite,'zh':re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])','',''.join(zh)),'source':source(p,'翻译原文')})
for file,group in byfile.items():
 if group[0]['kind']=='真题':collect_main(group)
print('MAIN units',len(units),'prompts',len(prompts),'translation originals',len(translations),flush=True)
# Clean supplemental listening transcripts, with Chinese paragraph explanations.
ref_files=list((ROOT/'补充资料_2026年6月'/'校对参考').glob('*_listening.html'))+list((ROOT/'补充资料_2026年6月').glob('*_听力解析.html'))
for file in ref_files:
 m=re.match(r'(202\d)-(\d{2})-([123])',file.name)
 if not m:continue
 session=f'{m[1]}-{m[2]}';suite=m[3]
 soup=BeautifulSoup(file.read_text(encoding='utf-8'),'html.parser')
 local=[p for p in pages if p['session']==session and p['kind']=='解析']
 for piece in soup.select('.lt-piece'):
  heading=piece.select_one('.lt-piece-head');title=heading.get_text(' ',strip=True) if heading else piece.get('id','')
  paragraphs=[];srcs=[];bilingual=[]
  for en in piece.select('.lt-body > .lt-en'):
   for extra in en.select('.exam-pno'):extra.decompose()
   et=norm(en.get_text(' ',strip=True));zh=en.find_next_sibling('p',class_='lt-zh');zt=zh.get_text(' ',strip=True) if zh else ''
   if not et:continue
   locator=en.get('id','段落');key=letters(et)
   scores=[(partial_ratio(key,letters(p['text'])),p) for p in local if len(letters(p['text']))>100]
   score,p=max(scores,key=lambda v:v[0]) if scores else (0,None)
   sr={'file':str(file.relative_to(ROOT)),'page':None,'session':session,'suite':suite,'method':'补充原文','locator':f'{title} {locator}','url':f'https://english-exam.lazynote.cn/cet6/sections/listening/{session}-{suite}/#{locator}'}
   if p and score>=82:sr['local_pdf_match']=source(p,locator);sr['match_score']=round(score,1)
   paragraphs.append(et);srcs.append(sr);bilingual.append({'en':et,'zh':zt,'source':sr})
  if paragraphs:addunit('听力原文',' '.join(paragraphs),srcs,subtype=title,locator=title,bilingual=bilingual)
print('LISTEN units',sum(u['category']=='听力原文' for u in units),flush=True)
# Recent reading paragraph interpretations are only attached where English text matches the local exam.
reading_refs=[];reading_materials=[]
for file in (ROOT/'补充资料_2026年6月'/'校对参考').glob('*_part3-*.html'):
 soup=BeautifulSoup(file.read_text(encoding='utf-8'),'html.parser')
 file_paragraphs=[]
 for para in soup.select('.art-passage__para'):
  p=para.find('p');m=re.search(r'\d+',para.get('id',''));notes=soup.select_one(f'#pp-{m[0]} .pp__read') if m else None
  if p:file_paragraphs.append(norm(p.get_text(' ',strip=True)))
  if p and notes:reading_refs.append({'en':norm(p.get_text(' ',strip=True)),'zh':notes.get_text(' ',strip=True),'source':str(file.relative_to(ROOT)),'note_type':'原句所在段的理解提示'})
 if file_paragraphs:reading_materials.append({'en':' '.join(file_paragraphs),'source':str(file.relative_to(ROOT))})
save('reading_bilingual_reference.json',reading_refs)
# Only near-identical complete paragraphs/materials are corrected; cloze text is left untouched.
corrections=[];candidates=reading_refs+reading_materials
for u in units:
 if u['category']!='阅读真题' or 'Section A' in u.get('subtype',''):continue
 key=letters(u['text'])
 if len(key)<150:continue
 session=u['sources'][0]['session']
 scored=[(ratio(key,letters(r['en'])),r) for r in candidates if session in r['source'] and .95*len(key)<len(letters(r['en']))<1.05*len(key)]
 if not scored:continue
 score,r=max(scored,key=lambda x:x[0])
 if score>=97 and norm(u['text'])!=norm(r['en']):
  corrections.append({'original':u['text'],'corrected':r['en'],'score':round(score,2),'original_sources':u['sources'],'reference':r['source']})
  u['text']=r['en'];u['proofread_reference']=r['source']
save('阅读文字双源校对记录.json',corrections)
# Reference essays and translations: explicit heading boundaries only; commentary remains excluded.
for file,group in byfile.items():
 if group[0]['kind']!='解析':continue
 if group[0]['session']=='2026-06':continue
 state=None;buf=[];refs=[]
 def flush_ref():
  if buf:addunit(state,' '.join(buf),list({json.dumps(x,ensure_ascii=False):x for x in refs}.values()),subtype=state,locator=state)
 for p in group:
  for raw in p['text'].splitlines():
   line=raw.strip();chinese=re.sub(r'\s','',line)
   if '参考范文' in chinese or '参考译文' in chinese:
    if state:flush_ref()
    state='作文范文' if '参考范文' in chinese else '翻译参考译文';buf=[];refs=[]
    # Answer quick sheets contain inline headings.
    line=re.split(r'参考(?:范文|译文)\s*[:：]?',chinese)[-1] if ':' in chinese or '：' in chinese else ''
   elif state and any(k in chinese for k in ['范文译文','写作句型','译点精析','答案详解','难词译注','PartII','PartⅢ','PartIII','听力原文','全文翻译']):
    flush_ref();state=None;buf=[];refs=[];continue
   if state:
    # Chinese marginal comments are removed from line, without replacing an unknown English word.
    line=re.split(r'[\u4e00-\u9fff]',line)[0].strip()
    line=re.sub(r'\s+[123]\s*$','',line)
    if len(TOK.findall(line))>=3:buf.append(line);refs.append(source(p,state))
 if state:flush_ref()
# 2026 model essays / translations are recovered from their dedicated sections, not the repeated tutorials.
for file,group in byfile.items():
 if group[0]['kind']!='解析' or group[0]['session']!='2026-06':continue
 for p in group:
  t=p['text']
  if '参考范文' in t and '英' in t and p['page']<20:
   m=re.search(r'参考范文[^\n]*\n(.+?)(?:整篇|中译|【第|逐段|A N A)',t,re.S)
   if m:
    en=' '.join(l for l in m[1].splitlines() if len(TOK.findall(l))>3 and not re.search('[\u4e00-\u9fff]',l))
    if len(TOK.findall(en))>80:addunit('作文范文',en,[source(p,'参考范文')],subtype='参考范文',locator='参考范文')
# Correct prompt wording by content rather than assuming cross-publisher suite numbers agree.
mappings=[];webmodels=[];webtranslations=[]
for file in sorted((ROOT/'补充资料_2026年6月'/'校对参考').glob('*_part1.html')):
 m=re.match(r'(202\d-\d{2})-([123])',file.name);session,websuite=m[1],m[2]
 soup=BeautifulSoup(file.read_text(encoding='utf-8'),'html.parser');di=soup.select_one('#directions');essay=soup.select_one('#essay')
 if not di:continue
 task=norm(di.get_text(' ',strip=True)).replace('sen tence','sentence');wm=re.search(r'sentence\s*[“"](.+?)[”"]\s*You',task,re.I)
 if wm:prompt=wm[1].strip()
 elif 'short passage' in task.lower():prompt=re.split(r'no more than 200\s*words\.',task,flags=re.I)[-1].strip()
 else:
  cm=re.search(r"comment on\s+(.+?)(?:\.\s*You should|\.)",task,re.I)
  prompt=cm[1] if cm else task
 candidates=[p for p in prompts if p['session']==session]
 scored=[(partial_ratio(letters(prompt),letters(p['task'])),p) for p in candidates]
 score,match=max(scored,key=lambda x:x[0]) if scored else (0,None)
 if score>=85:
  old=match['prompt'];match['prompt']=prompt;match['task']=task;match['web_source']=str(file.relative_to(ROOT));match['web_suite']=websuite
  mappings.append({'module':'写作','session':session,'web_suite':websuite,'local_suite':match['suite'],'score':round(score,1),'old_prompt':old,'verified_prompt':prompt})
  for u in units:
   if u['category']=='作文题干' and u['sources'][0]['session']==session and u['sources'][0]['suite']==match['suite']:u['text']=prompt
 if essay:
  en=norm(essay.get_text(' ',strip=True));zh=soup.select_one('#essay-zh')
  src={'file':str(file.relative_to(ROOT)),'page':None,'session':session,'suite':match['suite'] if match and score>=85 else websuite,'source_suite':websuite,'method':'第三方参考范文','locator':'essay','url':f'https://english-exam.lazynote.cn/cet6/sections/{session}-{websuite}/part1/#essay'}
  if match and score>=85:src['local_prompt_pdf']=match['source']
  webmodels.append({'category':'作文范文','text':en,'sources':[src],'subtype':'第三方参考范文','locator':'参考范文','bilingual':[{'en':en,'zh':zh.get_text(' ',strip=True).replace('【参考译文】','') if zh else '', 'source':src}]})
for file in sorted((ROOT/'补充资料_2026年6月'/'校对参考').glob('*_part-iv.html')):
 m=re.match(r'(202\d-\d{2})-([123])',file.name);session,websuite=m[1],m[2]
 soup=BeautifulSoup(file.read_text(encoding='utf-8'),'html.parser');stem=soup.select_one('#stem');eng=soup.select_one('#translation .tp-para')
 if not stem:continue
 zh=norm(stem.get_text(' ',strip=True));ch=lambda t:re.sub('[^\u4e00-\u9fff]','',t)
 candidates=[p for p in translations if p['session']==session]
 scored=[(partial_ratio(ch(zh),ch(p['zh'])),p) for p in candidates if ch(p['zh'])]
 score,match=max(scored,key=lambda x:x[0]) if scored else (0,None)
 if score<80:
  originals=[p for p in pages if p['kind']=='真题' and p['session']==session and 'Translation' in p['text']]
  scored=[(partial_ratio(ch(zh),ch(p['text'].split('Translation')[-1])),p) for p in originals if ch(p['text'].split('Translation')[-1])]
  score,orig=max(scored,key=lambda x:x[0]) if scored else (0,None)
  if score>=80:
   match={'session':session,'suite':orig['suite'],'zh':zh,'source':source(orig,'翻译原文')};translations.append(match)
 if match and score>=80:
  match['zh']=zh;match['web_source']=str(file.relative_to(ROOT));match['web_suite']=websuite
  mappings.append({'module':'翻译','session':session,'web_suite':websuite,'local_suite':match['suite'],'score':round(score,1)})
 else:
  issues.append({'reason':'翻译中文源匹配不足，保留网络来源','session':session,'web_suite':websuite,'score':score})
 if eng:
  src={'file':str(file.relative_to(ROOT)),'page':None,'session':session,'suite':match['suite'] if match and score>=80 else websuite,'source_suite':websuite,'method':'第三方参考译文','locator':'translation','url':f'https://english-exam.lazynote.cn/cet6/sections/{session}-{websuite}/part-iv/#translation'}
  if match and score>=80:src['local_prompt_pdf']=match['source']
  webtranslations.append({'category':'翻译参考译文','text':norm(eng.get_text(' ',strip=True)),'sources':[src],'subtype':'第三方参考译文','locator':'参考译文','bilingual':[{'en':norm(eng.get_text(' ',strip=True)),'zh':zh,'source':src}]})
save('本地参考文本待校对.json',[u for u in units if u['category'] in ['作文范文','翻译参考译文']])
units=[u for u in units if u['category'] not in ['作文范文','翻译参考译文']]+webmodels+webtranslations
save('套号与文字校对记录.json',mappings)
# Deduplicate shared complete materials, not isolated identical options from different questions.
materialgroups=collections.defaultdict(list);other=[]
for u in units:
 s=u['sources'][0]
 if u['category'] in ['听力选项','阅读真题']:
  materialgroups[(s['session'],s['file'],s['suite'],u['category'],u.get('subtype',''))].append(u)
 else:other.append(u)
dedup=[];materialseen={};duplicates=[]
for mk,us in materialgroups.items():
 fingerprint=letters(' '.join(u['text'] for u in us));key=(mk[0],mk[3],mk[4],fingerprint)
 if key in materialseen:
  base=materialseen[key];lookup=collections.defaultdict(list)
  for u in base:lookup[letters(u['text'])].append(u)
  for u in us:
   candidates=lookup[letters(u['text'])]
   if candidates:candidates[0]['sources'].extend(u['sources'])
  duplicates.append({'session':mk[0],'file':mk[1],'category':mk[3],'subtype':mk[4],'units':len(us)})
 else:materialseen[key]=us;dedup.extend(us)
otherseen={}
for u in other:
 key=(u['sources'][0]['session'],u['category'],letters(u['text']))
 if key in otherseen:otherseen[key]['sources'].extend(u['sources'])
 else:otherseen[key]=u;dedup.append(u)
for i,u in enumerate(dedup):u['id']=f'U{i+1:05d}'
units=dedup;save('重复材料记录.json',duplicates)
save('corpus_units.json',units);save('writing_prompts.json',prompts);save('translation_originals.json',translations)
# Build full, reproducible occurrence records.
sentences=[];words=collections.defaultdict(lambda:{'count':0,'sessions':set(),'recent':0,'categories':collections.Counter(),'forms':collections.Counter(),'occurrences':[]})
excluded=collections.Counter(); posmaps={'J':'a','V':'v','N':'n','R':'r'}
for ui,u in enumerate(units):
 sessions={s['session'] for s in u['sources']};recent=any(s>='2024-01' for s in sessions)
 chunks=u.get('bilingual') or [{'en':u['text'],'zh':'','source':None}]
 for chunk in chunks:
  en=norm(re.sub(r'\[\s*\d+\s*\]','',chunk['en']))
  en=re.sub(r'\b(?:M|W)\s*[:.]\s*','',en)
  # Sentences preserve original blanks and are not completed with reference answers.
  for sent in nltk.sent_tokenize(en):
   original_tokens=TOK.findall(sent);tokens=[];token_origins=[]
   contractions={"can't":['can','not'],"won't":['will','not'],"shan't":['shall','not'],"i'm":['I','am'],"it's":['it','is'],"that's":['that','is'],"there's":['there','is'],"what's":['what','is']}
   for oi,ot in enumerate(original_tokens):
    low=ot.lower();parts=contractions.get(low)
    if parts is None and low.endswith("n't"):parts=[ot[:-3],'not']
    if parts is None:
     cm=re.match(r"^(.+)'(re|ve|ll|d)$",ot,re.I)
     if cm:parts=[cm[1],{'re':'are','ve':'have','ll':'will','d':'would'}[cm[2].lower()]]
    for token in parts or [ot]:tokens.append(token);token_origins.append((oi,ot))
   if not tokens:continue
   if len(tokens)>180:issues.append({'reason':'异常长段，保留原文待核对','unit':u['id']})
   tags=nltk.pos_tag(tokens);lemmata=[]
   sid=f'S{len(sentences)+1:06d}'
   sr=chunk.get('source');sources=[sr] if sr else u['sources']
   if sr:
    # Aliases for the same transcript paragraph are retained separately by deduplication.
    same=[s for s in u['sources'] if s['locator'].split()[-1]==sr['locator'].split()[-1]]
    sources=same or [sr]
   for ti,(token,tag) in enumerate(tags):
    form=token.lower().replace('’',"'")
    if form.endswith("'s"):form=form[:-2]
    if len(form)<2 or form in ['nt','re','ve','ll','don','doesn','didn','isn','wasn','aren','weren','wouldn','couldn','shouldn','tve','fve']:continue
    lemma=WN.lemmatize(form,posmaps.get(tag[:1],'n'))
    if form=='according' and ti+1<len(tokens) and tokens[ti+1].lower()=='to':lemma='according'
    if lemma not in dictionary:
     lemma=WN.lemmatize(form,'v') if WN.lemmatize(form,'v') in dictionary else form
    if lemma not in dictionary:
     excluded[form]+=1;continue
    lemmata.append(lemma)
    w=words[lemma];w['count']+=1;w['sessions'].update(sessions);w['recent']+=int(recent);w['categories'][u['category']]+=1;w['forms'][form]+=1
    w['occurrences'].append({'sentence':sid,'position':token_origins[ti][0],'source_form':token_origins[ti][1],'form':form,'pos':tag,'sources':sources,'unit':u['id']})
   sentences.append({'id':sid,'unit':u['id'],'category':u['category'],'text':sent,'zh':chunk.get('zh',''),'zh_type':'原句所在段的参考译文' if chunk.get('zh') else '', 'sources':sources,'lemmata':lemmata})
 if ui%300==0:print('STATS',ui,'of',len(units),flush=True)
for lemma,w in words.items():
 w['sessions']=sorted(w['sessions']);w['categories']=dict(w['categories']);w['forms']=dict(w['forms']);row=dictionary[lemma]
 w['meaning']=row['translation'].replace('\\n','；');w['phonetic']=row['phonetic'];w['dictionary_pos']=row['pos'];w['tag']=row['tag'];w['coverage']=len(w['sessions'])
 w['exam_count']=sum(v for k,v in w['categories'].items() if k not in ['作文范文','翻译参考译文'])
 w['reference_count']=w['count']-w['exam_count']
 w['exam_sessions']=sorted({s['session'] for o in w['occurrences'] for s in o['sources'] if next((z['category'] for z in sentences if z['id']==o['sentence']),None) not in ['作文范文','翻译参考译文']}) if False else []
# Compute main-corpus coverage separately to avoid using reference prose in the learning ranking.
slookup={s['id']:s for s in sentences}
for lemma,w in words.items():
 exam_occ=[o for o in w['occurrences'] if slookup[o['sentence']]['category'] not in ['作文范文','翻译参考译文']]
 w['exam_sessions']=sorted({s['session'] for o in exam_occ for s in o['sources']});w['exam_coverage']=len(w['exam_sessions']);w['exam_recent']=sum(any(s['session']>='2024-01' for s in o['sources']) for o in exam_occ)
save('sentences.json',sentences);save('word_statistics.json',dict(words));save('待核对词形.json',dict(excluded.most_common()))
save('corpus_summary.json',{'pdf_files':len(byfile),'pdf_pages':len(pages),'ocr_pages':sum('OCR' in p['method'] for p in pages),'units':len(units),'sentences':len(sentences),'valid_lemmas':len(words),'tokens':sum(w['count'] for w in words.values()),'categories':dict(collections.Counter(u['category'] for u in units)),'prompts':len(prompts),'translation_tasks':len(translations),'excluded_tokens':sum(excluded.values()),'issues':issues})
print('SUMMARY',(DATA/'corpus_summary.json').read_text(encoding='utf-8'),flush=True)
