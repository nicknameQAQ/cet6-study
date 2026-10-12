import sys,json,re,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'六级备考成果'/'数据';sys.stdout.reconfigure(encoding='utf-8')
def load(n):return json.loads((D/n).read_text(encoding='utf-8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
sentences=load('sentences.json');sl={s['id']:s for s in sentences}
bad=[s for s in sentences if re.search('[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u0100-\u017f]',s['text'])]
badids={s['id'] for s in bad}
save('待核对残缺原句.json',[dict(s,reason='原文含编码控制符或异常字形；暂不计入可靠词频，保留原句和出处') for s in bad])
words=load('word_statistics.json');removed=0
for word,v in list(words.items()):
 kept=[o for o in v['occurrences'] if o['sentence'] not in badids];removed+=len(v['occurrences'])-len(kept)
 if not kept:del words[word];continue
 v['occurrences']=kept;v['count']=len(kept);v['forms']=dict(collections.Counter(o['form'] for o in kept));v['categories']=dict(collections.Counter(sl[o['sentence']]['category'] for o in kept));v['sessions']=sorted({sr['session'] for o in kept for sr in o['sources']});v['coverage']=len(v['sessions']);v['recent']=sum(any(sr['session']>='2024-01' for sr in o['sources']) for o in kept)
 exam=[o for o in kept if sl[o['sentence']]['category'] not in ['作文范文','翻译参考译文']];v['exam_count']=len(exam);v['reference_count']=len(kept)-len(exam);v['exam_sessions']=sorted({sr['session'] for o in exam for sr in o['sources']});v['exam_coverage']=len(v['exam_sessions']);v['exam_recent']=sum(any(sr['session']>='2024-01' for sr in o['sources']) for o in exam)
for s in bad:s['quality']='excluded_encoding';s['lemmata']=[]
save('word_statistics.json',words);save('sentences.json',sentences)
summary=load('corpus_summary.json');summary.update(valid_lemmas=len(words),tokens=sum(v['count'] for v in words.values()),quarantined_sentences=len(bad),quarantined_tokens=removed);save('corpus_summary.json',summary)
print('QUARANTINE',len(bad),'sentences',removed,'tokens','valid lemmas',len(words),flush=True)
