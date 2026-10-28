# FYP outlines (A2) coding log — stage 2, P11-A2 to P15-A2

Coded blind from the stage-1 extracts in `coding_work/texts/` against each plan's own proposal extract (`P1x-A1.md`). No market data consulted.
Calibration reference: `rows/P10-A2.csv` (already done, not changed). Row builder with quote checks: `scratch_outlines/build_rows.py`
(every `quote_zh` is an exact substring of the outline extract, every `prev_quote_zh` an exact substring of the proposal extract, <= 40 汉字).

## Conventions applied to all five outlines

- **What gets a row.** (a) concept absent from the proposal extract -> `new`; (b) stance differs from the proposal -> `up`/`down`;
  (c) intensity clearly higher or lower -> `up`/`down`. Same stance at the same strength is not coded. No `dropped` rows are written for
  outlines, and nothing is coded as dropped because an extract is partial.
- **Dedicated chapter/section.** Counted only when the 章/节 heading names the concept alone (e.g. 第二节 培育生物产业, 第三节 大力发展旅游业).
  A heading that names a whole sector (e.g. 第十一章 振兴装备制造业) does not by itself raise each sub-industry.
- **Quantitative target.** A number for the industry's own output, length, capacity, coverage rate or share (e.g. 粮食综合生产能力5亿吨,
  铁路新线1.7万公里, 污水处理率70%, a dated ban). Land, energy-intensity and resource-use targets are not counted as industry targets.
  A new target on a concept the proposal already had at intensity 3 is coded `up` (intensity stays 3) per the brief, and flagged `[quant]`.
- **Named national programme / project list.** Named projects, bases or engineering programmes (e.g. 万村千乡市场工程, 南水北调, named hydropower
  stations, 生物产业专项工程). Flagged `[named programme]` / `[project-list]`.
- **Intensity.** 3 = a dedicated 节/章 for the concept, a named programme/project list, a quantitative target, or the strongest verb
  (大力/加快/振兴/优先/着力/重点发展; restrictive 严格控制/禁止/加快淘汰). 2 = explicit sentence with a clear verb (积极/发展/支持/鼓励/推进/培育;
  控制/调控). 1 = list mention only (including mentions inside a regional list or a reform list).
- **change_vs_prev direction.** Same stance: `up`/`down` by intensity versus the proposal's coded row (`rows/P1x-A1.csv` used as the index of
  what the proposal said). Different stance: ordered S+ > S0 > R-*, so S0->S+ is `up`, S+->S0 and S0/S+->R-* are `down`; the flip is
  tagged `[stance]` in notes. `pivot` is left to the merge script.
- **Verb-tier shifts alone are not coded** (e.g. 大力发展 -> 积极发展 with nothing else changing), and lists that merely extend an unchanged
  clause are not coded.
- **SW mapping.** One L1 per row (the L1 parent of the L2 codes); where a concept spans two L1s the primary one is used and the other is
  named in notes. Concepts with no single industry get `none`/`none`.
- **Regional chapters.** Region-specific industry lists (东北, 中部, 西部, 东部) are coded only when they name an industry the outline does not
  support elsewhere and the proposal lacks it (intensity 1).
- **Social infrastructure with no industry mapping** (农村饮水安全工程, 农村卫生设施, 农村文化设施) is not coded.
- English in `quote_en` is an unofficial translation.

## P11-A2 (十一五纲要, event_date 2006-03-16) vs P11-A1

Extract caveats: key-clause extract (clause level for 第十九–二十一章, 第二十七章, 第四十四、四十六–四十八章); all 专栏 boxes (高技术产业, 装备制造, 能源, 交通, 循环经济 project lists) are missing, so named-project counts in 专栏 are not seen. The proposal extract is also key clauses, so "absent from the proposal" means absent from that extract.

Judgement calls
- 煤炭 coded S0 `down`: the outline's section heading is 有序发展煤炭 (S0 wording) while the proposal's same measures (大型煤炭基地, 调整改造中小煤矿) were coded S+. Flagged [borderline][stance]; the outline also has 依法关闭 small mines and 产能亿吨级 consolidation (R-supply element in notes).
- 钢铁 coded R-supply 3 `down` (S0 list mention -> strict capacity control, 严格控制新增钢铁生产能力, dedicated 节). 电解铝 and 铜铅锌冶炼 R-supply 2 (控制总量/建设规模); 氧化铝 (适度发展) and 铝深加工 are folded into the 电解铝 row notes.
- 房地产: two rows. `房地产业` R-demand 3 (调控 of primary/secondary/rental markets, 严格控制大户型高档商品房) is matched to the proposal's 房地产业 row (property tax, R-demand 2); `普通商品住房与经济适用住房` S+ 3 (重点发展) is coded separately as `new` because it is a different object. Judged this split cleaner than choosing a single dominant stance for a section that is both supportive and restrictive.
- 食品工业 (S+ 3) is named separately from the proposal's 食品 row (safety regulation, R-demand) so that a development sentence is not turned into a spurious reversal; the outline repeats the safety-regulation sentence from the proposal. 餐饮 is coded S+ `up` for the same reason (鼓励发展零售、餐饮 vs hygiene regulation).
- 矿产资源开发 R-demand 3 `down`: the dedicated 第三节 加强矿产资源管理 is entry/licensing control versus the proposal's S+ geological-exploration sentence; support elements elsewhere noted.
- 石油天然气 S+ 3 `up`: heading 加快发展 + 国家石油储备基地 + named pipelines; pipelines are coded under 管道运输 (`up`, named projects).
- 港口航运 `up` 3 is [borderline]: named 国际航运中心 and Yangtze waterway, but no numeric target. 铁路/公路 `up` 3 on numeric targets (1.7万公里 new lines; 230万公里 with 6.5万公里 expressways).
- 核电, 电网, 太阳能, 装备制造业, 高技术产业, 集成电路, 软件, 三网融合, 环保产业, 循环经济, 对外承包 not coded: same stance and strength as the proposal (核电 adds 百万千瓦级 and 自主化 but no count).
- 水产 (发展水产养殖 + 休渔、禁渔 + 控制捕捞强度) not coded: mixed wording of about the same strength as the proposal.
- 农村沼气 (大力普及 -> 积极发展…等可再生能源) not coded: verb-tier shift only.
- 生产性服务业 / 消费性服务业 chapter headings not coded as concepts: they restate 现代服务业 (大力发展, level 3 in the proposal).
- Regional lists: 东北 (先进装备, 精品钢材, 石化, 汽车, 船舶基地) not coded separately; 中部 list coded only for 矿山机械 and 机车车辆 (intensity 1).
- Reform list 深化石油、电信、民航、邮政、烟草、盐业和市政公用事业改革: coded as five intensity-1 S0 rows (industries named for the first time; proposal had only the generic 垄断行业改革 row, which is unchanged and not recoded).
- Concepts coded `none`/`none`: 服务业, 高耗能产业, 高耗水产业, 矿产资源开发, 机电产品与高技术产品出口, 高危行业安全整治, 烟草与盐业体制改革.

## P12-A2 (十二五纲要, event_date 2011-03-16) vs P12-A1

Extract caveats: all 专栏 boxes (专栏4 制造业发展重点方向, 专栏5 战略性新兴产业创新发展工程, 专栏6 能源建设重点, 专栏7 交通建设重点) are missing from the extract, so named-project lists and numeric targets that sit in those boxes (e.g. rail and nuclear capacity) are not seen; no outline numbers are inferred from memory. Clause-level extract.

Judgement calls
- 战略性新兴产业 coded `up` (3): the 8% share target and dedicated 第十章 (产业创新发展工程, special fund). The seven SEI fields (新一代信息技术, 节能环保, 生物, 高端装备制造, 新能源, 新材料, 新能源汽车) were already at level 3 in the proposal with the same list, so they are not recoded; only sub-areas the proposal did not name are coded as `new` (intensity 2, 重点发展 inside a list): 云计算, 新型显示, 高端服务器, 航空装备, 卫星及应用, 轨道交通装备, 智能制造装备, 生物医药, 医疗器械 (生物医学工程产品), 生物农业, 生物制造, 太阳能, 风电, 生物质能. 集成电路 is `up` (1 -> 2) because the proposal had it only as a technology-breakthrough item.
- 冶金 and 建材 coded R-supply 3 (`new`): 严格控制总量扩张 is the strongest restrictive wording; the proposal only had the generic 淘汰落后产能 (coded under 过剩产能行业 and raised here to level 2 by 加快淘汰落后工艺技术和设备). 兼并重组 priority list (电解铝, 稀土, 医药) coded at intensity 1.
- 房地产业 `up` 3 (dedicated 第三节 改善房地产市场调控: 稳定房价 as a local work target, 差别化住房信贷、税收, 房地产税改革); 保障性住房 `up` 3 on the 3600万套 target (quote uses the extract's full-width digits).
- 食品 `up` 3 (dedicated 第一节 保障食品药品安全); 药品安全监管 coded separately as `new` R-demand because the proposal's 药品 row is the supply-guarantee system (S0), which the outline repeats.
- 煤炭 S+ `up`: the proposal had coal only inside a resource-price list (S0, level 1); the outline says 发展安全高效煤矿 with 兼并重组. 国家综合能源基地 coded as a named project list (3).
- 电网 `up` 3 and 管道运输 `up` 3 (heading 加快, named import corridors); both sit in 第三节 加强能源输送通道建设. 水电, 核电, 智能电网, 石油天然气 not recoded (same strength; the outline's nuclear and hydro wording carries no count in the extract).
- 港口航运 not coded: 大力推进长江等内河高等级航道建设 is a verb-tier shift (积极发展水运 in the proposal) without a target or named programme. 铁路, 公路, 高速铁路 not coded for the same reason (no numeric target in the extract).
- 林业 `up` (proposal tenure reform S0 -> outline 积极发展林业产业), 农业保险 `up` (S0 -> S+), 物流 `up` (S0 opening-up list item -> dedicated 大力发展现代物流业), 国防科技工业 `up` (S0 -> S+ 建设先进的国防科技工业 in dedicated 第六十章).
- 资源税改革 `down` (S0 reform -> R-demand 适当提高资源税税负). 海水淡化 `up` is [borderline] (verb 鼓励 -> 大力推进 plus longer unconventional-water list).
- Not coded because unchanged in strength: 服务业 umbrella wording (only the 4-point share target is coded), 生产性服务业, 生活性服务业, 文化产业 umbrella, 循环经济, 环保产业, 电子商务, 三网融合, 电子政务, 养老服务, 社会办医, 高耗能产业, 碳排放交易, 垄断行业.
- Reform lists (铁路、盐业; 电信、石油、民航、市政公用事业) coded as S0 rows (铁路 and 电力 体制改革 at 2, the rest at 1).
- 港澳台 and regional chapters: no rows (regional industry lists restate national wording).
- Concepts coded `none`/`none`: 战略性新兴产业, 服务业, 高技术服务业, 重点行业污染治理, 资源税改革, 机电产品与高新技术产品出口, 高耗能资源性产品出口, 矿产资源开发, 过剩产能行业, 盐业体制改革.


## P13-A2 (十三五纲要, event_date 2016-03-17) vs P13-A1

Extract caveats: clause-level extract of all篇 (about 830 lines); all 专栏 boxes are missing, so named-project lists and numeric targets that sit in boxes (e.g. 专栏 on 高端装备创新, 消费品质量, 铁路公路里程) are not seen. The proposal extract is also key clauses.

Judgement calls
- 战略性新兴产业 `up` 3 on the 15% share target and the dedicated 第二十三章 (national strategic-industry fund). The 新一代信息技术 / 新能源汽车 / 生物技术 / 绿色低碳 / 高端装备与材料 fields were already level 3 in the proposal and are not recoded; only sub-areas newly named are coded `new` (先进半导体, 增材制造, 新型飞行器, 量子通信, 合成生物与再生医学, 新一代核电装备, 精准医疗, 虚拟现实, 数字创意). The shared sentence 大力推进先进半导体、机器人、增材制造、智能系统、新一代航空装备 is used as the quote for four rows (one per industry).
- 煤炭 coded R-supply 3 `down` [stance]: 限制东部、控制中部和东北、优化西部地区煤炭资源开发 plus 加快…煤炭等行业过剩产能退出 versus the proposal's clean-utilisation S0; the support element (大力推进煤炭清洁高效利用) is in notes. 钢铁 R-supply 3 `up` (proposal level 1 carbon-control list item) on the same dedicated 第五节 积极稳妥化解产能过剩; 过剩产能行业 `up` 3.
- 房地产业 `up` 3 [stance]: destocking support (鼓励…购买库存商品房, 住房租赁市场) coded S+ against the proposal's S0 institutional-reform wording; the dedicated 第二节 plus REITs pilot (S0), 住房租赁企业, 旅游/养老/文化地产 (S+) as `new`. 房地产税 R-demand 2 coded separately (property-tax legislation absent from the proposal extract). 保障性住房 `up` 3 on the 棚户区 completion goal (no unit count in the extract, flagged [quant] with that caveat).
- 畜牧业 `up` (S0 -> S+): the proposal listed it only inside an integration clause; the outline says 发展农区畜牧业. 水产业 `up` (R-supply 退养还滩 -> S+); capture limits are a separate 海洋捕捞 R-supply 3 row.
- 化肥农药 R-demand 3 `new` (零增长行动 is a named programme); 农业社会化服务, 农业信息化 (物联网区域试验工程), 粮食收储 `up` 3 on named projects. 种业 `up` 3 on 新一轮品种更新换代行动计划.
- 生产性服务业 / 生活性服务业 `up` 3 [stance]: the proposal's wording (推动…向专业化和价值链高端延伸; 生活性服务业向精细和高品质转变) was coded S0; the outline has 加快/发展 sentences and a named 高技术服务业创新工程 / 放心行动计划.
- Transport: 高速铁路, 城际铁路, 综合交通枢纽 `new` 3 (strongest verb or named hubs); 铁路, 港口航运, 管道运输, 多式联运 `up` (list item at level 1 -> verb or named project); 公路, 邮政业 `up` 2 [borderline] (explicit sentence, no target). 出租车业, 铁路体制改革 coded S0 `new`.
- Energy: 光热发电, 海洋能, 煤电, 国家综合能源基地, 生物燃料 `new` 2; 能源互联网 `new` 3 (dedicated heading with source-grid-load-storage wording). 风电, 光伏, 水电, 核电, 生物质, 地热 wording not stronger than the proposal's 加快发展 list so not recoded.
- 水利 `up` 3: dedicated 第三十一章 plus major diversion and river-lake connection project lists. 节能建筑 `up` 3 (named plan), 海绵城市 and 装配式建筑 `new` 2.
- Finance: 风险投资 and 融资租赁 `new` 3 (大力发展); 创业板与新三板, 小额贷款与融资担保, 金融综合经营, 期货衍生品 coded S0 (regulated development wording); 环境污染责任保险 R-demand 2; 税收递延型养老保险, 出口信用保险 S+ 2.
- Environment: 碳排放交易 `up` 2 (proposal level 1 allocation list); 环保技术装备 `new` 3 (dedicated 第二节 发展环保技术装备); 矿产资源节约与管理 R-demand 3 (dedicated 第四节); 围填海 R-demand 3 (严格控制). 污染企业搬迁关闭 coded `none`/`none`.
- 中药 `up` 3 (dedicated 第六节 促进中医药传承与发展), 创新药 `new` 2, 药品医疗器械审评审批 S0, 药品经营 R-demand.
- Culture: 网络视听与移动多媒体, 数字出版, 动漫游戏 share the same 加快发展 quote (one row per industry); 有线电视 `new` 3.
- 国际产能和装备制造合作 `up` 3 (dedicated 第二节 plus 产能合作项目库); 服务贸易 `up` 3 (大力发展生产性服务贸易); 服务外包, 加工贸易 `new` 2.
- 国防科技工业 `up` 3 (S0 reform wording -> 强基工程 named programme, kept S0 stance because the outline sentence is project-based). 海洋经济 `up` 3 (dedicated 第四十一章第一节); 海洋工程装备 `up` 2; 海洋生物医药 `new` 2.
- Not coded because unchanged: 智能制造, 互联网+, 大数据, 新能源汽车, 节能环保产业 umbrella, 电信, 旅游, 公共交通, 粮食 (the outline adds no target in the extract), 养老服务, 海水淡化, 再生水.
- Concepts coded `none`/`none`: 过剩产能行业, 绿色制造, 消费品工业, 战略性新兴产业, 生产性服务业, 高技术服务业, 生活性服务业, 众创空间, 碳排放交易, 污染企业搬迁关闭, 矿产资源节约与管理, 围填海, 国际产能和装备制造合作, 服务贸易, 海洋经济.

## P14-A2 (十四五纲要, event_date 2021-03-13) vs P14-A1

Extract caveats: clause-level extract of all 19 篇; the extract has no 专栏 boxes (checked by the extractor), so numeric targets that sit in the 专栏 indicator table (e.g. strategic-emerging-industry share, digital-economy share) are not seen. Only targets in body text are coded. Proposal baseline = the non-`dropped` rows of `rows/P14-A1.csv` plus the proposal extract text; concepts that exist only as `dropped` placeholders in that file (e.g. 数控机床, 机器人, 风能, 太阳能, 钢铁, 煤炭, 物流收费) are treated as absent from the proposal and coded `new`.

Calibration for P14 follows `rows/P14-A1.csv`: a sole 加快发展 object or a list item under 加快/推动 = 2; 3 is reserved for a named project/programme/action, a dedicated 节/章 for the concept alone, 大力/优先/坚决/培育壮大/做大做强, or a numeric target in body text.

Judgement calls
- Proposal concepts at level 3 are not recoded when the outline adds only a named programme or the same wording: 战略性新兴产业 (国家战略性新兴产业集群发展工程), 数字经济 (the whole 第五篇), 产业数字化 (上云用数赋智行动; an early `new` row was dropped because the proposal extract has 产业数字化), 制造业, 粮食 (黑土地保护工程, 国家粮食安全产业带; farmland-acreage figures are land targets and not counted), 交通运输, 海洋经济 (dedicated 第三十三章), 水利, 水电, 北斗, 中药, 养老服务, 文化产业, 城市更新, 房地产业 (R-demand 3, outline repeats 不炒 and adds 房地产金融调控), 新能源汽车, 对外贸易.
- Quantitative targets coded `up` at intensity 3 on level-3 or level-2 concepts, flagged [quant]: 电信 (5G penetration 56%), 新能源和可再生能源 (non-fossil share about 20%), 农业机械化 (comprehensive mechanisation 75%), 环保产业 (sludge disposal 90%), 再生水 (wastewater reuse above 25%, `new`). Energy-intensity, water-use, land-use, forest-cover and emission-reduction targets are not counted as industry targets.
- Stance flips (flagged [stance]): 平台经济 S0 -> R-demand 2 `down` (监管 and 垄断认定 sentences; the support clause 支持平台企业创新发展 is in notes); 金融科技 S+ -> S0 `down` ([borderline], 稳妥发展 plus 监管科技 and a suspension mechanism); 中小金融企业 S+ -> S0 `down` ([borderline], governance-reform wording versus 支持…持续健康发展); 生产性服务业 and 生活性服务业 S0 -> S+ `up` 3 (dedicated 第一节/第二节 with 加快发展 lists); 矿产资源开发 S0 -> S+ `up` 3 (新一轮找矿突破战略行动, with the 规划管控 control clause in notes).
- Development versus regulation are kept as different concept names so no spurious reversal arises: 核电建设 (S+) next to the proposal's 核电 (safety supervision, R-demand 1, repeated by the outline); 水产养殖 and 远洋渔业 next to the proposal's 水产业 (长江十年禁渔, repeated); 物业服务监管 next to 物业管理 (S+ list item); 体育产业 next to 体育健身; 化工产业 (modernisation) next to 化工 (hazardous-chemical relocation).
- 煤炭 S0 2 `new`: mixed wording (集中, 煤炭供应安全兜底, 加强煤炭储备能力建设, 合理控制煤炭开发强度 for the Yellow River basin, 清洁高效利用); dominant read S0; 煤电 R-supply 2 (合理控制煤电建设规模和发展节奏) and 高耗能产业 R-supply 3 (坚决遏制) are coded separately.
- Real-estate: 保障性住房 and 住房租赁 `up` 3 [borderline] (the housing-system 节 has about 35 clauses versus two proposal sentences, with 保障性租赁住房, 单列租赁住房用地计划, 住房租赁法规建设); 房地产税 R-demand 2 `new`; 基础设施REITs S0 `new`.
- 畜牧业 `up` 3 (大力发展现代畜牧业 versus a level-1 supply-security list item); 种业 `up` 3 [borderline] (germplasm and seed-bank block, 生物育种产业化应用, 种业龙头企业, but no named programme or number in the extract); 化肥农药 `up` 3 (农药化肥减量行动 named action).
- Finance: 机构投资者 S+ 3 (大力发展); 债券市场, 创业投资, 财富管理 S+; 非银行金融机构, 消费金融, 新三板, 期货, 基金 S0; 互联网金融, 影子银行, 金融控股公司, 环境污染责任保险 R-demand. 证券 (注册制) and 金融业 (零容忍) wording repeats the proposal and is not recoded; 绿色金融 (发展 -> 大力发展) is a verb-tier shift and not coded.
- Industry lists newly naming sectors under generic stances: 第八章 manufacturing list (集成电路 `up` 2 from level 1; 机器人, 轨道交通装备, 电力装备, 工程机械, 数控机床 `new` 2); raw-materials structure adjustment (钢铁, 有色金属, 建材, 石油化工 S0 2); 纺织, 轻工制造, 化妆品, 服装家纺, 消费电子 S+ 2; opening-up lists (教育服务, 医疗服务 S+ 1; 期货, 基金 S0 1).
- Not coded: social-infrastructure and public-service items, regional chapters (京津冀, 长三角, 东北, 中部, 西部, 港澳台 industry lists restate national wording), reform items for 铁路企业, 空管, 公路收费, 国有文艺院团 and 院线, 抽水蓄能 and 新型储能 (the same level as the proposal's 储能), 特色小镇, 都市圈 relocation of general manufacturing and logistics bases out of megacity cores (spatial, no industry stance).
- Concepts coded `none`/`none`: 未来产业, 专利密集型产业, 绿色制造, 生产性服务业, 生活性服务业, 新型基础设施, 智慧城市, 服务贸易, 过剩产能行业, 高耗能产业, 高耗水行业, 矿产资源开发, 绿色矿业, 劳动密集型产业, 技能密集型产业.

## P15-A2 (十五五纲要, event_date 2026-03-13) vs P15-A1

**Extract is PARTIAL.** 第二十六章第二节（后半）, 第二十七章 (强农惠农) and all of 第九篇 (第二十八-三十二章: 区域协调, 国土空间, 新型城镇化, 海洋) are missing from `texts/P15-A2.md`; 第十六篇, 第五十四章 and 第六十一章 were read but name no industry. Nothing is coded as dropped or lower because of a missing part, and no `dropped` rows exist in any outline file. Concepts whose outline wording would sit in the missing parts (e.g. 海洋经济 and 海洋工程装备 chapter wording, 城市更新, 农业保险 and 粮食收储 policy) are simply not recoded here; the proposal's level for them stands. No 专栏 boxes are in the extract. Only body-text numbers are coded.

Calibration follows `rows/P15-A1.csv`: list item = 1, explicit sentence = 2, 3 = named project/programme/base list, dedicated 节/章, strongest verb (大力/做强做优/做精做强/做大做强/发展壮大), or numeric target.

Judgement calls
- Quantitative targets (flagged [quant]): 粮食 `up` 3 (about 1.45 trillion jin capacity), 能源 `up` 3 ([stance]: proposal S0 umbrella, outline 58亿吨标准煤 output capacity), 农业机械化 `up` 3 (80%+ comprehensive mechanisation), 油气产量保障 `new` 3 (crude output about 200 million tonnes). Resource-use, emission and carbon targets are not counted.
- Named base or completion lists coded `up` 3 [project-list]: 风能, 太阳能, 水电, 核电 (the 清洁能源基地 sentence, versus level-1 list items in 风光水核 多能并举), 铁路 and 港口航运 ([borderline]: completion of the eight-vertical, eight-horizontal rail network and world-class port/airport clusters), 船舶, 海洋工程装备 and the new 钢铁 and 石化 rows (做强做优 base sentence), 对外承包工程 (中吉乌铁路, 匈塞铁路), 物流 ([borderline], 国家物流枢纽网络).
- Stance flips: 生产性服务业 and 生活性服务业 S0 -> S+ `up` 3 (dedicated 节 with 大力发展 / 加快补齐 verbs); 能源 S0 -> S+. 低空经济 `down` 2 ([borderline]): out of the 加快…战略性新兴产业集群发展 list into 健康有序发展 plus airworthiness and safety clauses.
- 内卷式竞争 R-supply `up` 3 (dedicated 第三节 with 产能监测预警机制, 产能调控, 价格治理); 高耗能产业 R-supply `up` 3 (碳排放等量或减量置换 for new projects); 过剩产能行业 R-supply `new` 2; 高风险工艺装备淘汰 R-supply `new` 2.
- Sections and named programmes: 新型基础设施 and 算力 `up` 3 (dedicated 节, 东数西算工程), 区块链 `new` 3 (国家区块链网络建设工程), 智能制造 `up` 3 (智能制造工程), 未来产业 `up` 3 (未来产业发展示范工程), 水利 `up` 3 (dedicated 第三节 加快建设现代化水网), 中药 `up` 3 (dedicated 第四节, 做大做强), 养老服务 and 银发经济 `up` 3 (dedicated 节; 大力发展 for 银发经济), 康复护理 `up` 3 (康复护理扩容提升工程; the supply clause is in the proposal text but has no row in the proposal CSV), 药品 `up` 3 (药品标准提高行动计划), 食品 `up` 3 (dedicated 第一节 强化食品药品安全监管), 网络安全 `up` 3.
- Strategic emerging industries: the outline's 加快 list newly names 新一代信息技术, 智能网联新能源汽车, 机器人, 生物医药 and 高端装备; coded `new` 3 (高端装备制造 `up` 3 from the proposal's technology-breakthrough clause at level 2). 新能源, 新材料, 航空航天 were already level 3 and are not recoded. 国产大飞机, 北斗卫星导航, 智能驾驶 `new` 2.
- Real-estate: 房地产业 S0 level 3 is unchanged (新模式, 基础制度 wording repeats; 好房子, 改善性住房, 物业管理 repeat the proposal and are not recoded). Coded: 保障性住房 `up` 3 ([borderline], same S0 stance, dedicated 完善住房保障体系 with whole-process management), 住房租赁 S0 `new`, 现房销售 R-demand `new`.
- Development versus regulation kept as different concept names: 水产养殖 vs 水产业 (长江十年禁渔 repeated), 体育产业 vs 体育健身, 旅游监管 vs 旅游, 油气产量保障 vs 石油天然气 (the proposal's R-demand row is the oil consumption peak, repeated by the outline), 电价市场化改革 and 油气价格改革 as S0 reform rows.
- Not coded because unchanged: 集成电路 and the 全链条 breakthrough list, 平台经济 (监管 and 创新健康发展 wording repeats), 金融业 and the 科技金融/绿色金融/普惠金融 list, 期货, 数字货币, 证券, 中小金融企业, 碳排放交易, 煤炭 and 石油 consumption peak, 种业振兴行动, 设施农业, 林业, 托育服务, 创新药 sub-clauses other than the combined row, 风险投资 (大力发展 versus 发展 is a verb-tier shift), 数字贸易, 跨境电商, 服务贸易, 民办教育, 职业教育, 国防科技工业, 军民融合, 绿色金融.
- Rows removed after a check against the proposal text: 绿色制造 (named in the proposal's 智能制造 clause) and 供水 (inside 水网 wording).
- Concepts coded `none`/`none`: 能源, 内卷式竞争, 过剩产能行业, 高耗能产业, 生产性服务业, 生活性服务业, 未来产业, 新型基础设施, 老字号与国货品牌, 垄断行业, 绿色矿业, 高风险工艺装备淘汰.

## Final notes (all five outlines)

- Hygiene checks run after drafting: every `new` row's concept name was searched in the proposal text; false-new cases found and corrected (P14-A2 产业数字化 dropped; P15-A2 绿色制造 and 供水 dropped, 康复护理 changed to `up`; P13-A2 物流 changed from `new` to `up` against the proposal's 物流 list mention 推动融资、商贸、物流、专业服务等向高端高增值方向发展). P11-A2 信息安全 and 南水北调 stay `new`: the proposal only has 健全信息安全保障体系 (a security system, no industry) and 南水北调 as a pollution-control area.
- Several `up`/`down` rows use a proposal quote that has no row of the same concept name in `rows/P1x-A1.csv` (the proposal clause is in the extract text but was coded under another name or not coded). The prev quote is always an exact substring of the proposal extract.
- Concept names are chosen to chain with the proposal CSV where the object is the same; where the outline adds development of something the proposal only regulated (or the reverse), a different name is used so that the later merge does not create a spurious pivot.
