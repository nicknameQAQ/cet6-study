import sys,json,re,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'六级备考成果'/'数据';sys.path.insert(0,str(D/'python_libs'));sys.stdout.reconfigure(encoding='utf-8')
from rapidfuzz.fuzz import partial_ratio
def load(n):return json.loads((D/n).read_text(encoding='utf-8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def letters(t):return re.sub('[^a-z]','',t.lower())
pages={(p['file'],p['page']):letters(p['text']) for p in load('pages_with_ocr.json')}
sentences=load('sentences.json');counts=collections.Counter();ledger=[]
for s in sentences:
 groups=collections.defaultdict(list);other=[]
 for src in s['sources']:
  if src.get('page'):groups[src['file']].append(src)
  else:other.append(src)
 updated=other[:];needle=letters(s['text'])
 for file,sources in groups.items():
  physical=sorted({x['page'] for x in sources})
  if len(physical)<2:updated.extend(sources);continue
  exact=[p for p in physical if needle in pages.get((file,p),'')]
  if exact:
   page=exact[0];chosen=dict(next(x for x in sources if x['page']==page));chosen['sentence_page_check']='exact';updated.append(chosen);counts['exact']+=1
  else:
   scored=[(partial_ratio(needle,pages.get((file,p),'')),p) for p in physical]
   score,page=max(scored)
   if score>=97 and len(needle)>=40:
    chosen=dict(next(x for x in sources if x['page']==page));chosen['sentence_page_check']='near-identical';chosen['page_match_score']=round(score,2);updated.append(chosen);counts['near-identical']+=1
   else:
    chosen=dict(sources[0]);chosen['page']=None;chosen['page_range']=physical;chosen['sentence_page_check']='material-page-range';updated.append(chosen);counts['page-range']+=1
  ledger.append({'sentence':s['id'],'file':file,'original_pages':physical,'resolved':[x.get('page') or x.get('page_range') for x in updated if x['file']==file]})
 s['sources']=updated
save('sentences.json',sentences);sl={s['id']:s for s in sentences}
words=load('word_statistics.json')
for v in words.values():
 for o in v['occurrences']:o['sources']=sl[o['sentence']]['sources']
save('word_statistics.json',words)
if (D/'read_examples.json').exists():
 examples=load('read_examples.json')
 for e in examples:e['sources']=sl[e['id']]['sources']
 save('read_examples.json',examples)
save('原始PDF句级位置核对.json',{'counts':dict(counts),'records':ledger,'note':'近似匹配仅校正文字符差异；无法确认到单页时明确列材料页范围，不重复算成多次出现。'})
print('SOURCE REFINEMENT',dict(counts),flush=True)
