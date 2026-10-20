"""Record provenance without equating text matching with semantic correctness."""
import sys,json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'六级备考成果';D=R/'数据'
sys.path.insert(0,str(D/'python_libs'))
from bs4 import BeautifulSoup
import pymupdf as fitz

def load(n):return json.loads((D/n).read_text(encoding='utf8'))
def normal(t):return re.sub('[^a-z0-9\u4e00-\u9fff]','',t.lower())

def build_audit():
 records=[];cache={}
 for section,name in [('writing','writing_analysis.json'),('translation','translation_originals.json')]:
  for p in load(name):
   f=ROOT/p['web_source'];html=BeautifulSoup(f.read_text(encoding='utf8'),'html.parser');canonical=html.select_one('link[rel=canonical]')
   source=p['source'];path=ROOT/source['file']
   if str(path) not in cache:
    with fitz.open(path) as pdf:cache[str(path)]=[q.get_text() for q in pdf]
   original=cache[str(path)][source['page']-1];prompt=p['prompt'] if section=='writing' else p['zh']
   url=canonical.get('href') if canonical else None
   assert url and url.startswith('https://english-exam.lazynote.cn/'),f
   content=html.select_one('#essay' if section=='writing' else '#translation .tp-para');assert content,f
   if section=='writing':assert html.select('#essay-zh .wp-trans__para'),f
   row=dict(id=p['session']+'-'+p['suite'],section=section,original_file=source['file'],original_page=source['page'],original_text_layer_match=normal(prompt) in normal(original),question_content_in_cached_page=normal(prompt) in normal(html.get_text(' ',strip=True)),reference_site='懒笔记',reference_url=url,reference_local_file=p['web_source'],reference_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),web_suite=p.get('web_suite',p['suite']),local_suite=p['suite'],source_title=html.title.get_text(' ',strip=True),reference_status='单一第三方参考，未完成独立逐题语义复核',official_answer=False)
   row['editorial_parts']=['题意中文翻译','主题标题与分类','主题表达及学习建议'] if section=='writing' else ['主题标题与分类','主题表达及学习建议']
   row['reference_parts']=['英文参考范文','范文中文参考译文'] if section=='writing' else ['整篇参考英译','来源页面的逐句参考英译']
   if not row['original_text_layer_match']:row['original_match_note']='本次PDF文字层未完整匹配；可能受OCR、图表或字符差异影响，本次未重做原卷OCR，不宣称独立核准。'
   records.append(row)
 assert len(records)==78
 result=dict(checked_on='2026-10-20',writing_references=39,translation_references=39,independent_reference_domains=1,semantic_independent_review_complete=False,records=records)
 (D/'写作翻译来源追溯.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 text=['# 范文、参考译文与分析的来源说明','',
 '检查日期：2026-10-20。39篇作文范文及中文参考译文、39道翻译的参考英译，均来自已缓存的懒笔记题型网页。原始试卷只有题目时，参考答案是从外部网页补充的，不能由题目本身推出唯一范文。',
 '', '这些网页属于单一第三方来源，不是官方标准答案，也没有完成逐题独立语义复核。网站是否使用AI撰写、是否经专业人员审定，现有缓存不能证实。主题标题、分类、题意中文翻译和部分学习表达由整理者编写，不应冒充原卷解析。',
 '', '此前“出处核对通过”是指选录文本与所用来源页的匹配，以及文件位置与排版检查；它不证明译文准确无误。新增加的替换例句、段落和练习均为自编材料，不计入真题频次。',
 '', '发现的具体问题：2025-12本地第1套对应网站第3套范文，英文“That experience taught me that challenges are conquered by those who keep improving.”的原参考中译末句写成“那段经历让我明白：挑战属于那些不断进步的人。”，语义不够准确。应理解为“那段经历让我明白：不断进步的人能够战胜挑战。”新版保留来源译文，同时加校订提示，避免把校订内容混称网站原文。',
 '', '## 每题来源', '', '| 本地考次套号 | 类型 | 原卷页码 | 网站套号 | 参考链接 | 状态 |', '|---|---|---|---|---|---|']
 for row in records:
  kind='写作' if row['section']=='writing' else '翻译';text.append(f"| {row['id']} | {kind} | {row['original_page']} | {row['web_suite']} | [懒笔记]({row['reference_url']}) | 单一第三方；非官方 |")
 text+=['','## 如何使用','', '先以原卷题干、Directions及给定首句为约束。第三方范文仅用于观察一种论证和表达；中文参考译文用于理解，但遇到不合语义的地方应回到英文核对。翻译练习遮住英译自己完成，再检查信息有无遗漏、主语关系、时态、数量和搭配；多个英语表达都可能成立。']
 (R/'范文译文与分析来源说明.md').write_text('\n'.join(text)+'\n',encoding='utf8')
 return {(r['section'],r['id']):r for r in records}

if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf8');a=build_audit();print('PROVENANCE',len(a),'records; PDF text-layer matches',sum(r['original_text_layer_match'] for r in a.values()),'; cached question matches',sum(r['question_content_in_cached_page'] for r in a.values()))
