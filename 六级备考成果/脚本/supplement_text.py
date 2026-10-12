import sys,urllib.request,json,re,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'六级备考成果'/'数据';OUT=ROOT/'补充资料_2026年6月'/'校对参考';OUT.mkdir(exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8')
tasks=[]
sessions=['2021-06','2021-12','2022-06','2022-09','2022-12','2023-03','2023-06','2023-12','2024-06','2024-12','2025-06','2025-12']
for session in sessions:
 for n in [1,2]:tasks.append((f'{session}-{n}_listening',f'https://english-exam.lazynote.cn/cet6/sections/listening/{session}-{n}/'))
for session in ['2024-06','2024-12','2025-06','2025-12','2026-06']:
 for n in [1,2,3]:
  for sec in ['part3-section-a','part3-section-b','part3-section-c','part3-section-c-2']:
   tasks.append((f'{session}-{n}_{sec}',f'https://english-exam.lazynote.cn/cet6/articles/{session}-{n}/{sec}/'))
for session in sessions+['2026-06']:
 for n in [1,2,3]:
  for sec in ['part1','part-iv']:
   tasks.append((f'{session}-{n}_{sec}',f'https://english-exam.lazynote.cn/cet6/sections/{session}-{n}/{sec}/'))
def worker(task):
 key,url=task;target=OUT/f'{key}.html'
 if target.exists():return {'key':key,'url':url,'file':str(target.relative_to(ROOT))}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45) as r:body=r.read()
  target.write_bytes(body)
  return {'key':key,'url':url,'file':str(target.relative_to(ROOT))}
 except Exception as e:return {'key':key,'url':url,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 results=[]
 for result in pool.map(worker,tasks):
  results.append(result);print('REF',result['key'],'OK' if 'file' in result else result['error'][:40],flush=True)
(DATA/'校对参考来源.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
