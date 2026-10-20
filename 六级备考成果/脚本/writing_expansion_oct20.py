"""Additional teaching material. Every example is newly authored, not exam text."""
import copy, collections

# theme | kind | base | alternative | restriction | before | after | zh before | zh after | misuse
EXTRA=r'''
教育学习|词|remember|retain|retain强调把已学知识保留在记忆中；remember还可指回想起一次经历。|Regular revision helps students remember new words.|Regular revision helps students retain new words.|定期复习帮助学生记住新单词。|定期复习帮助学生保留对新单词的记忆。|remember to do表示记得去做，不能改成retain to do。
教育学习|词|explain|clarify|clarify着重消除不清楚之处；explain可以详细解释原因，不必暗示原来有歧义。|The teacher explained the unclear rule.|The teacher clarified the unclear rule.|老师解释了那条不清楚的规则。|老师澄清了那条不清楚的规则。|解释完整历史过程一般用explain，不必改为clarify。
教育学习|短语|review|go over|go over lessons/notes表示复习；较口语，正式文章保留review也很好。|Students should review their notes before class.|Students should go over their notes before class.|学生课前应复习笔记。|学生课前应温习笔记。|go over用于复习义时后面直接接材料；不写go over about notes。
教育学习|短语|learn something well|develop a solid grasp of|后者强调形成扎实理解，不一定包含熟练操作；宾语宜为理论、基础知识。|Students need to learn the basic theory well.|Students need to develop a solid grasp of the basic theory.|学生需要把基础理论学好。|学生需要扎实掌握基础理论。|只能在学好强调理解时近似改写；学会游泳不能照搬a grasp of swimming。
教育学习|短语|have difficulty doing|struggle to do|struggle语气更强，强调努力仍感困难；完全保留程度时可继续用have difficulty。|Some students have difficulty keeping up with the course.|Some students struggle to keep up with the course.|一些学生跟上课程有困难。|一些学生很吃力地跟上课程。|difficulty后用doing；struggle后用to do。此处加强了困难程度。
科技数字生活|词|accurate|precise|accurate侧重结果正确；precise侧重细节或测量精确，二者不总能互换。|The sensor provides accurate measurements.|The sensor provides precise measurements.|传感器提供准确的测量结果。|传感器提供精密的测量结果。|重复测量很接近不代表都接近真值；不能把精密与准确混作同一性质。
科技数字生活|词|easy|straightforward|straightforward表示步骤直接、容易理解，不能替换easy-going等固定组合。|The registration process is easy to understand.|The registration process is straightforward.|注册流程容易理解。|注册流程简单明了。|不把an easy person改成a straightforward person；后者通常表示坦率。
科技数字生活|短语|keep in touch with|stay in contact with|都可表示与人保持联系；contact在这一用法中不可数。|Digital tools help families keep in touch with one another.|Digital tools help families stay in contact with one another.|数字工具帮助家人相互保持联系。|数字工具帮助家人相互保持联系。|不写stay in contacts with；不能省去with后的联系对象。
科技数字生活|短语|a lot of information|a large amount of information|information不可数；后者较正式，不改变信息数量多这一基本意思。|Users receive a lot of information every day.|Users receive a large amount of information every day.|用户每天接收大量信息。|用户每天接收大量信息。|不写many informations；可数名词要用a large number of。
科技数字生活|短语|make something better|improve|把make + 宾语 + better转成及物动词improve，保留被改善的对象。|Clear instructions can make the user experience better.|Clear instructions can improve the user experience.|清晰的说明能让用户体验更好。|清晰的说明能改善用户体验。|不写improve users better；改写后better已由improve表达。
职业发展|词|need|require|require表示需要，语体较正式；此处宾语保持不变，不自动增加法律强制性。|New employees need practical training.|New employees require practical training.|新员工需要实践培训。|新员工需要实践培训。|require还可表示要求；require sb to do与sb need to do结构不同。
职业发展|词|enough|sufficient|修饰名词时sufficient置于名词前；enough还可置于形容词之后。|The team has enough time to finish the task.|The team has sufficient time to finish the task.|团队有足够时间完成任务。|团队有充分时间完成任务。|不能把old enough写成old sufficient；sufficient常用于数量或条件。
职业发展|短语|be able to|be capable of|capable of后接名词或动名词，强调能力；具体一次成功做成某事时不必改写。|The team is able to solve complex problems.|The team is capable of solving complex problems.|团队能够解决复杂问题。|团队具备解决复杂问题的能力。|不写capable to solve；过去一次成功完成常用managed to，而非机械替换。
职业发展|短语|be good at|be skilled in|skilled in突出经过学习形成的技能；good at适用范围更广。|She is good at data analysis.|She is skilled in data analysis.|她擅长数据分析。|她熟练掌握数据分析技能。|不能把good at making excuses改成职业能力式的skilled in而不看语境。
职业发展|短语|get ready for|prepare for|都可表示为某事做准备；prepare for后接事情，prepare to后接动词。|Graduates should get ready for future challenges.|Graduates should prepare for future challenges.|毕业生应为未来挑战做好准备。|毕业生应为未来挑战做好准备。|不写prepare for face challenges；应为prepare to face challenges。
社会与个人|词|clear|explicit|explicit强调明确说出、不让人猜测；clear还可指容易理解或看清。|The rules make people's responsibilities clear.|The rules make people's responsibilities explicit.|规则让人们的责任清楚明了。|规则明确说明人们的责任。|clear water中的clear不能改为explicit；此处加强明确表达这一侧面。
社会与个人|词|careful|cautious|careful可指做事仔细；cautious着重避免风险，不能把细心一概改成谨慎。|People should be careful when sharing personal information.|People should be cautious when sharing personal information.|人们分享个人信息时应小心。|人们分享个人信息时应谨慎。|a careful analysis通常是细致分析，不一定是a cautious analysis。
社会与个人|短语|make a choice|make a decision|在选择具体行动方案时接近；decision还可指不涉及多个选项的决定。|Young people should make a choice based on their own goals.|Young people should make a decision based on their own goals.|年轻人应根据自身目标作出选择。|年轻人应根据自身目标作出决定。|不能由此把have no choice改成have no decision；固定搭配含义不同。
社会与个人|短语|keep doing|continue to do|此处都表示持续进行；continue也可接doing，keep不能直接接to do。|People should keep learning throughout their lives.|People should continue to learn throughout their lives.|人们应终身持续学习。|人们应终身持续学习。|不写keep to learn；keep to另有遵守、不偏离之义。
社会与个人|短语|more and more|an increasing number of|后面接可数名词复数时可改写；不可数名词用an increasing amount of。|More and more students volunteer in their communities.|An increasing number of students volunteer in their communities.|越来越多学生参与社区志愿服务。|越来越多学生参与社区志愿服务。|many students只是数量多，不一定表示增加趋势；不要丢掉趋势。
沟通合作|词|say|state|state较正式，强调清楚陈述；可保留that从句。|The report says that cooperation is necessary.|The report states that cooperation is necessary.|报告说合作是必要的。|报告指出合作是必要的。|say hello不能机械替换成state hello；state不能自动证明观点正确。
沟通合作|词|show|demonstrate|demonstrate在证据语境表示清楚表明；show适用范围更广。|The example shows the value of clear communication.|The example demonstrates the value of clear communication.|这个例子显示了清晰沟通的价值。|这个例子表明了清晰沟通的价值。|show sb a photo通常保留show；不要为正式而改成demonstrate sb a photo。
沟通合作|词|discuss|debate|debate含讨论不同立场或争议的意味，比一般discuss更强调分歧。|The students discussed whether phones should be allowed in class.|The students debated whether phones should be allowed in class.|学生讨论课堂上是否应允许使用手机。|学生就课堂是否应允许使用手机展开辩论。|若只是交换安排信息，debate会增加争论意味，不能视为完全等义。
沟通合作|短语|pay attention to|give attention to|在关注问题这一语境接近，均保留介词to；后面可接名词或动名词。|Team members should pay attention to quieter colleagues' ideas.|Team members should give attention to quieter colleagues' ideas.|团队成员应关注较少发言同事的想法。|团队成员应重视较少发言同事的想法。|to在此为介词；接动词要用doing，不能直接接动词原形。
沟通合作|短语|talk about|discuss|discuss为及物动词，直接接话题；前者更口语。|Team members should talk about the plan before acting.|Team members should discuss the plan before acting.|团队成员应在行动前讨论计划。|团队成员应在行动前讨论计划。|不写discuss about the plan；talk to sb中的talk也不能直接这样换。
环境健康|词|limit|restrict|restrict常强调加以约束；用于使用量时接近limit，但语气可能更强。|Cities should limit the use of disposable plastic bags.|Cities should restrict the use of disposable plastic bags.|城市应限制一次性塑料袋的使用。|城市应限制一次性塑料袋的使用。|restrict不等于ban；限制不代表完全禁止。
环境健康|词|dirty|polluted|polluted明确表示受到污染；dirty仅表示不干净，范围更广。|The river is dirty because of industrial waste.|The river is polluted by industrial waste.|工业废物使这条河很脏。|这条河受到工业废物污染。|衣服沾灰通常用dirty，不应都写polluted；此处污染原因已明确。
环境健康|词|clean|purify|purify强调去除杂质或有害成分；比一般clean更具体，不能保证完全纯净。|The system cleans the water by removing harmful substances.|The system purifies the water by removing harmful substances.|系统通过去除有害物质清洁水体。|系统通过去除有害物质净化水体。|打扫房间用clean the room；不写purify the room来代替普通打扫。
环境健康|短语|be in danger|be at risk|在受到伤害威胁时接近；at risk of后接风险事件，不能省掉关键条件。|Some species are in danger because their habitats are shrinking.|Some species are at risk because their habitats are shrinking.|一些物种因栖息地缩小而处于危险中。|一些物种因栖息地缩小而面临风险。|at risk不自动等于已发生损害；不应改写成have become extinct。
环境健康|短语|make people aware of|raise people's awareness of|把宾语补足语结构转为名词结构，保留需要提高意识的人群。|The campaign makes residents aware of food waste.|The campaign raises residents' awareness of food waste.|这项活动让居民意识到食物浪费问题。|这项活动提高居民对食物浪费问题的认识。|raise awareness不等于问题已经解决，不能删除后续行动。
社会发展|词|build|establish|establish在创建制度、机制、机构时自然；建筑物实际施工可继续用build。|The city plans to build a network of community services.|The city plans to establish a network of community services.|城市计划建设社区服务网络。|城市计划建立社区服务网络。|build a bridge的具体建造义不宜机械换成establish a bridge。
社会发展|词|support|assist|assist在帮助人做事时可替换support，但不包含赞同某种观点的含义。|These volunteers support older residents in using online services.|These volunteers assist older residents in using online services.|这些志愿者帮助老年居民使用在线服务。|这些志愿者协助老年居民使用在线服务。|support a policy表示支持政策时不能改成assist a policy。
社会发展|词|poor|disadvantaged|poor可指收入低；disadvantaged指处于不利条件，范围可包含教育和机会，不是所有贫困的同义词。|The programme helps students from poor families.|The programme helps students from disadvantaged backgrounds.|这个项目帮助来自贫困家庭的学生。|这个项目帮助家庭或成长条件不利的学生。|后一表达扩大了范围；需要精确指低收入时用low-income families。
社会发展|短语|provide somebody with something|provide something for somebody|在为某群体提供物品或服务时可转换，注意对象顺序。|Libraries provide residents with free learning resources.|Libraries provide free learning resources for residents.|图书馆为居民提供免费学习资源。|图书馆向居民提供免费的学习资源。|练习中优先使用with或for的完整搭配，明确提供物与接受者的关系。
社会发展|短语|spend money on|invest in|invest in增加期待未来回报或收益的含义，只在有这种目的时改写。|The government spends money on education to improve future opportunities.|The government invests in education to improve future opportunities.|政府在教育上花钱，以改善未来机会。|政府投资教育，以改善未来机会。|所有支出不一定是投资；没有长期收益含义时保留spend。
文化传承|词|old|ancient|ancient表示年代非常久远，比old强；用于古代历史对象时可用。|The museum displays objects from very old civilizations.|The museum displays objects from ancient civilizations.|博物馆展出年代十分久远的文明遗物。|博物馆展出古代文明遗物。|几十年前的流行歌曲通常是old songs，不能一概称ancient songs。
文化传承|词|keep|maintain|maintain强调使某种状态持续；此处不是keep的保留物品或继续做事用法。|Local communities work to keep the tradition alive.|Local communities work to maintain the vitality of the tradition.|当地社区努力使传统保持活力。|当地社区努力维持传统的活力。|不写maintain doing来替换keep doing；maintain后接名词对象。
文化传承|词|value|appreciate|value强调认为有价值、珍视；appreciate可强调理解其价值或欣赏。|Students should value the diversity of local traditions.|Students should appreciate the diversity of local traditions.|学生应珍视地方传统的多样性。|学生应理解并欣赏地方传统的多样性。|appreciate还可表示感激；value不一定包含欣赏的体验，侧重略变。
文化传承|短语|hand down|pass on|传承知识、故事、技艺时接近，均可加to引出传承对象。|Families hand down local stories to younger generations.|Families pass on local stories to younger generations.|家庭把地方故事传给年轻一代。|家庭将地方故事传承给年轻一代。|pass on information也可只是转告消息；不是每处都有文化传承含义。
文化传承|短语|be known for|be renowned for|renowned表示广为人知、有名望，强于普通known；需要有一定知名度依据。|The town is known for its traditional crafts.|The town is renowned for its traditional crafts.|这个镇以传统手工艺为人所知。|这个镇以传统手工艺闻名。|不能为换词把只在小范围有人知道写成广负盛名；区别for与as。
'''

# theme | basic paragraph | revised paragraph | Chinese | review comments
PARAGRAPHS=r'''
教育学习|Regular revision helps students remember new words. Teachers can help learning by giving clear feedback. Students should use what they learn to solve practical problems.|Regular revision helps students retain new words. Teachers can facilitate learning by giving clear feedback. Students should apply what they learn to practical problems.|定期复习帮助学生记住新单词。教师可通过清晰反馈促进学习。学生应把所学运用于实际问题。|remember到retain突出记忆保留；help learning到facilitate learning保留过程宾语；use...to solve到apply...to调整结构。保留helps/can/should的语气，不添加考试分数或研究数据。
科技数字生活|Digital tools help families keep in touch with one another. However, users receive a lot of information every day. Clear instructions can make the user experience better.|Digital tools help families stay in contact with one another. However, users receive a large amount of information every day. Clear instructions can improve the user experience.|数字工具帮助家人保持联系。但用户每天会接收大量信息。清晰的说明可以改善用户体验。|保留However的转折；information仍不可数；make...better转为improve后保留can，不宣称所有工具都会改善体验。
职业发展|New employees need practical training. They need enough time to improve their skills. Training can help them get ready for future challenges.|New employees require practical training. They need sufficient time to improve their skills. Training can help them prepare for future challenges.|新员工需要实践培训，也需要足够时间提高技能。培训能帮助他们准备应对未来挑战。|require不自动变成强制法律要求；sufficient放在time前；get ready for到prepare for保留对象与can的可能性。
社会与个人|People should keep learning throughout their lives. When they make a choice, they should consider their own goals. This habit is good for personal growth.|People should continue to learn throughout their lives. When they make a decision, they should consider their own goals. This habit is beneficial to personal growth.|人们应终身持续学习，作选择时应考虑自己的目标。这一习惯有益于个人成长。|keep doing转continue to do；选择与决定在当前行动语境接近；good for转beneficial to。保留This habit指代，不把建议写成既成事实。
沟通合作|The report says that cooperation is necessary. Team members should talk about the plan before acting. They should also pay attention to quieter colleagues' ideas.|The report states that cooperation is necessary. Team members should discuss the plan before acting. They should also give attention to quieter colleagues' ideas.|报告指出合作是必要的。成员应在行动前讨论计划，也应关注较少发言同事的想法。|state只改变陈述语体，不增加证据；discuss后不带about；关注对象仍是同事的想法，不偷换成强制认同。
环境健康|Cities should limit the use of disposable plastic bags. The campaign makes residents aware of food waste. These measures may help protect the environment.|Cities should restrict the use of disposable plastic bags. The campaign raises residents' awareness of food waste. These measures may help safeguard the environment.|城市应限制一次性塑料袋的使用。宣传活动使居民认识食物浪费问题。这些措施可能有助于保护环境。|restrict不等于ban；提高意识不等于已消除浪费；保留may help，不能写成will solve every environmental problem。
社会发展|Libraries provide residents with free learning resources. Volunteers support older residents in using online services. Together, these services can make daily life easier.|Libraries provide free learning resources for residents. Volunteers assist older residents in using online services. Together, these services can make daily life easier.|图书馆为居民提供免费学习资源。志愿者帮助老年居民使用在线服务。这些服务共同让日常生活更便利。|provide转换时居民仍是接受者；support到assist限于具体协助义；最后一句保留原表达，避免为增加替换数量而硬换。
文化传承|Families hand down local stories to younger generations. Schools can help students understand the value of these traditions. Communities also work to keep the traditions alive.|Families pass on local stories to younger generations. Schools can help students understand the value of these traditions. Communities also work to maintain the vitality of the traditions.|家庭把地方故事传给年轻一代，学校可帮助学生理解这些传统的价值，社区也努力维持传统的活力。|传承对象与方向不变；保留understand以强调理解，不偷换成已经珍视；keep...alive改为maintain the vitality of，保留努力过程。
'''

# trap | wrong | corrected | explanation
TRAPS=r'''
把相关写成因果|Screen time is associated with poor sleep, so screen time causes poor sleep.|Screen time is associated with poor sleep.|相关性不能自动推出因果；若没有额外证据，不能加so causes。
把可能写成必然|Regular exercise may help reduce stress. → Regular exercise eliminates stress.|Regular exercise may help alleviate stress.|may、help与reduce的力度均需保留；eliminate是消除，意义过强。
替换对象方向颠倒|Replace paper forms with online forms. → Substitute paper forms for online forms.|Substitute online forms for paper forms.|replace A with B与substitute B for A对象顺序相反。
名词可数性错误|Users receive many informations.|Users receive a large amount of information.|information不可数；a large number of后面接可数名词复数。
主语能力与资源可用性混淆|Digital libraries make students accessible to books.|Digital libraries make books accessible to students.|可获取的是书籍，学生是使用者；宾语与to后的对象不能颠倒。
词尾搭配照抄|The course facilitates students to learn.|The course facilitates student learning.|facilitate后接名词或动名词；enable students to learn是另一种可用结构。
词性不变换就堆高级词|The policy is benefit to residents.|The policy is beneficial to residents.|benefit是名词或动词，此处表语用形容词beneficial。
动词后多加介词|Team members discussed about the plan.|Team members discussed the plan.|discuss是及物动词；也可写had a discussion about the plan。
介词后仍用动词原形|The team is capable to solve the problem.|The team is capable of solving the problem.|capable of后用名词或动名词；able to后接原形。
趋势被静态数量替代|More and more students volunteer. → Many students volunteer.|An increasing number of students volunteer.|many只说明数量多，不保留不断增加的趋势。
无证据加强重要程度|Feedback is useful. → Feedback is indispensable in every situation.|Feedback is useful in supporting learning.|useful不自动等于不可或缺，every situation也扩大范围。
把提醒认识写成已经行动|The campaign raises awareness of food waste. → The campaign ends food waste.|The campaign helps residents recognise the problem of food waste.|意识提高与行为改变、问题解决是不同层次。
声称获得固定分数|Using sophisticated words guarantees a high score.|Use precise words that fit the meaning and grammar.|词汇复杂程度不能单独保证成绩；首先保证切题和语言准确。
为了多样而换掉关键术语|Privacy protection is important. → Secrecy protection is important.|Privacy protection is important.|privacy为隐私权或私人信息边界；secrecy强调保密，不能当成全部等义词。
同主题也不是同义|Young people need experience. → Young people need expertise.|Young people need practical experience.|经历或经验并不必然构成专业专长；expertise会提高能力要求。
误改题目规定首句|题目要求照抄给定首句，却把其中important换成essential。|按题目要求照抄给定首句，在后续自写句中练习替换。|具体硬性任务以原卷Directions为准；替换练习不能改变必须照抄的文字。
'''

def build_expanded(base):
 data=copy.deepcopy(base);extra=[]
 for i,line in enumerate(EXTRA.strip().splitlines(),101):
  cols=line.split('|');assert len(cols)==10,(i,len(cols))
  theme,kind,a,b,note,en1,en2,zh1,zh2,misuse=cols
  extra.append(dict(id=f'R{i:03}',theme=theme,kind=kind,base=a,alternative=b,distinction=note,before=en1,after=en2,chinese_before=zh1,chinese_after=zh2,misuse=misuse,example_origin='自编迁移练习，不计入真题频次',added_in='2026-10-20'))
 assert len(extra)==40
 data['groups'].extend(extra)
 # Four new tasks per theme. Every task has its own conditional reference answer.
 for ti,theme in enumerate(data['themes']):
  selected=[g for g in extra if g['theme']==theme][:4]
  for g in selected:
   number=len(data['exercises'])+1
   data['exercises'].append(dict(id=f'P{number:02}',theme=theme,prompt=g['before'],chinese=g['chinese_before'],hint=g['alternative'],answer=g['after'],answer_chinese=g['chinese_after'],explanation=g['distinction']+' '+g['misuse'],replacement_id=g['id'],example_origin='自编练习'))
 data['paragraphs']=[dict(id=f'D{i:02}',theme=t,before=b,after=a,chinese=z,review=n,example_origin='自编段落，不是真题范文') for i,line in enumerate(PARAGRAPHS.strip().splitlines(),1) for t,b,a,z,n in [line.split('|')]]
 data['traps']=[dict(id=f'E{i:02}',title=t,wrong=w,correct=c,explanation=e) for i,line in enumerate(TRAPS.strip().splitlines(),1) for t,w,c,e in [line.split('|')]]
 data['word_groups']=sum(g['kind']=='词' for g in data['groups']);data['phrase_groups']=sum(g['kind']=='短语' for g in data['groups'])
 assert len(data['groups'])==140 and data['word_groups']==80 and data['phrase_groups']==60
 assert len(data['exercises'])==64 and set(collections.Counter(e['theme'] for e in data['exercises']).values())=={8}
 assert len(data['paragraphs'])==8 and len(data['traps'])==16
 data['version']='2026-10-20';return data
