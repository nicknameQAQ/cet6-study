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
if qa.get('oct20_revision'):
 assert not qa['oct20_revision']['errors']
 assert qa['oct20_revision']['visual_review']=='passed'
if qa.get('oct27_revision'):
 assert not qa['oct27_revision']['errors'] and not qa['oct27_revision']['source_errors']
 assert qa['oct27_revision']['visual_review']=='passed'
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

2026年10月20日更新：
06_核心词汇1500速记_仅单词与英音.pdf：30页，仅1500个主词与英音，顺序与15卷详解版一致。
07_写作同义替换独立扩充版.pdf：140组指导（80组词、60组短语）、64道练习、8个主题段落改写、16类常见误用。
04册已移出原替换附录，保留39篇作文、39道翻译对照、主题词库、40个句式与20道翻译练习。
原00册仍供训练安排参考；写作章节拆分后的最新位置以本说明为准。
范文、范文中译和翻译参考英译来自单一第三方“懒笔记”，未完成逐题独立语义复核，不能视作官方标准答案。
每题增加了参考来源；题意中文、分类和部分学习建议为整理者编写。
详见同包“范文译文与分析来源说明.md”，其中列出78条来源与一处已发现的中译校订提示。

从00_使用指南与备考安排.pdf开始阅读。
日常使用06速记筛词，01详解查漏，02短语、03听力阅读、04写作翻译、07替换训练。
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
原100组写作替换及32道练习已移至07册，并扩充为140组、64道。
07册按8个作文主题组织，逐组说明意义、程度、搭配与结构变化；新例句、段落和练习均标为自编材料。
原118项中文概念统计可在统计数据包的translation_concepts.json中查阅。

2026年6月补充文件：三套真题、三套第三方解析、两套MP3。
补充版保留来源标记；不同出版者的套号可能不同，请按题目内容核对。
听力第1套约24分56秒，第2套约26分27秒，已核对格式和文件差异。

PDF页码指文件中的物理页码。完整索引的F代码见使用指南末尾。
资料可在平板中搜索、使用书签跳转并批注。建议保持PDF文件放在同一文件夹。
统计数据和复算脚本另保存在当前工作文件夹，原始试卷保持不变。
'''
if qa.get('oct27_revision'):
 readme='''六级平板学习资料 使用说明 - 2026年10月30日

本次修改：
01核心1500：保持原词及顺序，1239词改配阅读正文句，261词保留注明来源的听力句。例句改为该句的中英对照。
02短语100条：展示对应英文句子及该句中文，去掉整段对照。
06核心1500速记：单词、英音、中文义，共63页，顺序与详解一致。
08阅读高频500：按阅读正文频次独立统计，五卷、每卷100词；每词有阅读原句、单句译文、音标、辨析与出处。
09阅读500速记：同样500词的单词、英音、中文义，共21页。
00指南：补充阅读500跨卷索引；07仍是独立写作同义替换指导。

阅读500允许与原1500重合，实际重合336词，共1664个不同主词，不是新增500个生词。高频榜含基础内容词，可快筛认识的词。
原1500的全题型频次不变；阅读500仅计阅读正文，排除题干、选项、解析、指令和参考范文，不补入选词填空答案。
旧统计将species误归入specie，本册已校正为species（物种）；旧总索引按specie定位，次数没有增加。

先用06或09筛出不会的词，再查同序详解；详解每10词一组，速记每页24词。
每天以90分钟为基准：词句15分钟、听力35分钟、阅读25分钟、写作或翻译15分钟。额外时间复练错题。
词义与译文为学习参考，原句文本核对不能代替语义审定。阅读中译主要由整理者逐句编写或校订，不是官方答案。
04册保留39篇作文、39道翻译双语对照和主题表达；07册为140组替换、64道练习、8篇主题改写、16类误用。
范文、范文中译、翻译参考英译来自单一第三方“懒笔记”，没有冒充官方答案或声称教师逐条审定。
具体见同包《阅读配句与词音义版说明.md》《范文译文与分析来源说明.md》。

完整包保留全部58份学习PDF、2026年6月三套试卷、三套第三方解析及两套MP3。
日常包供学习；05全部出处索引和来源补充册在完整包中。
跨文件跳转需要把PDF保留在同一文件夹，并使用支持跳转的阅读器；原卷按文件名和PDF物理页码查阅。
数据包新增阅读正文词频、500词全部出处CSV、799条单句译文、来源核验和展示校订记录；可继续添加试卷复算。
原始试卷不改动，已替换的生成资料归档到历史版本。
'''
(R/'使用说明.txt').write_text(readme,encoding='utf-8-sig')
daily=[m for m in manifest if m['kind'] in ['core','phrases','guide','listening_reading','writing_translation','quick_vocabulary','writing_replacements','reading_core','reading_quick']]
def archive(name,items):
 target=R/name
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for path,arc in items:z.write(path,arc)
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
 print('PACKAGE',target.name,round(target.stat().st_size/1048576,2),'MB',len(items),'files',flush=True)
 return {'file':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
daily_items=[(ROOT/m['file'],Path(m['file']).name) for m in daily]+[(R/'使用说明.txt','使用说明.txt')]
if (R/'范文译文与分析来源说明.md').exists():daily_items.append((R/'范文译文与分析来源说明.md','范文译文与分析来源说明.md'))
if (R/'阅读配句与词音义版说明.md').exists():daily_items.append((R/'阅读配句与词音义版说明.md','阅读配句与词音义版说明.md'))
dailyzip=archive('六级平板日常学习包.zip',daily_items)
full_items=[(ROOT/m['file'],'学习资料/'+Path(m['file']).name) for m in manifest]
for p in sorted((ROOT/'补充资料_2026年6月').glob('*.pdf')):full_items.append((p,'2026年6月试卷与听力/'+p.name))
for p in sorted((ROOT/'补充资料_2026年6月').glob('*.mp3')):full_items.append((p,'2026年6月试卷与听力/'+p.name))
full_items.extend([(R/'使用说明.txt','使用说明.txt'),(D/'补充资料来源.json','来源与验收/补充资料来源.json'),(D/'验收报告.json','来源与验收/验收报告.json')])
if (R/'范文译文与分析来源说明.md').exists():full_items.append((R/'范文译文与分析来源说明.md','范文译文与分析来源说明.md'))
if (D/'写作翻译来源追溯.json').exists():full_items.append((D/'写作翻译来源追溯.json','来源与验收/写作翻译来源追溯.json'))
if (R/'阅读配句与词音义版说明.md').exists():full_items.append((R/'阅读配句与词音义版说明.md','阅读配句与词音义版说明.md'))
fullzip=archive('六级平板完整资料包.zip',full_items)

updatezip=None
if qa.get('oct27_revision'):
 files=set(qa['oct27_revision']['files'])
 update_items=[(ROOT/m['file'],Path(m['file']).name) for m in manifest if m['file'] in files]
 update_items.extend([(R/'阅读配句与词音义版说明.md','阅读配句与词音义版说明.md'),(R/'使用说明.txt','使用说明.txt')])
 updatezip=archive('2026-10-30_阅读配句与词音义更新包.zip',update_items)
elif qa.get('oct20_revision'):
 update_items=[(ROOT/m['file'],Path(m['file']).name) for m in manifest if m['kind'] in ['writing_translation','quick_vocabulary','writing_replacements']]
 update_items.append((R/'范文译文与分析来源说明.md','范文译文与分析来源说明.md'))
 updatezip=archive('2026-10-20_速记与写作更新包.zip',update_items)
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
for p in [D/'阅读高频500全部出处.csv',R/'阅读配句与词音义版说明.md']:
 if p.exists():data_items.append((p,str(p.relative_to(ROOT)).replace('\\','/')))
if (R/'范文译文与分析来源说明.md').exists():data_items.append((R/'范文译文与分析来源说明.md','范文译文与分析来源说明.md'))
datazip=archive('六级统计数据与复算脚本.zip',data_items)
save('交付清单.json',{'daily':dailyzip,'full':fullzip,'data':datazip,'update':updatezip,'daily_pdf_count':len(daily),'all_pdf_count':len(manifest),'validation':'逐页自动检查及人工版面抽查通过；出处文本匹配不等于语义准确性审定','created_date':'2026-10-30' if qa.get('oct27_revision') else '2026-10-20'})
