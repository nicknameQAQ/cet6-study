import sys,json,time,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'六级备考成果'/'数据'
sys.path.insert(0,str(DATA/'ocr_libs'))
sys.stdout.reconfigure(encoding='utf-8')
from rapidocr_onnxruntime import RapidOCR
parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=0);parser.add_argument('--worker',type=int,default=0);parser.add_argument('--workers',type=int,default=1);args=parser.parse_args()
engine=RapidOCR(det_limit_side_len=960,rec_batch_num=32,intra_op_num_threads=2,inter_op_num_threads=1)
out=DATA/'ocr_rapid';out.mkdir(exist_ok=True)
jobs=json.loads((DATA/'ocr_jobs.json').read_text(encoding='utf-8'));done=0
for ji,job in enumerate(jobs):
 if ji%args.workers!=args.worker:continue
 p=out/f"{job['id']}.json"
 if p.exists():continue
 start=time.time();result,elapsed=engine(job['image'])
 lines=[{'box':b,'text':t,'confidence':float(c)} for b,t,c in (result or [])]
 lines.sort(key=lambda x:(round(min(y for _,y in x['box'])/12),min(xx for xx,_ in x['box'])))
 p.write_text(json.dumps({'id':job['id'],'engine':'RapidOCR PP-OCRv4','lines':lines,'text':'\n'.join(x['text'] for x in lines)},ensure_ascii=False),encoding='utf-8')
 done+=1
 if done%5==0 or args.limit:print('OCR',done,'seconds',round(time.time()-start,2),job['id'],flush=True)
 if args.limit and done>=args.limit:break
