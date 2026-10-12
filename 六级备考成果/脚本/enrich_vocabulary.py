"""Build a reusable enrichment layer without changing the exam token counts."""
import sys,json,re,collections,math,ast,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'六级备考成果'/'数据'
sys.path.insert(0,str(D/'python_libs'));sys.stdout.reconfigure(encoding='utf-8')
import nltk
nltk.data.path.insert(0,str(D/'nltk_data'))
from nltk.corpus import wordnet as wn
from vocabulary_editorial import UK_OVERRIDES,HOMOGRAPHS,SOUND_NOTES,SYN_MAP,CONFUSION_GROUPS,FAMILIES,GLOSSES,SENSE_OVERRIDES,CONTEXT_OVERRIDES,POS_GLOSSES
from vocabulary_paraphrases import PARAPHRASES
def load(n):return json.loads((D/n).read_text(encoding='utf-8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def words(t):return re.findall('[a-z]+',t.lower())
def main():
 rows=load('vocabulary_revision_candidates.json');dictionary=load('vocabulary_revision_dictionary.json');W=load('word_statistics.json');SL={s['id']:s for s in load('sentences.json')}
 ipa={}
 for line in (D/'pronunciation/en_UK.txt').read_text(encoding='utf-8').splitlines():
  if '\t' in line:a,b=line.split('\t',1);ipa[a.lower()]=b
 ipa.update(UK_OVERRIDES)
 # Preserve the reference pronunciation; normalise only equivalent notational symbols.
 def ip(k,pos=''):
  v=HOMOGRAPHS.get(k,{}).get(pos[:1],ipa.get(k,''))
  return v.replace('ɹ','r').replace('ɐ','ə').replace('ɛ','e')
 def gloss(k,pos=None):
  p='a' if pos=='s' else pos
  if p in POS_GLOSSES.get(k,{}):return POS_GLOSSES[k][p]
  if k in GLOSSES:return GLOSSES[k]
  raw=dictionary.get(k,{}).get('translation','').replace('\\n','；')
  if not raw:return ''
  blocks=re.split(r'(?:^|；)\s*(n|v|vt|vi|a|adj|adv|prep|conj|pron|num)\.\s*',raw)
  if pos:
   allowed={'n':{'n'},'v':{'v','vt','vi'},'a':{'a','adj'},'s':{'a','adj'},'r':{'adv'}}.get(pos,{pos})
   selected=[blocks[i+1] for i in range(1,len(blocks)-1,2) if blocks[i] in allowed]
   if selected:raw='；'.join(selected)
  raw=re.split(r'\[|；\s*(?:n|v|vt|vi|a|adj|adv|prep|conj)\.',raw)[0]
  raw=re.sub(r'^(?:n|v|vt|vi|a|adj|adv|prep|conj|pron|num)\.\s*','',raw)
  return '；'.join(re.split('[,，；]',raw)[:3]).strip()[:55]
 def posname(p):return {'n':'n.','v':'v.','a':'adj.','s':'adj.','r':'adv.'}.get(p,p)
 def item(k,p=None):
  syn=wn.synsets(k)
  if p is None:
   raw=dictionary.get(k,{}).get('translation','')
   parts=re.findall(r'(?:^|\\n)(n|v|vt|vi|a|adj|adv|prep|conj|pron|num)\.\s*',raw)
   mapped=list(dict.fromkeys({'vt':'v','vi':'v','adj':'a','adv':'r'}.get(a,a) for a in parts))
   p=mapped[0] if mapped else (syn[0].pos() if syn else '')
   # A participle used as an adjective is not displayed as an uninflected verb.
   if 'a' in mapped and k.endswith(('ed','ing')):p='a'
  source='https://dictionary.cambridge.org/pronunciation/english/'+k if k in UK_OVERRIDES else 'https://github.com/open-dict-data/ipa-dict/blob/master/data/en_UK.txt'
  return dict(word=k,ipa_uk=ip(k,{'n':'N','v':'V','a':'J','s':'J','r':'R'}.get(p,'')),ipa_source=source,ipa_source_type='编辑补充英音；链接供词典复核' if k in UK_OVERRIDES else '公开英音词表',pos=posname(p),meaning=gloss(k,p),exam_count=W.get(k,{}).get('exam_count',0),in_main=k in mainwords)
 mainwords={r['word'] for r in rows}
 families=[g.split() for g in FAMILIES.splitlines() if g.strip()]
 shapes=[g.split() for g in CONFUSION_GROUPS.splitlines() if g.strip()]
 # Existing contextual definitions are retained and extended, not discarded.
 tree=ast.parse((ROOT/'六级备考成果/脚本/build_learning.py').read_text(encoding='utf-8'))
 selected=[n for n in tree.body if (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OVERRIDE' for t in n.targets)) or (isinstance(n,ast.FunctionDef) and n.name in ['meaning','contextual_meaning'])]
 ns={'words':W,'re':re,'collections':collections};exec(compile(ast.Module(body=selected,type_ignores=[]),'context_definitions','exec'),ns)
 # In-context semantic scoring: same POS, content-word overlap and supplied bilingual context.
 stop=set('the a an of to and in or on for by with from as is are be that this it one something someone person people have make do cause become state quality act action'.split())
 def sense(k,e):
  if k in SENSE_OVERRIDES:return wn.synset(SENSE_OVERRIDES[k])
  pos={'N':'n','V':'v','J':'a','R':'r'}.get(e['pos'][:1]);ss=wn.synsets(k,pos=pos) if pos else wn.synsets(k)
  if not ss:ss=wn.synsets(k)
  context=set(words(e['text']))-stop-{k,e['form'].lower()};zh=set(re.findall('[\u4e00-\u9fff]',e['paragraph_zh']))
  scored=[]
  for i,s in enumerate(ss):
   desc=set(words(s.definition()+' '+' '.join(s.examples())+' '+' '.join(s.lemma_names())))-stop-{k}
   overlap=len(context&desc)
   alternatives=[l.name().lower() for l in s.lemmas() if l.name().lower()!=k and l.name().isalpha()]
   ch=max([len(zh & set(gloss(a,s.pos()))) for a in alternatives] or [0])
   score=overlap*2.0+min(ch,5)*.30-i*.16
   # Explicitly reject biographical and taxonomic named-entity senses.
   if re.search(r'\b(?:United States|American|British|English) (?:writer|author|composer|poet|politician|scientist|actor)|\b\d{4}-\d{4}\b',s.definition()):score-=100
   scored.append((score,s))
  return max(scored,key=lambda x:x[0])[1] if scored else None
 no_syn=[];no_fam=[];tag_cache={}
 for r in rows:
  k=r['word'];e=r['example'];context_pos=CONTEXT_OVERRIDES.get(k,(e['pos'],''))[0]
  r['context_pos']=context_pos
  semantic_example=dict(e,pos=context_pos);s=sense(k,semantic_example);r['sense_id']=s.name() if s else None;r['sense_definition']=s.definition() if s else ''
  r['meaning']=CONTEXT_OVERRIDES[k][1] if k in CONTEXT_OVERRIDES else POS_GLOSSES.get(k,{}).get({'N':'n','V':'v','J':'a','R':'r'}.get(context_pos[:1]),GLOSSES.get(k,ns['contextual_meaning'](k,e)))
  r['ipa_uk']=ip(k,context_pos);assert r['ipa_uk'],k
  r['ipa_source']='https://dictionary.cambridge.org/pronunciation/english/'+k if k in UK_OVERRIDES else 'https://github.com/open-dict-data/ipa-dict/blob/master/data/en_UK.txt'
  r['ipa_source_type']='编辑补充英音；链接供词典复核' if k in UK_OVERRIDES else '公开英音词表'
  r['sound_note']=SOUND_NOTES.get(k,'')
  if k in HOMOGRAPHS:r['sound_note']='；'.join({'N':'名词','V':'动词','J':'形容词','R':'副词'}[p]+' '+v for p,v in HOMOGRAPHS[k].items())+'。'+r['sound_note']
  r['synonyms']=[];r['synonym_note']='';r['substitution']=''
  if k in SYN_MAP:
   spec=SYN_MAP[k]
   for a in spec['words']:
    if ip(a) and gloss(a):r['synonyms'].append(item(a))
   r['synonym_note']=spec['note'];r['substitution']='按下列义项、词性与搭配条件判断；辨析中的其他义项不直接套入原句。'
   r['synonym_source']='编辑辨析；ECDICT与WordNet词义参照'
  elif s:
   alternatives=[l.name().lower() for l in s.lemmas() if l.name().lower()!=k and l.name().isalpha() and ip(l.name().lower()) and gloss(l.name().lower(),s.pos())]
   alternatives=[a for a in alternatives if a not in {'homo','fuck','shit','arse','damn','fag','nigger','nigga','bitch','bastard'}]
   alternatives.sort(key=lambda a:(W.get(a,{}).get('exam_coverage',0),W.get(a,{}).get('exam_count',0)),reverse=True)
   for a in list(dict.fromkeys(alternatives))[:2]:r['synonyms'].append(item(a,s.pos()))
   if r['synonyms']:
    r['synonym_note']='义项对照：'+s.definition()+'.'
    r['substitution']='本组供对应义项拓展，不作为原句逐词改写答案；使用时核对'+{'n':'可数性和介词搭配','v':'时态、语态及宾语结构','a':'修饰对象与语气程度','s':'修饰对象与语气程度','r':'修饰范围与程度'}.get(s.pos(),'词性和搭配')+'。'
    r['synonym_source']='Princeton WordNet 3.0 '+s.name()
  if not r['synonyms']:
   no_syn.append(k);r['synonym_note']='本条暂不列无条件互换词；用真题语境与中文义项建立理解。';r['substitution']='不建议为了换词直接改写原句。'
  r['paraphrase']=PARAPHRASES.get(k) if not r['synonyms'] else None
  r['confusables']=[]
  near=list(dict.fromkeys(a for group in shapes if k in group for a in group if a!=k))
  for a in near[:2]:
   if ip(a) and gloss(a):
    t=item(a);t['spelling_difference']=' / '.join(f'{k[i:j] or "∅"} → {a[u:v] or "∅"}' for op,i,j,u,v in difflib.SequenceMatcher(None,k,a).get_opcodes() if op!='equal');r['confusables'].append(t)
  r['families']=[];family=[]
  for group in families:
   if k in group:
    base=group[0]
    for a in group:
     if a==k:continue
     def derived(b,t):
      stems={b,b[:-1] if b.endswith('e') else b,b[:-1]+'i' if b.endswith('y') else b}
      if any(t==st+sf for st in stems for sf in ['ness','ly','er','or','ment','ation','ity','al','ful','less','ous','ive','able','ism','ist','ship']):return True
      return any(t==pr+b for pr in ['un','in','im','dis','mis','non','re'])
     if derived(k,a):relation='直接派生：'+k+' → '+a
     elif derived(a,k):relation='派生关系：'+a+' → '+k+'（此处列词基）'
     else:relation='同词族：'+base+'；不表示两词直接派生'
     family.append((a,relation))
  if s:
   for ss in wn.synsets(k):
    for l in ss.lemmas():
     if l.name().lower()!=k:continue
     for d in l.derivationally_related_forms():
      a=d.name().lower()
      # WordNet sometimes links conceptually related but etymologically distinct
      # forms: retain only transparent shared stems here.
      shared=0
      for ca,cb in zip(k,a):
       if ca!=cb:break
       shared+=1
      if a.isalpha() and shared>=min(4,len(k)-1) and a!=k:family.append((a,'WordNet派生关系'))
  seen=set();family.sort(key=lambda x:(x[1]!='WordNet派生关系',W.get(x[0],{}).get('exam_coverage',0)),reverse=True)
  for a,relation in family:
   if a in seen or not ip(a) or not gloss(a) or len(r['families'])>=3:continue
   seen.add(a);t=item(a);t['relation']=relation;r['families'].append(t)
  if not r['families']:no_fam.append(k)
  r['collocations']=[]
  for o in W[k]['occurrences']:
   z=SL[o['sentence']]
   if z['category'] in ['作文范文','翻译参考译文']:continue
   toks=re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*",z['text']);fm=o.get('source_form',o['form'])
   if z['id'] not in tag_cache:tag_cache[z['id']]=nltk.pos_tag(toks)
   tags=tag_cache[z['id']]
   for j,t in enumerate(toks):
    if t.lower()!=fm.lower():continue
    for a,b in [(j,min(j+2,len(toks))),(j,min(j+3,len(toks))),(max(0,j-1),j+1),(max(0,j-1),min(j+2,len(toks)))]:
     while b<len(toks) and tags[b-1][1].startswith('N') and tags[b][1].startswith('N') and b-a<5:b+=1
     group=toks[a:b]
     gt=[t[1] for t in tags[a:b]]
     if any(t.startswith('NNP') for t in gt):continue
     if len(group)<2 or not (gt[0].startswith(('N','J','V','R')) and gt[-1].startswith(('N','J','V'))):continue
     if any(t.startswith(('PR','WP','CC','MD')) or t=='DT' for t in gt):continue
     if len(gt)==2 and not ((gt[0].startswith(('J','N')) and gt[1].startswith('N')) or (gt[0].startswith('R') and gt[1].startswith(('J','V'))) or (gt[0].startswith('V') and gt[1].startswith('N'))):continue
     if len(gt)==3 and not ((gt[1]=='IN' and gt[0].startswith(('V','N','J')) and gt[2].startswith('N')) or (gt[0].startswith('V') and gt[1].startswith('J') and gt[2].startswith('N')) or all(t.startswith(('J','N')) for t in gt)):continue
     if group[-1].lower() in stop or group[0].lower() in {'a','an','the','is','are','was','were','have','has','had','and','by','into'}:continue
     if gt[-1].startswith('N') and not wn.synsets(group[-1].lower(),pos='n'):continue
     if any("'" in t for t in group):continue
     phrase=' '.join(group)
     if len(phrase)<=52:r['collocations'].append({'phrase':phrase,'sentence_id':z['id'],'source':z['sources'][0]})
  cc=collections.Counter(t['phrase'].lower() for t in r['collocations'])
  unique={t['phrase'].lower():t for t in r['collocations']}
  r['collocations']=[unique[a] for a,n in cc.most_common(2)]
  if not r['collocations']:
   r['collocations']=[dict(phrase='见下方完整语境',sentence_id=e['id'],source=e['sources'][0],note='未单独截取固定搭配')]
  r.pop('dictionary',None)
  e['sources'][0]['generated_pdf']={key:e['paragraph_source'][key] for key in ['file','page','paragraph_start_page','sentence_page_verified'] if key in e['paragraph_source']}
  if r['rank']%250==0:print('ENRICH',r['rank'],flush=True)
 save('core_words_enriched1500.json',rows)
 save('core_words.json',rows);save('core_words_with_source_pages.json',rows)
 save('vocabulary_enrichment_audit.json',dict(main_words=len(rows),unique_main_words=len(mainwords),new_main_words=1000,existing_main_words=500,uk_ipa_complete=all(r['ipa_uk'] for r in rows),synonym_entries=sum(len(r['synonyms']) for r in rows),words_with_synonyms=sum(bool(r['synonyms']) for r in rows),words_with_paraphrases=sum(bool(r['paraphrase']) for r in rows),words_without_safe_synonym=no_syn,confusable_entries=sum(len(r['confusables']) for r in rows),family_entries=sum(len(r['families']) for r in rows),words_without_verified_family=no_fam,corpus_counts_unchanged=True))
 print('ENRICH DONE',len(rows),'NO_SYN',len(no_syn),'NO_FAMILY',len(no_fam),flush=True)
if __name__=='__main__':main()
