"""Fetch pronunciation references and prepare traceable bilingual candidates."""
import sys,json,re,csv,collections,urllib.request,hashlib,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'六级备考成果'/'数据'
sys.path.insert(0,str(D/'python_libs'));sys.stdout.reconfigure(encoding='utf-8')
def load(n):return json.loads((D/n).read_text(encoding='utf-8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def prepare():
 pd=D/'pronunciation';pd.mkdir(exist_ok=True)
 for name in ['data/en_UK.txt','data/en_US.txt','LICENSE','README.md']:
  target=pd/Path(name).name
  if not target.exists():
   url='https://raw.githubusercontent.com/open-dict-data/ipa-dict/master/'+name
   with urllib.request.urlopen(url,timeout=90) as r:target.write_bytes(r.read())
  print('PRONUNCIATION',target.name,target.stat().st_size,flush=True)
 ipa={}
 for lang in ['UK','US']:
  ipa[lang]={}
  for line in (pd/f'en_{lang}.txt').read_text(encoding='utf-8').splitlines():
   if '\t' in line:
    a,b=line.split('\t',1);ipa[lang][a.lower()]=b
 W=load('word_statistics.json');S=load('sentences.json');U=load('corpus_units.json');UL={u['id']:u for u in U};SL={s['id']:s for s in S}
 old=load('core_words_original500.json') if (D/'core_words_original500.json').exists() else load('core_words_with_source_pages.json');oldwords={x['word'] for x in old}
 save('core_words_original500.json',old) if not (D/'core_words_original500.json').exists() else None
 dic={}
 with (D/'ecdict.csv').open(encoding='utf-8',newline='') as f:
  for r in csv.DictReader(f):
   if r['word'].isalpha() and r['word'].islower():dic[r['word']]=r
 stop=set()
 for n in ast.parse((ROOT/'六级备考成果/脚本/build_learning.py').read_text(encoding='utf-8')).body:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['STOP','BAD'] for t in n.targets):stop.update(n.value.args[0].func.value.value.split())
  if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='STOP' and n.value.func.attr=='update':stop.update(n.value.args[0].func.value.value.split())
 stop.update('specie felt fell york america american british canadian chinese london china english thousand million completely highly mainly typically actually necessarily extremely positively consistently specifically literally physically regularly frequently hardly nearly probably possibly eventually currently previously simply entirely generally directly indirectly greatly particularly increasingly necessarily appropriately comparatively recently shop size ready list type moment room rest main total spot mistake voice real become got name yorker remark today tomorrow yesterday fifth sixth twice twenty thirty forty fifty anyone anybody somebody something everything anything towards center email website online grandma grandfather grandmother mum mom daddy professor television video mobile internet'.split())
 ps={(r['sentence'],r['source_key']):r for r in load('句子来源页码核对.json')}
 def example(k):
  candidates=[]
  for o in W[k]['occurrences']:
   s=SL[o['sentence']]
   if s['category']!='听力原文' or not s.get('zh'):continue
   u=UL[s['unit']];source=s['sources'][0]
   pair=next((b for b in u.get('bilingual',[]) if b['source']['file']==source['file'] and b['source']['locator']==source['locator']),None)
   if not pair:continue
   en=pair['en'];zh=pair['zh'];tokens=re.findall('[A-Za-z]+',en)
   if not 6<=len(tokens)<=240 or len(zh)>800:continue
   if re.search('[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]',en):continue
   if re.search('[À-ÖØ-öø-ÿ]',en):continue
   source=s['sources'][0];loc=ps.get((s['id'],source['file']+'#'+source['locator']))
   if not loc or not loc.get('sentence_page_verified'):continue
   score=10*(source['session']>='2024-01')-abs(len(tokens)-26)*.25-len(zh)*.008
   candidates.append((score,dict(s,form=o['form'],pos=o['pos'],paragraph_en=en,paragraph_zh=zh,paragraph_source=loc)))
  return max(candidates,key=lambda x:x[0])[1] if candidates else None
 stop.update('john peter pizza chocolate orange supermarket homework snack bacon steak dessert idiot math laptop rent chat borrow loud sunlight weekly indoor workday menu cooking eating driving functioning shared preferred mixed prescribed prepared understood found loved worried frozen hidden limited desired excited faster bent varied burning developed advanced assistant speaker learner interviewer grandfather'.split())
 # The available aligned example uses Frank only as a person's name.
 stop.add('frank')
 # Regular adverbs and inflected forms belong in the family panel rather than
 # artificially increasing the count of new headwords.
 adverb_keep=set('seemingly inevitably nonetheless notwithstanding nevertheless consequently simultaneously initially inherently exclusively arguably'.split())
 rows=[]
 for k,v in W.items():
  if k in oldwords|stop or not k.isalpha() or len(k)<4 or v['exam_coverage']<2 or k not in dic or not ipa['UK'].get(k):continue
  d=dic[k]
  if re.search(r'(?:^|/)0:',d['exchange']):continue
  if k.endswith('ly') and k not in adverb_keep and (k[:-2] in W or k[:-3]+'y' in W or k[:-1]+'e' in W):continue
  if re.search(r'(?:男名|女名|男子名|女子名|姓氏|人名)',d['translation']) and not re.search(r'\\n(?:v|a|adj)\.',d['translation']):continue
  if k=='behaviour' and 'behavior' in oldwords:continue
  e=example(k)
  if not e:continue
  tag=d['tag'].split();freq=int(d['frq'] or 0)
  level=3 if 'cet6' in tag and 'cet4' not in tag else 2 if 'gre' in tag and 'gk' not in tag and 'cet4' not in tag else 1 if freq>2500 or ('gre' in tag and 'gk' not in tag) else 0
  score=(level,v['exam_coverage'],v['exam_recent'],v['exam_count'])
  rows.append(dict(word=k,score=score,example=e,meaning=v['meaning'],tag=d['tag']))
 rows.sort(key=lambda x:x['score'],reverse=True);new=rows[:1000];assert len(new)==1000
 result=[]
 for i,r in enumerate(new+old,1):
  k=r['word'];e=r['example'] if i<=1000 else example(k)
  if not e:raise ValueError('Missing bilingual example '+k)
  result.append(dict(rank=i,word=k,tier='进阶突破' if i<=1000 else '熟词深化',meaning=r['meaning'],example=e,statistics={a:W[k][a] for a in ['exam_count','exam_coverage','exam_recent','exam_sessions','categories','forms','reference_count']},ipa_uk=ipa['UK'].get(k,''),ipa_us=ipa['US'].get(k,''),dictionary=dic.get(k,{})))
 save('vocabulary_revision_candidates.json',result)
 save('vocabulary_revision_dictionary.json',{k:v for k,v in dic.items() if k in W or k in ipa['UK']})
 print('SELECTED',len(result),'UNIQUE',len({r['word'] for r in result}),'UK_MISSING',[r['word'] for r in result if not r['ipa_uk']],flush=True)
 print('FIRST_120',', '.join(r['word'] for r in result[:120]),flush=True)
 print('LONGEST_PARAGRAPH',max(len(r['example']['paragraph_en']) for r in result))
if __name__=='__main__':prepare()
