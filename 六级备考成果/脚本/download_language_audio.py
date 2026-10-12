import sys,re,json,urllib.request,html,zipfile,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'六级备考成果'/'数据'; OUT=ROOT/'补充资料_2026年6月'
sys.path.insert(0,str(DATA/'python_libs'));sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=90) as r:return r.read()
NLP=DATA/'nltk_data';NLP.mkdir(exist_ok=True)
for category,name in [('corpora','wordnet'),('taggers','averaged_perceptron_tagger_eng'),('tokenizers','punkt_tab')]:
    target=NLP/category;target.mkdir(exist_ok=True)
    z=target/f'{name}.zip'
    if not z.exists():z.write_bytes(fetch(f'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/{category}/{name}.zip'))
    if not (target/name).exists():zipfile.ZipFile(z).extractall(target)
    print('NLP',name,flush=True)
manifest=[]
for n in [1,2]:
    url=f'https://english-exam.lazynote.cn/cet6/sections/listening/2026-06-{n}/'
    page=fetch(url);(OUT/f'2026-06-{n}_听力解析.html').write_bytes(page)
    soup=BeautifulSoup(page,'html.parser')
    print('LISTENING',n,len(soup.get_text()),flush=True)
    whole=html.unescape((OUT/f'2026-06-{n}_来源网页.html').read_text(encoding='utf-8'))
    media=list(dict.fromkeys(re.findall(r'https://listening[^\s\"<>]+\.m3u8',whole)))
    for src in media:
        audiodir=OUT/f'听力第{n}套';audiodir.mkdir(exist_ok=True)
        playlist=fetch(src).decode('utf-8')
        if '#EXT-X-KEY' in playlist:
            print('ENCRYPTED_PLAYLIST: using online link only',flush=True);continue
        if '#EXT-X-STREAM-INF' in playlist:
            link=next(s for s in playlist.splitlines() if s and not s.startswith('#'))
            src=urllib.parse.urljoin(src,link);playlist=fetch(src).decode('utf-8')
        lines=[];k=0
        for line in playlist.splitlines():
            if line and not line.startswith('#'):
                k+=1;segurl=urllib.parse.urljoin(src,line);filename=f'{k:04d}'+Path(line.split('?')[0]).suffix
                target=audiodir/filename
                if not target.exists():target.write_bytes(fetch(segurl))
                lines.append(filename)
            else:lines.append(line)
        (audiodir/'index.m3u8').write_text('\n'.join(lines),encoding='utf-8')
        manifest.append({'suite':n,'source':src,'local_playlist':str((audiodir/'index.m3u8').relative_to(ROOT)),'segments':k,'online':url})
        print('AUDIO',n,k,'segments',flush=True)
(DATA/'音频补充清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
