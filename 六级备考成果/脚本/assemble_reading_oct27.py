"""Assemble sentence-only vocabulary, with independent reading counts.

Raw exam text and token counts are preserved; display OCR corrections and
editorial translations are separate, traceable fields.
"""
import sys,json,re,copy,ast,collections,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'六级备考成果';D=R/'数据'
sys.stdout.reconfigure(encoding='utf8')
def load(n):return json.loads((D/n).read_text(encoding='utf8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')

CORRECTIONS={
 'S001861':[('reporfs',"report's")], 'S004340':[('archacologists','archaeologists')],
 'S000997':[('a2014','a 2014')], 'S007588':[('·think','think'),('better-one','better - one')],
 'S001075':[('tourism Uncontrolled','tourism. Uncontrolled')],
 'S000754':[('light • caution','light - caution')], 'S000967':[('sk仆ls','skills')],
 'S004323':[('US S4 million','US $4 million')], 'S007581':[('( 6 )','')],
 'S001515':[('a ubeautifuF, campus','a "beautiful" campus')],
 'S002021':[('Cunently','Currently')], 'S000201':[('managers,M says','managers," says')],
 'S007250':[('( fftliJH1g)',''),('·regime','regime')], 'S004529':[('linguistie','linguistic')],
 'S004255':[('diferently','differently')], 'S008249':[('b/oc左','block')],
 'S007578':[('(:ic.fiq)',''),('and-later-pens','and - later - pens')],
 'S007747':[('j°:st','just'),('says·;','says;')], 'S001540':[('fbcus','focus')],
}
FIX={
 'compromise':'使受损；泄露（密码）','power':'力量；权力；电力','state':'国家；州；状态',
 'medium':'媒介；媒体（复数 media）','according':'根据（according to）',
 'ward':'抵御（ward off）','sensitivity':'体谅；审慎',
 'shark':'鲨鱼；比喻强硬竞争型的人','like':'像；例如',
}
FIX.update(dict(line.split('|',1) for line in '''bias|偏差；偏见
mechanism|机制；运作方式
extinction|灭绝
subtle|细微的；不易察觉的
meaningful|有意义的
nurture|后天培养；养育
expertise|专业知识；专长
layman|门外汉；非专业人士
trigger|触发；激活
disrupt|扰乱；打断
consensus|共识；一致意见
overwhelm|使不堪承受；压倒
comprehend|理解；领会
versus|与……相对；对抗
plague|困扰；使受折磨
causal|因果的
credential|资格证明；资历
stray|偏离；走失
dwarf|使相形见绌；远远超过
economically|在经济上；受经济因素影响地
formulate|制定；明确表述
assertive|坚定自信的；敢于表达的
recession|经济衰退
collaboration|合作
negligible|微不足道的；可忽略的
vicious|恶性的；恶毒的
renovation|翻修；整修
consultancy|咨询服务；咨询公司
ensue|接着发生；随后出现
spectacular|壮观的；引人注目的
ethical|符合道德的；道德方面的
haul|收获；所得
replacement|替代物；更换
affordable|负担得起的
viable|可行的；能持续发展的
oversee|监督；监管
tenure|任期；任职期
infection|感染；传染病
animation|动画制作；动画片
graphic|图像的；绘画的
counterproductive|适得其反的
multiple|多个的；多种的
highlight|突出；凸显
stem|起源于（stem from）
feature|特征；特点
instance|例子；情况
behave|行事；表现
recruit|招聘；招募
guideline|指导原则；准则
imagination|想象力；想象
sustain|维持；使持续
globe|地球；球体
anticipate|预期；预料
exhaust|尾气；耗尽；此处数据尾迹
widespread|广泛的；普遍的
evolve|演变；进化
supportive|给予支持的
sensible|明智的；合理的
dependent|依赖的
unrelated|不相关的
genetic|遗传的；基因的
secondary|次要的；中等教育的
royal|王室的；皇家的
dismiss|不予理会；驳回
leverage|利用；发挥……优势
instant|即时的；立即的
motherhood|为人母；母亲身份
implementation|实施；执行
worthy|值得的
micro|微小的；微型的
timber|木材
plain|明白地；仅此而已
data|数据；资料
online|在线的
fast|快的；快速的（fast food：快餐）
piece|拼合；拼接（piece together）
sound|听起来
close|弥合；缩小（差距）
play|起作用（play a role）
field|领域；场地；playing field 指竞争条件
form|形式
care|照料；关怀
figure|数字；比例
treat|奖励食物；款待
sustainable|可持续的
emission|排放；排放物
forest|森林
identity|身份；此处所发现事物的属性
key|关键；钥匙
account|考虑（take into account）
state|州
point|时刻；时间点
order|订单；命令；次序
grant|认为理所当然（take for granted）
disperse|分散；散开
automate|使自动化
notwithstanding|尽管
wish|希望；愿望
leave|离开；留下；休假
follow|跟随；遵循
halfway|在中途；半途的
stay|保持；停留
generally|通常；一般地
consumption|消费；消耗
trait|特征；特性
specie|物种（species，单复数同形）
housing|住房；住房供应
addition|增加；添加
school|学校
company|公司
child|孩子；儿童
people|人们；人民
student|学生
woman|女性；妇女
grow|增长；成长；种植
make|使；制造；做
take|采取；拿；花费
way|方式；方法；道路
life|生活；生命
need|需要；需求
get|得到；变得
help|帮助；有助于
place|地方；位置
good|好的；有益的
high|高的
great|很大的；伟大的
important|重要的
person|人；个人
less|更少；较少
long|长的；长久的
money|钱；资金
include|包括
large|大的；大量的
pay|工资；报酬
small|小的；少的
tax|税；税款
back|回；恢复原状
tree|树
crop|农作物
able|能够的
parent|父亲或母亲；家长
big|大的
art|艺术
set|设定；设置
screen|屏幕；银幕
really|确实；实际上
keep|保持；保留
business|商业；企业；业务
foreign|外国的
low|低的
water|水
course|课程；过程
bank|银行；河岸
gas|气体；天然气；汽油
standard|标准
friend|朋友
act|行动；表现
full|满的；完全的
early|早的；早期的
due|应有的；到期的；due to 因为
several|几个；若干
personality|个性；人格
advantage|优势；好处
game|游戏；比赛
private|私营的；私人的
principle|原则；原理
let|让；允许
spider|蜘蛛
name|名字；名称
statement|陈述；声明
countryside|乡村；农村
production|生产；制作
intelligence|智力；情报
worth|价值
'''.splitlines() if '|' in line))
POS_FIX=dict(line.split() for line in '''trigger VB
plague VB
causal JJ
dwarf VBZ
multiple JJ
stem VBZ
exhaust NN
dependent JJ
royal JJ
leverage VB
worthy JJ
fast JJ
play VBZ
forest NNS
help VB
according IN
'''.splitlines() if line.strip())

def archive():
 target=R/'历史版本/2026-10-27修订前';target.mkdir(parents=True,exist_ok=True)
 names=['core_words_enriched1500.json','core_words.json','core_words_with_source_pages.json','core_phrases.json','pdf_manifest.json','验收报告.json','vocabulary_revision_candidates.json']
 for p in [D/n for n in names]+list((R/'学习资料').glob('01_核心词汇1500_*.pdf'))+[R/'学习资料'/n for n in ['00_使用指南与备考安排.pdf','02_高频短语与复习.pdf','06_核心词汇1500速记_仅单词与英音.pdf']]+list(R.glob('*.zip'))+[R/'使用说明.txt']:
  if p.exists() and not (target/p.name).exists():shutil.copy2(p,target/p.name)
 # The manifest holds the authoritative phrase filename.
 for m in load('pdf_manifest.json'):
  if m['kind']=='phrases':
   p=ROOT/m['file']
   if not (target/p.name).exists():shutil.copy2(p,target/p.name)
 return target

def assemble():
 target=archive();core=json.loads((target/'core_words_enriched1500.json').read_text(encoding='utf8'))
 phrases=json.loads((target/'core_phrases.json').read_text(encoding='utf8'))
 chosen=load('阅读优先例句待译.json');mapping=load('阅读优先配句映射.json');trans=load('阅读优先例句译文.json');W=load('word_statistics.json')
 assert set(chosen)<=set(trans)
 locations={(r['sentence'],r['source_key']):r for r in load('句子来源页码核对.json')}
 tree=ast.parse((R/'脚本/build_learning.py').read_text(encoding='utf8'))
 selected=[n for n in tree.body if (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OVERRIDE' for t in n.targets)) or (isinstance(n,ast.FunctionDef) and n.name in ['meaning','contextual_meaning'])]
 ns={'words':W,'re':re,'collections':collections};exec(compile(ast.Module(body=selected,type_ignores=[]),'context_meaning','exec'),ns)
 rolekeys={k.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='role' for t in n.targets) for k in n.value.keys}
 from vocabulary_editorial import GLOSSES,POS_GLOSSES
 errata=[]
 def example(sid,word=None):
  c=chosen[sid];e=copy.deepcopy(c['sentence']);pr=c.get('proof');zh=trans[sid]
  if word:e.update(c['words'][word])
  display=e['text']
  applied=[]
  for a,b in CORRECTIONS.get(sid,[]):
   if a in display:display=display.replace(a,b);applied.append({'raw':a,'display':b})
  e.update(display_text=display,zh=zh['zh'],paragraph_en=e['text'],paragraph_zh=zh['zh'],sentence_only=True,reading_body=c['reading'],translation_provenance=zh,ocr_display_corrections=applied)
  if applied:errata.append(dict(sid=sid,corrections=applied))
  e['sources']=[{k:v for k,v in s.items() if k!='generated_pdf'} for s in e['sources']]
  if pr and pr.get('generated'):e['paragraph_source']=copy.deepcopy(pr['generated'])
  elif pr:
   src=copy.deepcopy(pr['source']);e['sources'].remove(next(s for s in e['sources'] if s['file']==src['file']))
   e['sources'].insert(0,src)
   e['paragraph_source']=dict(file=src['file'],page=pr['page_start'],paragraph_start_page=pr['page_start'],page_end=pr['page_end'],sentence_page_verified=True,is_original_pdf=True,verification=pr['verification'])
  else:
   src=e['sources'][0];key=(sid,src['file']+'#'+src['locator'])
   if key in locations:e['paragraph_source']=copy.deepcopy(locations[key])
   else:
    assert src.get('page'),('missing phrase source',sid)
    e['paragraph_source']=dict(file=src['file'],page=src['page'],paragraph_start_page=src['page'],sentence_page_verified=False,is_original_pdf=True,verification='原句沿用语料；页码按原始出处，未新增逐字符核对')
  if e['reading_body']:
   sub=c['reading_subtype'];loc=c['unit_locator']
   kind='选词填空正文' if 'Section A' in sub else '长篇阅读正文' if 'Section B' in sub else '仔细阅读正文'
   e['source_display_locator']=kind+' · '+(loc if loc.startswith('段落') else sub+' · 正文')
  else:e['source_display_locator']=e['category']+' · '+e['sources'][0]['locator']
  return e
 rows=copy.deepcopy(core);known={r['word'] for r in rows}
 for p in load('阅读高频500选词.json'):
  if p['word'] not in known:rows.append(dict(rank=len(rows)+1,word=p['word'],tier='阅读高频',statistics={a:W[p['word']][a] for a in ['exam_count','exam_coverage','exam_recent','exam_sessions','categories','forms','reference_count']}))
 for r in rows:
  w=r['word'];e=example(mapping['words'][w],w);r['example']=e
  if w in POS_FIX:e['pos']=POS_FIX[w]
  pos=e['pos'];g=ns['contextual_meaning'](w,e)
  if w not in rolekeys:g=POS_GLOSSES.get(w,{}).get({'N':'n','V':'v','J':'a','R':'r'}.get(e['pos'][:1]),GLOSSES.get(w,g))
  if w in FIX:g=FIX[w]
  if w=='like' and e['pos'].startswith('V'):g='喜欢'
  # Keep concise, coherent senses in the quick list; remove dictionary field tags.
  g=re.sub(r'\[(?:计|医|法|网络)[^\]]*\]','',g)
  if re.search(r'(?:^|；)\s*(?:n|v|vt|vi|a|adj|adv)\.',g):g=re.sub(r'(?:^|；)\s*(?:n|v|vt|vi|a|adj|adv)\.\s*','；',g)
  g=re.sub(r'\s+','',g).strip('； ')
  assert g,('empty meaning',w)
  r.update(meaning_editorial=g,context_pos_editorial=e['pos'],quick_meaning=g)
  if w=='specie':r.update(display_word='species',ipa_uk='/ˈspiːʃiːz/',ipa_editorial='/ˈspiːʃiːz/',sense_editorial='species.n.01')
 save('vocabulary_oct27_candidates1664.json',rows)
 for p in phrases:p['example']=example(mapping['phrases'][p['phrase']])
 save('core_phrases_sentence_oct27.json',phrases)
 save('阅读配句展示OCR校订.json',list({x['sid']:x for x in errata}.values()))
 (D/'词义待核对_oct27.txt').write_text('\n'.join(f"{r['word']} | {r['example']['pos']} | {r['meaning_editorial']} | {r['example']['display_text']} | {r['example']['zh']}" for r in rows),encoding='utf8')
 print('ASSEMBLED',len(rows),'PHRASES',len(phrases),'ERRATA',len({x['sid'] for x in errata}))
 return rows

def commit():
 rows=load('vocabulary_oct27_enriched1664.json');old=load('vocabulary_oct27_candidates1664.json');assert [r['word'] for r in rows]==[r['word'] for r in old]
 core=rows[:1500]
 for n in ['core_words_enriched1500.json','core_words.json','core_words_with_source_pages.json']:save(n,core)
 byword={r['word']:r for r in rows};reading=[]
 for p in load('阅读高频500选词.json'):
  r=copy.deepcopy(byword[p['word']]);s=p['statistics'];r.update(rank=p['rank'],tier='阅读正文高频',statistics_scope='reading_body')
  r['statistics']=dict(exam_count=s['count'],exam_coverage=s['exam_coverage'],exam_recent=s['recent'],exam_sessions=s['exam_sessions'],categories=s['categories'],forms=s['forms'],reference_count=0)
  if r['word']=='specie':r.update(word='species',corpus_lemma='specie',display_word='species',normalization_note='旧语料将species误归入specie；本册按原始词形校正为species（物种）。旧总索引仍按specie定位；无额外增加频次。')
  assert r['example']['reading_body'],r['word'];reading.append(r)
 save('reading_words_enriched500.json',reading);save('core_phrases.json',load('core_phrases_sentence_oct27.json'))
 save('阅读配句修订配置.json',dict(version='2026-10-30',core=1500,reading=500,overlap=336,union=1664,core_reading_examples=1239,core_listening_examples=261,translation_note='参考译文按原句编写或校订；不视作官方答案或教师审定译文',scope='阅读500独立按阅读正文出现次数排序，不排除1500中已有词'))
if __name__=='__main__':
 if '--commit' in sys.argv:commit()
 else:assemble()
