import sys, urllib.request, re, json, hashlib, time
from pathlib import Path
from html import unescape
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'补充资料_2026年6月'
DATA=ROOT/'六级备考成果'/'数据'
OUT.mkdir(exist_ok=True); DATA.mkdir(exist_ok=True)
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=90) as r: return r.read()
manifest=[]
for n in (1,2,3):
    url=f'https://english-exam.lazynote.cn/cet6/paper/2026-06-{n}/'
    body=fetch(url); (OUT/f'2026-06-{n}_来源网页.html').write_bytes(body)
    text=body.decode('utf-8')
    links=list(dict.fromkeys(unescape(u) for u in re.findall(r'href=[\"\x27]([^\"\x27]+\.pdf)[\"\x27]',text)))
    links=[u for u in links if f'/2026-06-{n}/' in u]
    for u in links:
        kind='解析' if '%E8%A7%A3' in u.upper() or '解析' in u or '%E7%AD%94' in u.upper() else '真题'
        name=f'2026年06月六级{kind}第{n}套_懒笔记整理版.pdf'
        target=OUT/name
        try:
            if not target.exists():
                payload=fetch(u)
                if not payload.startswith(b'%PDF'): raise ValueError('Not a PDF')
                target.write_bytes(payload)
            payload=target.read_bytes()
            manifest.append({'file':str(target.relative_to(ROOT)),'url':u,'page_url':url,'sha256':hashlib.sha256(payload).hexdigest(),'source_type':'第三方整理版'})
            print(name,len(payload),flush=True)
        except Exception as e: print('DOWNLOAD_ERROR',u,str(e),flush=True)
    media=list(dict.fromkeys(unescape(u) for u in re.findall(r'[\"\x27]((?:https?:)?//[^\"\x27<> ]+\.(?:mp3|m4a)(?:\?[^\"\x27<> ]*)?)[\"\x27]',text)))
    print('MEDIA',n,media,flush=True)
    (DATA/f'media_links_{n}.json').write_text(json.dumps(media,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest.append({'file':str((OUT/f'2026-06-{n}_来源网页.html').relative_to(ROOT)),'url':url,'source_type':'第三方整理版'})
(DATA/'补充资料来源.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
dictionary=DATA/'ecdict.csv'
if not dictionary.exists():
    print('Downloading ECDICT',flush=True)
    dictionary.write_bytes(fetch('https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv'))
print('Dictionary bytes',dictionary.stat().st_size,flush=True)
