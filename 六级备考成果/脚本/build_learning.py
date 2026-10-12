import sys,json,re,collections,csv,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'六级备考成果'/'数据';sys.path.insert(0,str(D/'python_libs'));sys.stdout.reconfigure(encoding='utf-8')
from rapidfuzz.fuzz import partial_ratio
from bs4 import BeautifulSoup
def load(n):return json.loads((D/n).read_text(encoding='utf-8'))
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
words=load('word_statistics.json');sentences=load('sentences.json');units=load('corpus_units.json');refs=load('reading_bilingual_reference.json');SL={s['id']:s for s in sentences}
STOP=set('a an the and or but if as at by for from in into of on out to up with about after all also am are be been being can could did do does doing each either even ever every few first get gets getting give go good got great had has have having he her here hers herself him himself his how i it its itself just last little lot made make makes making man many may me men might more most much must my new next no nor not now off old once one only other our ours ourselves over own people person put same say says said see seem she should so some such take than that their theirs them themselves then there these they thing things think this those through time too two under until us use used using very want was way we well were what when where which while who whom why will would year years you your yours yourself yourselves young work world life like need help day days today know large long small come become part less best back still often always around both change country different end find high keep learn look number place point really right show start state study sure tell together try water week without yes name never again before during between however something nothing anyone everyone everything within another any school student students college university teacher child children family friend woman women say much money business job times able better own course certain several especially example kind'.split())
BAD=set('answer sheet question questions direction directions section part passage words write minutes page essay following choose marked letter corresponding choices heard centre comprehension based allowed sentence given quotes exam news listening reading writing translation english cet6'.split())
STOP.update('because whether others someone somebody anyone everyone since across along down almost always anyway anything although despite unless whose whatever whenever wherever yet perhaps soon enough else far also often parent feel grow believe call early alone important problem idea include company stop accord according'.split())
OVERRIDE={'increase':'增加；提高','reduce':'减少；降低','develop':'发展；开发；培养','development':'发展；开发','significant':'显著的；重要的','evidence':'证据；依据','approach':'方法；途径','issue':'问题；议题','concern':'关注；担忧','subject':'主题；学科；研究对象','term':'术语；时期','individual':'个人；个体的','benefit':'益处；使受益','impact':'影响；冲击','access':'获得或使用的机会；获取','practice':'实践；练习','resource':'资源','policy':'政策','potential':'潜力；潜在的','influence':'影响；影响力','associate':'联系；关联','figure':'数字；人物','conduct':'实施；行为','present':'目前的；呈现','mean':'意味着；平均值','account':'解释；账户','rate':'比率；速度','degree':'程度；学位','range':'范围；一系列','matter':'事情；重要','process':'过程；加工','support':'支持；证据支持','require':'需要；要求','effect':'影响；效果','concerns':'担忧','major':'主要的；专业','environment':'环境','maintain':'维持；保持','recognize':'识别；承认','recognise':'识别；承认','focus':'关注；集中','affect':'影响','demand':'需求；要求','challenge':'挑战','economic':'经济的','research':'研究','provide':'提供','improve':'改善；提高','opportunity':'机会','responsibility':'责任','responsible':'负责任的','ability':'能力','effective':'有效的','available':'可获得的；可使用的','experience':'经验；经历','quality':'质量；品质','value':'价值；重视','result':'结果；导致','expect':'预期；期待','public':'公众；公共的','specific':'具体的；特定的','level':'水平；程度','community':'社区；群体','suggest':'建议；表明','involve':'涉及；使参与','relate':'与……有关','respond':'回应；作出反应','lead':'引领；导致','leadership':'领导力','estimate':'估计；估算','supply':'供应；供给','apply':'应用；申请','application':'应用；申请','industry':'产业；行业','industrial':'工业的；产业的','mental':'心理的；精神的','physical':'身体的；物质的','control':'控制；管理','strength':'力量；优势','beneficial':'有益的','critical':'关键的；批判性的','technology':'技术；科技','digital':'数字的','knowledge':'知识','health':'健康','social':'社会的；社交的','society':'社会','system':'系统；制度','condition':'条件；状况','attention':'注意；关注','education':'教育','educational':'教育的','basic':'基础的','essential':'必要的；至关重要的','particular':'特定的；特别的','consider':'考虑；认为','likely':'可能的','probably':'很可能','recent':'最近的','success':'成功','successful':'成功的','traditional':'传统的','culture':'文化','skill':'技能','factor':'因素','information':'信息','future':'未来','current':'当前的','solution':'解决办法','professional':'专业的；职业的','difficult':'困难的','difficulty':'困难','successful':'成功的','achieve':'实现；达到','achievement':'成就','cause':'原因；造成','energy':'能源；精力','opinion':'观点','purpose':'目的','risk':'风险','cost':'成本；代价','relationship':'关系','income':'收入','employee':'雇员','employer':'雇主','attitude':'态度','behaviour':'行为','behavior':'行为','benefit':'益处；使受益','exchange':'交流；交换','promote':'促进；推广','protect':'保护','protection':'保护','efficient':'高效的','efficiency':'效率','concerned':'担忧的；有关的','positive':'积极的；肯定的','negative':'负面的；否定的','situation':'情况；局面','accountability':'责任；问责','productivity':'生产率；工作效率'}
def meaning(w):
 if w in OVERRIDE:return OVERRIDE[w]
 m=words[w]['meaning'].split('[网络]')[0].split('[医]')[0].split('[法]')[0]
 m=re.sub(r'\([^)]{25,}\)','',m);m=m.split('；')[0:3]
 return '；'.join(m)[:100]
def contextual_meaning(w,e):
 text=words[w]['meaning'].split('[网络]')[0]
 parts=re.split(r'(?:^|；)\s*(n|vi|vt|v|a|adj|adv|prep|pron|num|conj|aux)\.\s*',text)
 blocks=collections.defaultdict(list)
 for i in range(1,len(parts)-1,2):
  typ={'n':'N','vi':'V','vt':'V','v':'V','a':'J','adj':'J','adv':'R','prep':'I','conj':'I','pron':'P','aux':'M','num':'C'}[parts[i]];blocks[typ].append(parts[i+1])
 typ=e['pos'][:1]
 if typ not in blocks and len(blocks)==1:typ=next(iter(blocks));e['pos']={'N':'NN','V':'VB','J':'JJ','R':'RB','I':'IN'}.get(typ,e['pos'])
 if w=='weight' and e['pos'].startswith('J'):typ='N';e['pos']='NN'
 role={
 'mean':{'V':'我是说；我的意思是' if re.search(r'\bI mean\b',e['text']) else '意味着','N':'平均值','J':'吝啬的；刻薄的'},
 'increase':{'V':'增加；提高','N':'增长；增幅'},'lead':{'V':'导致' if re.search(r'\blead(?:s|ing)?\b.{0,60}\bto\b',e['text'],re.I) else '引领；带领','N':'铅；领先地位'},
 'live':{'V':'生存；居住','J':'活的；实况的'},'meet':{'V':'会面' if 'meeting with' in e['text'] else '遇见；满足'},
 'face':{'V':'面对；面临','N':'面孔；表面'},'present':{'V':'展示；呈现','N':'礼物；现在','J':'当前的；在场的'},
 'conduct':{'V':'开展；进行','N':'行为'},'account':{'V':'解释；占比','N':'账户；叙述'},'interest':{'N':'利息' if '利息' in e['zh'] else '兴趣；关注','V':'使感兴趣'},
 'issue':{'N':'问题；议题','V':'发布；颁布'},'project':{'N':'项目；研究课题','V':'预计；投射'},'record':{'N':'记录；档案','V':'记录；录制'},
 'claim':{'V':'声称；断言','N':'主张；索赔'},'stick':{'V':'坚持' if re.search(r'\bstick\b.{0,15}\bto\b',e['text'],re.I) else '粘住；插入','N':'棍；棒'},
 'major':{'J':'主要的','N':'专业'},'subject':{'N':'主题；学科；研究对象','V':'使遭受'},'practice':{'N':'实践；练习','V':'练习；实践'},
 'range':{'N':'范围；一系列','V':'在某范围内变化'},'figure':{'N':'数字；人物','V':'计算；认为'},'matter':{'N':'事情；物质','V':'重要；有关系'},
 'term':{'N':'术语；时期','V':'称为'},'benefit':{'N':'益处','V':'使受益；受益于'},'control':{'N':'控制；管理','V':'控制；管理'},
 'value':{'N':'价值','V':'重视；评价'},'support':{'N':'支持；支撑','V':'支持；支撑'},'cost':{'N':'成本；代价','V':'花费；付出代价'},
 'change':{'N':'变化','V':'改变'},'cause':{'N':'原因','V':'造成'},'process':{'N':'过程；流程','V':'加工；处理'},
 'individual':{'N':'个人；个体','J':'个人的；个别的'},'potential':{'N':'潜力','J':'潜在的'},'public':{'N':'公众','J':'公共的；公众的'},
 'sentence':{'N':'句子；判决'},'implement':{'V':'实施；执行','N':'工具'},'challenge':{'N':'挑战','V':'挑战；质疑'},
 'influence':{'N':'影响；影响力','V':'影响'},'impact':{'N':'影响；冲击','V':'影响；冲击'},'access':{'N':'获取或使用的机会','V':'获取；访问'},
 'concern':{'N':'担忧；关注','V':'涉及；使担忧'},'approach':{'N':'方法；途径','V':'接近；处理'},'supply':{'N':'供给；供应量','V':'供应；提供'},
 'estimate':{'N':'估计；估算值','V':'估计；估算'},'experience':{'N':'经验；经历','V':'经历；体验'},'demand':{'N':'需求；要求','V':'要求'},
 'condition':{'N':'条件；状况','V':'使适应'},'return':{'N':'回报；返回','V':'返回；归还'},'mind':{'N':'头脑；思想','V':'介意'},
 'approach':{'N':'方法；途径','V':'接近；处理'},'current':{'N':'水流；电流','J':'当前的'},'general':{'N':'将军','J':'总体的；一般的'},
 }
 if w in role and typ in role[w]:return role[w][typ]
 if w in OVERRIDE:return OVERRIDE[w]
 if blocks.get(typ):
  selected='；'.join(blocks[typ]);selected=re.split(r'\[|；\s*(?:n|v|adj|adv)\.',selected)[0]
  return '；'.join(re.split('[,，；]',selected)[:3]).strip()[:90]
 return meaning(w)
def good(s):
 t=s['text'];tokens=re.findall('[A-Za-z]+',t)
 return bool(7<=len(tokens)<=65 and len(t)<=440 and re.search(r'[.!?]["”\']?$',t) and not re.search(r'(?:Directions|Answer Sheet|You can make comments|You should write|.{20}\d{2}\s*[_—])',t) and len(s['lemmata'])/max(1,len(tokens))>.85)
def example(word,category=None):
 cand=[]
 for o in words[word]['occurrences']:
  s=SL[o['sentence']]
  if category and s['category'] not in category:continue
  if not good(s):continue
  score=20*(s['category']=='听力原文')+12*bool(s['zh'])+6*any(z['session']>='2024-01' for z in s['sources'])-abs(len(s['text'])-150)/35-len(s['zh'])/25
  cand.append((score,s,o))
 if not cand:
  cand=[(0,SL[o['sentence']],o) for o in words[word]['occurrences'] if SL[o['sentence']]['category'] not in ['作文范文','翻译参考译文']]
 if not cand:return None
 _,s,o=max(cand,key=lambda x:x[0]);e=dict(s);e['pos']=o['pos'];e['form']=o['form']
 if not e['zh'] and e['category']=='阅读真题':
  scored=[(partial_ratio(e['text'].lower(),r['en'].lower()),r) for r in refs if len(r['en'])>=len(e['text'])*.8]
  score,r=max(scored,key=lambda x:x[0]) if scored else (0,None)
  if score>=97:e['zh']=r['zh'];e['zh_type']='原句所在段的理解提示';e['zh_source']=r['source']
 return e
rank=sorted([w for w,v in words.items() if v['exam_count'] and len(w)>=4 and w not in STOP|BAD and not re.search(r'\d',w) and v['exam_coverage']>=2],key=lambda w:(words[w]['exam_coverage'],sum(s>='2024-01' for s in words[w]['exam_sessions']),words[w]['exam_recent'],words[w]['exam_count']),reverse=True)
core=[]
for w in rank:
 e=example(w,{'听力原文','阅读真题','作文题干','听力选项'})
 if not e or not good(e):continue
 core.append({'rank':len(core)+1,'word':w,'meaning':contextual_meaning(w,e),'statistics':{k:words[w][k] for k in ['exam_count','exam_coverage','exam_recent','exam_sessions','categories','forms','reference_count']},'example':e})
 if len(core)==500:break
save('core_words.json',core)
families=[g.split() for g in ['research researcher','develop development developer','educate education educational educator','employ employment employer employee','create creation creative creativity','compete competition competitive competitor','produce product production productive productivity producer','economy economic economical economist','protect protection protective','innovate innovation innovative','construct construction constructive','technology technological','environment environmental','improve improvement','decide decision decisive','define definition','communicate communication','organize organisation organization organizational','analyse analysis analytical','analyze analysis analytical','signify significant significance','respond response responsive','responsible responsibility','efficient efficiency inefficient','success successful successfully','benefit beneficial','achieve achievement','different difference differentiate','relate relation relationship relative','inform information informative','global globalization','contribute contribution contributor','imagine imagination imaginative','recognize recognition','recognise recognition','involve involvement','associate association associated','require requirement','consider consideration considerable','apply application applicant','consume consumption consumer','sustain sustainable sustainability','individual individuality','motivate motivation','participate participation participant','rely reliance reliable','vary variety various','society social socially','healthy health unhealthy']]
save('derived_word_families.json',[[w for w in g if w in words] for g in families if sum(w in words for w in g)>1])
phrases_text='''in terms of|就……而言
as a result|因此；结果
as a result of|由于
in addition|此外
in addition to|除……之外
for example|例如
for instance|例如
such as|例如
according to|根据
due to|由于
because of|因为
instead of|而不是；代替
rather than|而不是
in order to|为了
so as to|为了
on the other hand|另一方面
in contrast|相比之下
by contrast|相比之下
in fact|事实上
in particular|尤其；特别
in general|一般而言
in other words|换句话说
at least|至少
at the same time|同时
at first|起初
in the past|过去
in recent years|近年来
in the future|将来
in the long run|从长远看
in the short term|短期内
as well as|以及
as long as|只要
as far as|就……而言；直到
even though|尽管
even if|即使
now that|既然
whether or not|是否
more or less|或多或少
no longer|不再
not only|不仅
more than|超过；不仅仅
less than|少于
up to|达到；由……决定
all over the world|世界各地
around the world|世界各地
a wide range of|范围广泛的
a variety of|各种各样的
a number of|许多
a series of|一系列
the majority of|大多数
the number of|……的数量
the amount of|……的数量
the importance of|……的重要性
the ability to|……的能力
the impact of|……的影响
the lack of|缺乏……
the use of|……的使用
the development of|……的发展
the risk of|……的风险
the need for|对……的需要
the cost of|……的成本
access to|获取或使用……的机会
attention to|对……的注意
attitude towards|对……的态度
attitude toward|对……的态度
approach to|……的方法
response to|对……的回应
solution to|……的解决办法
contribute to|有助于；导致
lead to|导致
result in|导致
result from|起因于
depend on|取决于；依靠
rely on|依靠
focus on|关注；集中于
concentrate on|集中于
refer to|指；提到
relate to|与……有关
be related to|与……有关
be associated with|与……相关
be linked to|与……有联系
be based on|以……为基础
be likely to|可能会……
be able to|能够
be willing to|愿意
be expected to|预计会……
be used to|被用于；习惯于
be aware of|意识到
be responsible for|对……负责
be concerned about|担心……
be interested in|对……感兴趣
be involved in|参与……
be regarded as|被视为
be considered as|被认为是
be known as|被称为
be known for|因……而著名
be made of|由……制成
be made up of|由……组成
be exposed to|接触；暴露于
be committed to|致力于
be devoted to|致力于
take advantage of|利用
make use of|利用
take part in|参加
take care of|照顾
take into account|考虑到
take account of|考虑到
pay attention to|注意
attach importance to|重视
make a difference|产生影响
make an effort|努力
make efforts|努力
make progress|取得进展
make sense|有意义；讲得通
make sure|确保
give rise to|引起
give up|放弃
set up|建立
carry out|实施；开展
find out|查明
point out|指出
work out|解决；锻炼
deal with|处理
cope with|应对
come up with|提出
keep up with|跟上
catch up with|赶上
put forward|提出
cut down on|减少
turn out|结果是
bring about|引起
get rid of|摆脱
put off|推迟
look forward to|期待
in charge of|负责
in favor of|支持
in favour of|支持
in spite of|尽管
in response to|作为对……的回应
in relation to|关于；与……有关
in connection with|与……有关
with regard to|关于
with respect to|关于
regardless of|不管
apart from|除……之外
along with|连同
compared with|与……相比
compared to|与……相比
contrary to|与……相反
in comparison with|与……相比
on behalf of|代表
for the sake of|为了……
in place of|代替
in the absence of|缺少……时
on a daily basis|每天
in a sense|从某种意义上说
to some extent|在一定程度上
to a large extent|在很大程度上
to a certain extent|在一定程度上
by no means|绝不
in turn|反过来；依次
in return|作为回报
in conclusion|总之
to sum up|总之
first of all|首先
for one thing|一方面
for another|另一方面
on the whole|总体而言
all walks of life|各行各业
living standards|生活水平
economic development|经济发展
social development|社会发展
traditional culture|传统文化
artificial intelligence|人工智能
climate change|气候变化
mental health|心理健康
physical health|身体健康
public health|公共卫生
social media|社交媒体
digital skills|数字技能
digital literacy|数字素养
renewable energy|可再生能源
natural resources|自然资源
environmental protection|环境保护
personal development|个人发展
critical thinking|批判性思维
lifelong learning|终身学习
well-being|身心健康；福祉
work-life balance|工作与生活的平衡'''
phrase_data=[]
for line in phrases_text.splitlines():
 phrase,zh=line.split('|');pattern=re.compile(r'(?<![A-Za-z])'+re.escape(phrase).replace(r'\ ',r'\s+')+r'(?![A-Za-z])',re.I)
 occ=[]
 for s in sentences:
  if s['category'] in ['作文范文','翻译参考译文']:continue
  matches=list(pattern.finditer(s['text']))
  if matches:occ.append({'sentence':s['id'],'count':len(matches),'sources':s['sources']})
 if not occ:continue
 sessions=sorted({z['session'] for o in occ for z in o['sources']})
 ex=max([SL[o['sentence']] for o in occ],key=lambda s:15*bool(s['zh'])+10*good(s)+5*any(z['session']>='2024-01' for z in s['sources'])-len(s['text'])/150)
 phrase_data.append({'phrase':phrase,'meaning':zh,'count':sum(o['count'] for o in occ),'coverage':len(sessions),'sessions':sessions,'recent':sum(o['count'] for o in occ if any(z['session']>='2024-01' for z in o['sources'])),'occurrences':occ,'example':ex})
phrase_data.sort(key=lambda p:(p['coverage'],p['recent'],p['count']),reverse=True);save('phrase_statistics.json',phrase_data);save('core_phrases.json',phrase_data[:100])
# Frequency of concepts is based on Chinese originals; references are not counted as Chinese examinations.
concept_text='''发展|develop; development
建设|build; construction
政府|government
经济|economy; economic
社会|society; social
文化|culture; cultural
传统|tradition; traditional
历史|history; historical
技术|technology; technique
科技|science and technology
创新|innovation; innovate
资源|resource
服务|service; serve
提供|provide; offer
促进|promote; facilitate
提高|improve; enhance; raise
改善|improve
保护|protect; protection
政策|policy
措施|measure; action
生活|life; living
环境|environment
城市|city; urban
农村|rural area; countryside
农业|agriculture
交通|transport; transportation
产业|industry
企业|enterprise; company
教育|education
人才|talent
人口|population
老年人|the elderly; older people
养老|elderly care
健康|health; healthy
医疗|healthcare; medical care
旅游|tourism; travel
游客|tourist; visitor
桥|bridge
大楼|building
建筑|architecture; building
工程|project; engineering
开放|open; opening-up
改革|reform
世界|world
国际|international
全球|global
出口|export
消费|consume; consumption
消费者|consumer
生产|produce; production
产品|product
食品|food
食品安全|food safety
安全|safety; security
能源|energy
生态|ecology; ecological
绿色|green
污染|pollution
公园|park
设施|facility
公共|public
健身|fitness; exercise
社区|community
便利|convenient; convenience
便利服务|convenient services
生活水平|living standards
高质量发展|high-quality development
基础设施|infrastructure
人工智能|artificial intelligence
信息技术|information technology
电子商务|e-commerce
数字经济|digital economy
乡村振兴|rural revitalization
无人机|drone; unmanned aerial vehicle
远程医疗|telemedicine
劳动|labor; labour
节俭|frugality; thrift
传统美德|traditional virtue
文明|civilization
交流|exchange; communication
历史悠久|have a long history
位于|be located in; be situated in
著名|famous; renowned
闻名|be well known for
建于|be built in
吸引|attract
世纪|century
面积|area
数量|number
品质|quality
需求|need; demand
权益|rights and interests
社会保障|social security
尊老|respecting the elderly
自强自立|self-reliance and self-strengthening
近年来|in recent years
越来越|increasingly; more and more
不仅|not only
为了|in order to
逐渐|gradually
逐步|gradually; step by step
广泛|widely
持续|continuously
不断|constantly
显著|significantly
迅速|rapidly
重要|important; significant
著名景点|famous attraction
中国特色|Chinese characteristics
传统文化|traditional culture
中华民族|the Chinese nation
循环利用|recycle; recycling
生活方式|lifestyle
覆盖范围|coverage
确保|ensure
满足|meet; satisfy
增加|increase
减少|reduce
支持|support
鼓励|encourage
推动|promote; drive
历史遗址|historical site
革命|revolution
爱国主义|patriotism'''
tasks=load('translation_originals.json');concepts=[]
for line in concept_text.splitlines():
 phrase,en=line.split('|');hits=[]
 for task in tasks:
  text=re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])','',task['zh']);count=text.count(phrase)
  if not count:continue
  examples=[s.strip()+'。' for s in re.split('[。！？]',text) if phrase in s]
  hits.append({'count':count,'session':task['session'],'suite':task['suite'],'source':task['source'],'sentences':examples})
 if hits:
  concepts.append({'zh':phrase,'english':en,'count':sum(o['count'] for o in hits),'coverage':len(set(o['session'] for o in hits)),'tasks':len(hits),'recent':sum(o['count'] for o in hits if o['session']>='2024-01'),'occurrences':hits,'example':sorted(hits,key=lambda h:h['session'],reverse=True)[0]})
concepts.sort(key=lambda c:(c['coverage'],c['recent'],c['count']),reverse=True);save('translation_concepts.json',concepts)
# Writing theme labels are content-based; numbered editions remain traceable.
theme_map={
'2021-06': [('城镇化成就','社会发展','图表描述'),('高等教育成就','教育学习','图表描述'),('脱贫成就','社会发展','图表描述')],
'2021-12':[('追星现象','社会与个人','材料评论'),('父母过度保护孩子','教育学习','材料评论'),('辨别网络虚假信息','科技数字生活','材料评论')],
'2022-06':[('环保生活方式','环境健康','给定首句'),('学习新技能适应变化','教育学习','给定首句'),('帮助有需要的人','社会与个人','给定首句')],
'2022-09':[('培养数字技能','科技数字生活','给定首句'),('现实社交的乐趣','沟通合作','给定首句'),('互信开放促进合作','沟通合作','给定首句')],
'2022-12':[('信息技术与多样化学习','科技数字生活','给定首句'),('信息爆炸与批判性思维','教育学习','给定首句'),('培养团队精神','沟通合作','给定首句')],
'2023-03':[('容貌焦虑','环境健康','给定首句'),('选择过多与决策困难','社会与个人','给定首句'),('老年人与数字鸿沟','科技数字生活','给定首句')],
'2023-06':[('心理健康与身体健康','环境健康','给定首句'),('理性讨论与达成共识','沟通合作','给定首句'),('学会学习','教育学习','给定首句')],
'2023-12':[('基础知识与学科掌握','教育学习','给定首句'),('儿童自主探索与独立自信','教育学习','给定首句'),('老年人的社会贡献','社会发展','给定首句')],
'2024-06':[('数字素养与数字技能','科技数字生活','给定首句'),('社会实践与学业同等重要','教育学习','给定首句'),('自主学习能力','教育学习','给定首句')],
'2024-12':[('现实目标与持之以恒','社会与个人','给定首句'),('自律与个人成长','社会与个人','给定首句'),('大学探索与人生方向','教育学习','给定首句')],
'2025-06':[('求职准备与职业能力','职业发展','给定首句'),('负责任地使用社交媒体','科技数字生活','给定首句'),('人工智能与人类创造力','科技数字生活','给定首句')],
'2025-12':[('大学生应对竞争与挑战','职业发展','给定首句'),('中国梦与青年自我价值','社会发展','给定首句'),('教师影响学业与个人发展','教育学习','给定首句')],
'2026-06':[('城市居民培养对自然的热爱','环境健康','给定首句'),('青年责任感','社会与个人','给定首句'),('传统文化理解与文化自信','文化传承','给定首句')]}
prompts=load('writing_prompts.json')
for p in prompts:
 title,theme,form=theme_map[p['session']][int(p['suite'])-1];p.update(title=title,theme=theme,form=form)
save('writing_analysis.json',prompts)
save('writing_theme_statistics.json',{'themes':dict(collections.Counter(p['theme'] for p in prompts)),'forms':dict(collections.Counter(p['form'] for p in prompts))})
# Export flat data with every occurrence's sentence ID and exact token position.
with (D/'全部词形与出处.csv').open('w',encoding='utf-8-sig',newline='') as f:
 wr=csv.writer(f);wr.writerow(['lemma','form','sentence_id','token_position','category','session','suite','file','PDF_page','locator'])
 for w,v in words.items():
  for o in v['occurrences']:
   for s in o['sources']:wr.writerow([w,o['form'],o['sentence'],o['position'],SL[o['sentence']]['category'],s['session'],s['suite'],s['file'],s.get('page'),s['locator']])
print('CORE',len(core),'PHRASES',len(phrase_data[:100]),'CONCEPTS',len(concepts),'THEMES',load('writing_theme_statistics.json'),flush=True)
if (D/'core_words_enriched1500.json').exists():
 from prepare_vocabulary_revision import prepare
 from enrich_vocabulary import main as enrich_main
 prepare();enrich_main()
