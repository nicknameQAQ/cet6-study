"""Reading-only counts and sentence selection; original all-section counts stay intact."""
import sys,json,re,collections,math,hashlib,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'六级备考成果';D=R/'数据';QA=R/'核验/2026-10-27修订'
sys.stdout.reconfigure(encoding='utf8')
def load(n):return json.loads((D/n).read_text(encoding='utf8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def normal(t):return re.sub('[^a-z0-9]','',t.lower())
def tokens(t):return re.findall("[A-Za-z]+(?:[-'][A-Za-z]+)*",t)

FUNCTION=set('a an the and or but if as at by for from in into of on out to up with about after all also am are be been being can could did do does doing each either even ever every few first had has have having he her here hers herself him himself his how i it its itself just last little lot many may me men might more most much must my new next no nor not now off old once one only other our ours ourselves over own same say says said see seem she should so some such than that their theirs them themselves then there these they this those through too two under until us very was we well were what when where which while who whom why will would you your yours yourself yourselves whose whatever whether whenever otherwise thus however therefore hence because although despite unless yet perhaps almost enough especially another any anyone anybody anything someone somebody something everyone everybody everything nothing neither both per upon within without throughout among against toward towards versus whilst though'.split())
# Content verbs are useful in reading; retain them even when also used as discourse markers.
FUNCTION-=set('say says said see seem'.split())
FUNCTION.update('between across along before during down again above below beside besides beyond around behind toward towards onto through throughout whenever wherever moreover otherwise often others else indeed instead rather thereby nevertheless nonetheless somehow somewhat anyway'.split())
NAMES=set('america american british england english china chinese london york john peter james william frank brown michael mary smith jane uk usa cet et al ii iii iv pdf'.split())
INSTRUCTIONS=set('directions answer sheet cet6 section part passage minutes comprehension marked corresponding choices choose'.split())
BAD_EXAMPLES=set('S006114 S008207 S007004 S001541 S002108 S003962 S004256 S004077 S003996 S001250 S001275'.split())

def body_unit(u):
 if u['category']!='阅读真题' or '选项' in u['locator']:return False
 if u['locator']=='正文' or u['locator'].startswith('段落'):return True
 # The old parser retained Q45/Q50 as a locator after switching to Passage One/Two.
 # A long unit in that position is passage text; short question stems are excluded.
 return len(tokens(u['text']))>=55 and (u['subtype'].startswith('Passage') or u['subtype'].startswith('Section C'))

def main():
 units=load('corpus_units.json');ul={u['id']:u for u in units};S=load('sentences.json');sl={s['id']:s for s in S};W=load('word_statistics.json');core=load('core_words_enriched1500.json');phrases=load('core_phrases.json')
 bodies={u['id']:u for u in units if body_unit(u)}
 duplicate_units={};seen={}
 for uid,u in bodies.items():
  exams=tuple(sorted({s['session'] for s in u['sources']}));key=(exams,u['subtype'].split(' 英语菌')[0],normal(u['text']))
  if key in seen and len(tokens(u['text']))>=50:duplicate_units[uid]=seen[key]
  else:seen[key]=uid
 canonical={uid:duplicate_units.get(uid,uid) for uid in bodies}
 reading={};ranked=[]
 for word,raw in W.items():
  occ=[o for o in raw['occurrences'] if o['unit'] in bodies and o['unit'] not in duplicate_units and not o['pos'].startswith('NNP')]
  if not occ:continue
  sessions=sorted({s['session'] for o in occ for s in o['sources']});cats=collections.Counter()
  for o in occ:
   t=ul[o['unit']]['subtype'];cats['选词填空' if 'Section A' in t else '长篇阅读' if 'Section B' in t else '仔细阅读']+=1
  record=dict(word=word,count=len(occ),exam_coverage=len(sessions),exam_sessions=sessions,recent=sum(any(s['session']>='2024-01' for s in o['sources']) for o in occ),categories=dict(cats),forms=dict(collections.Counter(o['form'] for o in occ)),occurrences=occ)
  reading[word]=record
  if word.isalpha() and len(word)>=3 and word not in FUNCTION|NAMES|INSTRUCTIONS and sessions and not re.search(r'(?:男名|女名|姓氏|人名)',raw['meaning'][:50]):ranked.append(word)
 ranked.sort(key=lambda w:(-reading[w]['count'],-reading[w]['exam_coverage'],-reading[w]['recent'],w))
 ipa={}
 for line in (D/'pronunciation/en_UK.txt').read_text(encoding='utf8').splitlines():
  if '\t' in line:a,b=line.split('\t',1);ipa[a]=b
 sys.path.insert(0,str(R/'脚本'));from vocabulary_editorial import UK_OVERRIDES
 ipa.update(UK_OVERRIDES)
 ranked=[k for k in ranked if ipa.get(k)][:500];assert len(ranked)==500
 save('阅读正文词频统计.json',reading)
 save('阅读高频500选词.json',[dict(rank=i+1,word=w,statistics=reading[w]) for i,w in enumerate(ranked)])
 pages={(p['file'],p['page']):p for p in load('pages_with_ocr.json')}
 pagecache={k:normal(v['text']) for k,v in pages.items()}
 def proof(s):
  needle=normal(s['text']);choices=[]
  for src in s['sources']:
   if src.get('page') is None:continue
   p=src['page'];fn=src['file'];text=pagecache.get((fn,p),'')
   for end in range(p,p+3):
    if end>p:text+=pagecache.get((fn,end),'')
    if needle and needle in text:choices.append((end-p,src,end));break
  if not choices:return None
  _,src,end=min(choices,key=lambda x:(x[0],x[1]['file']));return dict(source=copy.deepcopy(src),page_start=src['page'],page_end=end,verification='原卷文字层或已存OCR逐字符归一比对',method=pages.get((src['file'],src['page']),{}).get('method',''))
 proof_cache={};candidates={};target_words={r['word'] for r in core}|set(ranked)
 # Existing occurrence tags give the inflected form and avoid filling original cloze gaps.
 for word in target_words:
  for o in W[word]['occurrences']:
   s=sl[o['sentence']];uid=o['unit']
   if uid not in bodies or o['pos'].startswith('NNP') or s['id'] in BAD_EXAMPLES:continue
   t=s['text'];ts=tokens(t)
   if not 7<=len(ts)<=42 or len(t)>340:continue
   if not re.match(r'^[\"\u201c\u2018\']?[A-Z]',t) or not re.search(r'[.!?][\"\u201d\u2019\']?$',t):continue
   if re.search(r'\^|\bfbr\b|\bfbrm\b|www\.|Directions|Answer Sheet|_{2}|\b(?:2[6-9]|3\d|4\d|5[0-5])\b|[À-ÖØ-öø-ÿ]',t):continue
   if len(s['lemmata'])/max(1,len(ts))<.82:continue
   if s['id'] not in proof_cache:proof_cache[s['id']]=proof(s)
   pr=proof_cache[s['id']]
   if not pr:continue
   if s['id'] not in candidates:candidates[s['id']]=dict(sentence=copy.deepcopy(s),proof=pr,words={},reading=True,reading_subtype=ul[uid]['subtype'],unit_locator=ul[uid]['locator'])
   candidates[s['id']]['words'][word]=dict(form=o.get('source_form',o['form']),pos=o['pos'])
 covered=set().union(*(set(c['words']) for c in candidates.values())) if candidates else set()
 # Greedy sharing keeps the number of independently translated sentences modest;
 # one real sentence may illustrate several different headwords.
 selected={};assigned={};remaining=target_words&covered
 while remaining:
  scored=[]
  for sid,c in candidates.items():
   keys=set(c['words'])&remaining
   if not keys:continue
   recent=any(z['session']>='2024-01' for z in c['sentence']['sources']);length=len(tokens(c['sentence']['text']))
   score=len(keys)/(1+max(0,length-22)*.025)*(1.08 if recent else 1)
   scored.append((score,-length,sid,keys))
  _,_,sid,keys=max(scored);selected[sid]=candidates[sid]
  for word in keys:assigned[word]=sid
  remaining-=keys
 # Fall back to the earlier verified listening sentence only when a clean reading
 # sentence is unavailable. Every fallback is labelled in the final book/audit.
 oldmap={r['word']:r for r in core}
 generated_locations={(r['sentence'],r['source_key']):r for r in load('句子来源页码核对.json')}
 for word in sorted(target_words-set(assigned)):
  if word in oldmap:
   e=copy.deepcopy(oldmap[word]['example'])
   if word=='shark':
    e.update(copy.deepcopy(sl['S010941']));o=next(o for o in W[word]['occurrences'] if o['sentence']=='S010941');e.update(pos=o['pos'],form=o['form']);src=e['sources'][0];e['paragraph_source']=generated_locations['S010941',src['file']+'#'+src['locator']]
   sid=e['id'];pr=dict(source=e['sources'][0],page_start=e['paragraph_source']['page'],page_end=e['paragraph_source'].get('end_page',e['paragraph_source']['page']),verification='沿用已核对补充原文页',method='补充原文',generated=e['paragraph_source'])
   if sid not in selected:selected[sid]=dict(sentence=e,proof=pr,words={},reading=False)
   selected[sid]['words'][word]=dict(form=e['form'],pos=e['pos']);assigned[word]=sid
  else:
   # A newly ranked frequent word must be backed by a clean original reading sentence.
   possible=[]
   for o in reading[word]['occurrences']:
    s=sl[o['sentence']]
    if s['id'] not in BAD_EXAMPLES and 5<=len(tokens(s['text']))<=65 and re.match('[A-Z]',s['text']) and re.search(r'[.!?]$',s['text']) and not re.search('\\bfbr\\b|\\^',s['text']):
     pr=proof(s)
     if pr:possible.append((len(tokens(s['text'])),s,o,pr))
   assert possible,('no reading example',word)
   _,s,o,pr=min(possible,key=lambda x:x[0]);sid=s['id']
   selected.setdefault(sid,dict(sentence=copy.deepcopy(s),proof=pr,words={},reading=True,reading_subtype=ul[o['unit']]['subtype'],unit_locator=ul[o['unit']]['locator']))
   selected[sid]['words'][word]=dict(form=o.get('source_form',o['form']),pos=o['pos']);assigned[word]=sid
 phrase_assign={}
 for p in phrases:
  pattern=re.compile(r'(?<![A-Za-z])'+r'\s+'.join(re.escape(t) for t in p['phrase'].split())+r'(?![A-Za-z])',re.I)
  found=[(sid,c) for sid,c in selected.items() if pattern.search(c['sentence']['text'])]
  if not found:
   # Keep the existing short phrase example, but translate only its exact sentence.
   e=copy.deepcopy(p['example']);sid=e['id']
   if sid not in selected:selected[sid]=dict(sentence=e,proof=None,words={},reading=False)
  else:sid=min(found,key=lambda a:(not a[1]['reading'],len(a[1]['sentence']['text'])))[0]
  phrase_assign[p['phrase']]=sid
 for sid,c in selected.items():c['phrases']=[p for p,s in phrase_assign.items() if s==sid]
 save('阅读优先例句待译.json',selected);save('阅读优先配句映射.json',dict(words=assigned,phrases=phrase_assign))
 existing=load('阅读优先例句译文.json') if (D/'阅读优先例句译文.json').exists() else {}
 for path in sorted(D.glob('oct27_translations_*.tsv')):
  for line in path.read_text(encoding='utf8').splitlines():
   if not line.strip():continue
   sid,zh=line.split('\t',1);existing[sid]=dict(zh=zh,origin='整理者参考译文；不是官方译文',review='依据对应英文句子编写或校订')
 existing={sid:z for sid,z in existing.items() if sid in selected}
 auto=[]
 for sid,c in selected.items():
  if sid in existing:continue
  e=c['sentence']
  if c['reading'] or not e.get('paragraph_en') or not e.get('paragraph_zh'):continue
  en=e['paragraph_en'];zh=re.sub(r'^[WM男女]：[ \s]*','',e['paragraph_zh']).strip()
  ep=re.split(r'(?<=[.!?])\s+(?=[A-Z"\u201c])',en)
  zp=[z.strip() for z in re.findall(r'[^。！？]+[。！？]?',zh) if z.strip()]
  if len(ep)==1 and normal(en)==normal(e['text']):
   existing[sid]=dict(zh=zh,origin='第三方参考译文：原段本身为单句',review='沿用原来源单句译文');auto.append((sid,e['text'],zh))
  elif len(ep)==len(zp) and not re.search(r'\b(?:Dr|Mr|Mrs|Prof|St)\.|[A-Z]\.[A-Z]',en):
   ix=next((i for i,t in enumerate(ep) if normal(t)==normal(e['text'])),None)
   if ix is not None:
    existing[sid]=dict(zh=zp[ix],origin='第三方参考译文：等句数分句对齐',review='需逐句语义复核');auto.append((sid,e['text'],zp[ix]))
 save('阅读优先例句译文.json',existing)
 (D/'等句数对齐待校对.txt').write_text('\n'.join(a+' | '+b+' | '+c for a,b,c in auto),encoding='utf8')
 summary=dict(date='2026-10-27',reading_units=len(bodies),duplicate_body_units=len(duplicate_units),sessions=sorted({s['session'] for u in bodies.values() for s in u['sources']}),selected_reading_words=500,overlap_with_core1500=len(set(ranked)&set(oldmap)),core_reading_examples=sum(selected[assigned[r['word']]]['reading'] for r in core),core_fallback_examples=sum(not selected[assigned[r['word']]]['reading'] for r in core),unique_sentences=len(selected),word_targets=len(target_words),phrase_targets=100,scope='仅阅读正文；排除题干选项解析；选词填空保留原空缺；同考次重复长材料按整单元合并')
 save('2026-10-27选词配句概况.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2));print('TOP500',', '.join(ranked[:50]))
 todo=[(sid,c) for sid,c in selected.items() if sid not in existing];print('TRANSLATION_AUTO',len(auto),'MANUAL_TODO',len(todo))
 for start in range(0,len(todo),60):
  block=todo[start:start+60];(D/f'待译句子_{start//60+1:02}.txt').write_text('\n'.join(sid+' | '+c['sentence']['text'] for sid,c in block),encoding='utf8')
if __name__=='__main__':main()
