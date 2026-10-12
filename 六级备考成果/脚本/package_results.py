import sys,json,zipfile,hashlib,csv,collections,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'六级备考成果';D=R/'数据'
sys.stdout.reconfigure(encoding='utf-8')
def load(n):return json.loads((D/n).read_text(encoding='utf-8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
manifest=load('pdf_manifest.json');qa=load('验收报告.json')
assert not qa['page_errors'] and not qa['glyph_errors'] and not qa['link_errors']
if qa.get('vocabulary_revision'):
 assert not qa['vocabulary_revision']['source_errors']
 assert qa['vocabulary_revision']['visual_review']=='passed'
checked={r['file']:r for r in qa['pdf_checks']}
for m in manifest:
 path=ROOT/m['file'];assert checked[m['file']]['sha256']==hashlib.sha256(path.read_bytes()).hexdigest(),m['file']
if qa.get('vocabulary_revision'):
 archived=R/'历史版本/1500词修订前';archived.mkdir(parents=True,exist_ok=True)
 for name in ['六级平板日常学习包.zip','六级平板完整资料包.zip','六级统计数据与复算脚本.zip']:
  old=R/name
  if old.exists() and not (archived/name).exists():shutil.copy2(old,archived/name)
supplement=[];seen=set()
for row in load('补充资料来源.json'):
 if row['file'] in seen:continue
 seen.add(row['file']);supplement.append(row)
save('补充资料来源.json',supplement)
sources=load('句子来源页码核对.json');sourcepages={(x['sentence'],x['source_key']):x for x in sources};sents=load('sentences.json');sl={s['id']:s for s in sents};words=load('word_statistics.json')
with (D/'全部词形与出处.csv').open('w',encoding='utf-8-sig',newline='') as f:
 wr=csv.writer(f);wr.writerow(['词条','原始词形','原句中的词形','词性标签','句子ID','原句词位从0起','来源类别','考次','套号','原始文件','原始PDF页码','材料页范围','题号或段落','补充PDF','补充PDF页码','原句','段落参考译文'])
 for lemma,v in words.items():
  for o in v['occurrences']:
   s=sl[o['sentence']]
   for z in o['sources']:
    source=sourcepages.get((s['id'],z['file']+'#'+z['locator']),{})
    wr.writerow([lemma,o['form'],o.get('source_form',o['form']),o['pos'],s['id'],o['position'],s['category'],z['session'],z['suite'],z['file'],z.get('page'),','.join(map(str,z.get('page_range',[]))),z['locator'],source.get('file',''),source.get('page',''),s['text'],s.get('zh','')])
readme='''六级平板学习资料 使用说明

从00_使用指南与备考安排.pdf开始阅读。
日常使用01核心词汇、02短语、03听力阅读、04写作翻译。
05完整索引用于查词和核对全部出处，不需要从头背完。
来源补充册提供听力段落原文、中文解释及第三方参考表达。

本次统计读取2021至2026年6月共70份六级PDF。
包含39道作文题、39道翻译原题、23套独立听力材料。
可靠词条9153个；核心词汇已扩为1500个主词条，另有100短语、118项中文概念统计及40个句式。
核心词汇共15卷，每卷100词；前10卷是新增词，后5卷是原500词深化。
主词均有英音、原句语境和对应译文、词频与出处；另列近义辨析、形近词及派生拓展。
无合适单词近义词的术语使用明确标注的释义转述，不当作原位替换词。
近义、形近和词族扩展不计入1500个主词条，也不增加真题频次。
指南含1500词跨卷索引；跨文件跳转需要阅读器支持并保留同目录文件名。
编码残缺的15条原句暂不计入可靠词频，原文与出处留在待核对清单。

写作与翻译专项册已更新为主题对照版：
39篇作文范文中英段落对照，39道翻译原文与参考英译对照。
按8个作文主题及11个翻译主题，列出415条主题词汇与短语条目。
词库区分原文表达与同主题迁移表达；不同主题有复用，不代表415个互不重复的词条。
40个句式和20句中译英练习及独立答案页仍保留。
新增100组写作替换指导（60组单词、40组短语）和32道练习及集中答案。
按8个作文主题组织，逐组说明意义、程度、搭配与结构变化；新例句均标为自编练习。
原118项中文概念统计可在统计数据包的translation_concepts.json中查阅。

2026年6月补充文件：三套真题、三套第三方解析、两套MP3。
补充版保留来源标记；不同出版者的套号可能不同，请按题目内容核对。
听力第1套约24分56秒，第2套约26分27秒，已核对格式和文件差异。

PDF页码指文件中的物理页码。完整索引的F代码见使用指南末尾。
资料可在平板中搜索、使用书签跳转并批注。建议保持PDF文件放在同一文件夹。
统计数据和复算脚本另保存在当前工作文件夹，原始试卷保持不变。
'''
(R/'使用说明.txt').write_text(readme,encoding='utf-8-sig')
daily=[m for m in manifest if m['kind'] in ['core','phrases','guide','listening_reading','writing_translation']]
def archive(name,items):
 target=R/name
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for path,arc in items:z.write(path,arc)
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
 print('PACKAGE',target.name,round(target.stat().st_size/1048576,2),'MB',len(items),'files',flush=True)
 return {'file':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
daily_items=[(ROOT/m['file'],Path(m['file']).name) for m in daily]+[(R/'使用说明.txt','使用说明.txt')]
dailyzip=archive('六级平板日常学习包.zip',daily_items)
full_items=[(ROOT/m['file'],'学习资料/'+Path(m['file']).name) for m in manifest]
for p in sorted((ROOT/'补充资料_2026年6月').glob('*.pdf')):full_items.append((p,'2026年6月试卷与听力/'+p.name))
for p in sorted((ROOT/'补充资料_2026年6月').glob('*.mp3')):full_items.append((p,'2026年6月试卷与听力/'+p.name))
full_items.extend([(R/'使用说明.txt','使用说明.txt'),(D/'补充资料来源.json','来源与验收/补充资料来源.json'),(D/'验收报告.json','来源与验收/验收报告.json')])
fullzip=archive('六级平板完整资料包.zip',full_items)
data_names=['word_statistics.json','sentences.json','corpus_units.json','corpus_summary.json','全部词形与出处.csv','资料清单.json','资料覆盖与缺项.json','套号与文字校对记录.json','原始PDF句级位置核对.json','句子来源页码核对.json','补充原文PDF页码.json','source_id_catalogue.json','待核对词形.json','待核对残缺原句.json','阅读文字双源校对记录.json','derived_word_families.json','translation_concepts.json','translation_originals.json','writing_analysis.json','writing_theme_statistics.json','core_words_with_source_pages.json','phrase_statistics.json','sentence_structures.json','translation_practice.json','pdf_manifest.json','验收报告.json']
data_names += [n for n in ['writing_translation_topic_banks.json','写作翻译新版主题词汇.json','写作翻译新版对照核验.json'] if (D/n).exists()]
data_names += [n for n in ['core_words_original500.json','core_words_enriched1500.json','core_vocabulary_volume_index.json','vocabulary_revision_candidates.json','vocabulary_enrichment_audit.json','vocabulary_revision_pdf_manifest.json','1500词原文逐条核验.json','writing_replacement_guidance.json'] if (D/n).exists()]
data_items=[(D/n,'数据/'+n) for n in data_names]+[(p,'脚本/'+p.name) for p in sorted((R/'脚本').glob('*')) if p.is_file()]
data_items += [(p,'数据/pronunciation/'+p.name) for p in sorted((D/'pronunciation').glob('*')) if p.is_file()]

# Preserve the structured inputs required by the revised generators, including
# dictionary lookups and source HTML, instead of shipping scripts without inputs.
known={p.resolve() for p,_ in data_items}
for p in sorted(D.glob('*.json')):
 if p.name!='交付清单.json' and p.resolve() not in known:
  data_items.append((p,''));known.add(p.resolve())
data_items.append((D/'ecdict.csv',''))
language_files=[D/'nltk_data/corpora/wordnet.zip']
language_files+=list((D/'nltk_data/taggers/averaged_perceptron_tagger_eng').glob('*'))
language_files+=list((D/'nltk_data/tokenizers/punkt_tab/english').glob('*'))
language_files+=[D/'nltk_data/tokenizers/punkt_tab/README']
data_items += [(p,'') for p in language_files if p.is_file()]
data_items += [(p,'') for p in sorted((ROOT/'补充资料_2026年6月').rglob('*.html'))]
data_items=[(p,str(p.relative_to(ROOT)).replace('\\','/')) for p,_ in data_items]
data_items.append((R/'复算说明.md','复算说明.md'))
datazip=archive('六级统计数据与复算脚本.zip',data_items)
save('交付清单.json',{'daily':dailyzip,'full':fullzip,'data':datazip,'daily_pdf_count':len(daily),'all_pdf_count':len(manifest),'validation':'逐页自动检查及人工版面抽查通过；1500条双语例句文本与出处页比对通过','created_date':'2026-10-12'})
