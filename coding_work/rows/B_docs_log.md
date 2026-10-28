# B_docs_log — judgement calls, seed list B (non-plan documents), second batch

Files covered: B05j, B06-B13, B27a, B27b, B28, B29, B30a, B30b, B31, B32, B33a, B33b, B34, B35, B36, B37
(rows written with `tools_b/common_b.py`; every `quote_zh` is a verbatim substring of its extract and at most 40 characters).
All `quote_en` fields are [unofficial translation]. Coded blind from the words alone (protocol section 0).

## Conventions applied to every file
- doc_type = other; change_vs_prev = na; prev_quote_zh empty; event_date = `publication_date` in the extract header; source_url = first `fulltext_urls` entry.
- One row per industry concept. Broad concepts (strategic emerging industries, traditional industries, digital economy, future industries, marine economy, cross-sector programmes) have sw_l1 = sw_l2 = none. Fiscal tools (特别国债, 专项债), local-government debt and non-industry items (e.g. 民营经济促进法) are not coded.
- Stance where a sentence mixes verbs: dominant stance in the row, the other side in notes. 稳步/有序/规范/引导 alone = S0; 积极稳妥 mixed with an expansion aim = S+ (noted).
- Intensity: 3 = named programme / quantitative target / dedicated chapter or headline verb with a drive word; 2 = standalone sentence with a clear verb (大力发展 is 2 unless it is the headline or a named programme, matching existing rows such as B29 and B27b); 1 = tail item of a list or passing mention. Where a list of several concepts is the only object of a sentence verb (B33a key-chain sentence), each item gets 2; where the list sits inside a longer sentence about a broader concept (B33a strategic-field list, B33b service consumption, B37 technology lists) the items get 1.
- Supply-assurance wording (保供, 保供稳价) = S0, not expansion (B33b, B34).
- Items in a split sentence that restrict one thing and support another are separate concepts, e.g. B34 房地产市场 (S+) versus 商品房新增供给 (R-supply); B35 房地产市场 (S+) versus 房地产用地供应 (R-supply). They share an SW code on the same date; the merge script handles same-date events without counting them as earlier.
- Trade modes (外贸新动能, 服务贸易) were mapped to 贸易Ⅱ (801202) at intensity 1; this is a judgement because they are not industries.

## Judgement calls by document
- B05j (logistics plan): quotes only from sections 一 to 三. Sections 四 and 五 of the extract were not clause-checked by the earlier extractor and none of my quotes come from them.
- B06: 现代煤化工 coded R-supply (three-year freeze on new pilots), the 稳步开展…示范 clause in notes. 多晶硅 mapped to 光伏设备. Generic rows 产能过剩行业 and 新兴产业 have no SW code.
- B07: 保障性安居工程 S+ 3 (quantified target, own section); housing-price control rows R-demand. Section headings and item mapping were corrected after a verification fetch.
- B08: 26 rows, all S+ (seven fields plus sub-industries). 风电 coded S+ although 有序推进 appears (aims are expansionary).
- B10: 节能汽车 coded S0 because the main instrument is a fuel-consumption management measure with targets; electrified vehicles S+.
- B11-B13: published on gov.cn as abridged (此件有删减); coverage limited to the published text. B12 date: the gov.cn zwgk page header shows 2013-08-11 16:00 (corroborated by a law-firm update); the zhengceku library shows 2013-08-12. The earlier date is used and the difference is in the extract header.
- B27a/B27b: 核电 is S+ in the Party-State opinion (B27a, 积极…有序) and S0 in the State Council plan (B27b, 有序发展…平稳建设节奏). 石油消费 R-demand despite neutral 合理区间 because of 逐步调整汽油消费规模. CCUS and 氢能 have no SW industry (CCUS mapped to 环保 at L1 only).
- B29: 平台经济 coded S+ 3 (support dominant), the supervision clause in notes; contrast B24b (R-demand).
- B30b: 房地产市场 S+ 2 despite 平稳健康发展 wording.
- B32: 资本市场发行上市与上市公司监管 R-demand 3 (strict-entry, supervision, delisting); support clauses (并购重组, 权益类公募基金) in separate rows.
- B33a (64 rows): 三中全会 decision. 房地产市场 coded S0 3 (reform wording: new development model, 开发融资方式和预售制度, tax system), easing of 限购 recorded in notes; 保障性住房 S+ 3 separate. 平台经济 S+ 2 (promotion first, regular supervision in notes). 人工智能 coded R-demand 2 on the explicit sentence 建立人工智能安全监管制度, outranking its intensity-1 mention in the strategic-field list. Eight strategic fields at intensity 1, the key-chain items (集成电路, 工业母机, 仪器仪表, 基础/工业软件, 先进材料, 医疗装备) at 2. 战略性矿产资源 mapped to 小金属. 民办教育 and 民营医院 S0 (引导规范). 能耗双控 to 碳排放双控 R-demand. 金融业监管/防火墙 R-demand, none.
- B33b: 内卷式恶性竞争 R-supply 2 (防止, via 行业自律) - first appearance of the phrase among the B documents. 房地产市场 S+ 2 (the support clause 积极支持收购存量商品房 dominates the S0-type 平稳健康); 资本市场 S0 (balanced: 强监管 and 提振信心); 能源电力保供 S0 1; 污染防治 mapped to 环境治理 at 1.
- B34: 房地产市场 S+ 3 (止跌回稳), 商品房新增供给 R-supply 2 (严控增量), 白名单项目贷款 S+ 2. 养老托育产业 S+ (支持和规范; support leads and the aim is expansion, regulation in notes). 资本市场 S+ 3, 公募基金 S0 1.
- B35: 内卷式竞争 R-supply 3 (综合整治; B33b used 防止 at 2). 平台经济 S0 2 (加强监管 plus 促进健康发展, balanced; B29 had S+). 地方中小金融机构 R-demand 2 (risk resolution is regulatory action; 稳妥 soft). 房地产市场 S+ 3 (持续用力). 海洋经济与湾区经济 S+ 2. 首发/冰雪/银发经济 three rows from one sentence.
- B36: the word 内卷 does not occur; 依法依规治理企业低价无序竞争 coded R-supply 3 (the clause pairs governance with 落后产能有序退出). 海洋经济 S+ 3 (meeting theme); 海上风电 S0 (规范有序); 沿海港口群 S0 (有序).
- B37 (33 rows): 人工智能 S+ 3 (named State Council action); 新一代智能终端 S+ 3 (adoption targets above 70% by 2027 and above 90% by 2030); 算力 S+ 3 (东数西算 named programme). Technology-list items (元宇宙, 增材制造, 脑机接口, 生物制造, 量子科技, 6G, 低空飞行) intensity 1, one row each from the same quote. 医疗 and 市政基础设施 S0 (有序).

## Borderline SW mappings (judgement, never made with reference to market data)
物流 sub-concepts in B05j (医药物流 to 医药商业; 国际物流 to 航运港口); 仪器仪表 to 自动化设备; 战略性矿产 to 小金属; 好房子 to 房地产开发 plus 房屋建设; 城中村改造 to 房屋建设; 公募基金 and 资本市场融资 to 证券Ⅱ; REITs and 期货 to 多元金融; 冰雪经济 and 海洋旅游 to 旅游及景区; 智能农机 to 专用设备; 智能制造装备 to 专用设备 plus 自动化设备; 算力 to 计算机设备 plus IT服务; 海洋生物医药 to 化学制药 plus 生物制品; 地方中小金融机构 to 城商行 plus 农商行; 节能服务业 to 环境治理.

## Concepts coded none (no single SW industry)
Generic: 产能过剩行业, 高耗能高排放行业, “两高”项目, 战略性新兴产业, 新兴产业, 未来产业, 传统产业, 数字经济, 现代服务业, 新质生产力, 内卷式竞争, 低价无序竞争, 海洋经济, 绿色低碳产业, 服务业开放, 制造业外资准入, 设备更新与以旧换新, 新型消费. No SW equivalent: 氢能, 量子科技, 生物制造, 元宇宙, 脑机接口, 专精特新企业, 瞪羚/独角兽企业, 首发经济, 非法金融活动, 碳市场.

## Documents and extraction
All eight Part 2 documents (B06-B13) were found on gov.cn and extracted (two-pass verbatim check). None missing. First-publication dates: B06 2009-09-29, B07 2010-04-17, B08 2010-10-18, B09 2011-02-09, B10 2012-07-09, B11 2013-07-15, B12 2013-08-11, B13 2013-10-15.
