# FYP proposals coding log (stage 2)

## P14-A1 and P15-A1 (coded 2026-10-27; this agent took over after P10–P13-A1)

Inputs: extracts `texts/P13-A1.md`, `P14-A1.md`, `P15-A1.md` and the frozen rows `P13-A1.csv` (P12-A1.csv skimmed for calibration).
Output: `rows/P14-A1.csv` (163 rows, compared with P13-A1) and `rows/P15-A1.csv` (165 rows, compared with P14-A1).
Every `quote_zh` was checked by script as an exact substring of the extract (one flagged exception, below) and as ≤ 40 汉字. For continuing concepts, `concept_en` and the SW codes were copied from the previous plan's row. `prev_quote_zh` is the previous row's `quote_zh`. A `dropped` row was added for every non-dropped concept in the previous plan's rows that has no counterpart. Helper scripts were kept in `/home/claude/stage2_tmp/`, outside `/tmp/claude-0/`, the folder the blindness rules put off-limits; that folder includes the default scratchpad.

### Calibration carried over from P12/P13
- Strategic-emerging-industry list members get intensity 3 when the list is explicitly designated 战略性新兴产业 inside its own numbered item (as in 十二五). In 十三五 they got 1 (undesignated 6-item list). P14 item 12 and P15 item （8） both qualify, so several P14 SEI rows are `up` against P13.
- I applied the same rule to the P15 未来产业 list (量子科技、生物制造、氢能和核聚变能、脑机接口、具身智能、第六代移动通信): designated in its own item → 3. This is a judgement call by analogy.
- Long lists with an ordinary verb → 1. Short lists (about 3 items) with a clear verb → 2. 大力 with a sole object → 3. A named 工程 / 行动 / 战略 / 试点 or a quantitative target → 3. Key-technology / frontier S&T lists stay 1, even P15's 全链条推动…取得决定性突破, which is strong wording but a list.
- An "X强国" goal stated in its own sentence (交通强国, 海洋强国, 体育强国, 金融强国, 农业强国) → 3. When the goal appears only inside the part-headline list (制造强国、网络强国、航天强国、交通强国), it supports the intensity 3 of a concept that already has other wording (制造业, 电信, 航空航天, 交通运输). 体育强国 in the 2035-vision list was not used for P14.
- `change_vs_prev` when the stance changes (convention inherited from P13): S0→S+ and S0→R = `up`; S+→S0 and R→S0 = `down`; S+→R = `down` (as P13 水产业); R→S+ = `up`. The merge script computes `pivot` mechanically, so these labels only describe the direction of the change.
- "促进…健康发展" (平台经济, 共享经济) and "引导规范…" → S0. An explicit "支持…" (支持中小银行和农村信用社持续健康发展, 支持和规范民办教育发展) → S+, with the 规范 component noted. Quality-upgrading wording (…向高品质升级, 物业服务质量提升行动) → S0, following P13's "upgrading wording" practice.
- Safety regulation naming an industry → R-demand, as P13 coded 食品安全战略. This gives P14 核电 (加强核安全监管, R-demand 1, `down` and a reversal from S+), 矿山 and 建筑业 (safety-accident list, R-demand 1), 食品, and 化工 (危化品搬迁改造).

### P14 judgement calls
- 房地产业: 坚持房子是用来住的、不是用来炒的定位 → R-demand 3, matching B18/B24b. 促进房地产市场平稳健康发展 and 促进住房消费健康发展 (S0) are in notes.
- 药品: 推进国家组织药品和耗材集中采购使用改革 → R-demand 3 (as B20b). 医用耗材 is a separate new row (R-demand 3). 医疗器械 (发展高端医疗设备) is S+2, because the document frames consumables and equipment differently.
- 垄断行业: 打破行业垄断 (R-demand 2) is coded as dominant over the market-reform sentence for 能源、铁路、电信、公用事业 (S0 2).
- 电力: the 十三五 carbon-control list (R-supply) is not repeated, and P14 has only layout wording → S0 2, `down`.
- 林业: only 推行草原森林河流湖泊休养生息 (use restraint) → R-supply 1. 国土绿化 and 林长制 are ecological wording and were not coded.
- 水产业: 实施好长江十年禁渔 → R-supply 3, `up` (same direction as 退养还滩).
- 旅游: several supportive clauses but no 大力 → 2, `down`. 传统工艺: 保护和传承 → S0 2, `down`.
- 汽车: 推动汽车等消费品由购买管理向使用管理转变 sits under 全面促进消费 and eases purchase restrictions → S+2. It could be read as S0.
- 军民融合: the term is not used. Item 54 促进国防实力和经济实力同步提升 is coded as its successor framing (S+2, `down`). Weapons-modernisation wording is mapped to 国防科技工业 (as P12 did), giving S0 → S+.
- 中小银行 is coded under the existing concept name 中小金融企业 (from 十一五), and 第五代移动通信 under 电信. 新型基础设施 gets its own broad row (none); its components are coded under 电信, 工业互联网 and 大数据.
- 互联网+: 推动互联网、大数据、人工智能等同各产业深度融合 is coded as its counterpart (S+2, `down`; no named plan).
- 棉花 / 油料 / 糖料 get three separate S+1 rows from 保障粮、棉、油、糖、肉等重要农产品供给安全 (exhaustive rule). 肉 → 畜牧业.
- I did not code the 进口博览会 trade-fair platform, 自由贸易试验区, 人民币国际化, the 碳达峰 action plan (no industry named), the 冬奥会 event, or land-system reforms.

### P15 judgement calls
- Source check (allowed by stage-2 §1): the extract cuts item （8） with "…", so I re-opened the Xinhua URL for the context of items （7） and （8）. It confirmed the SEI list is 新能源、新材料、航空航天、低空经济 only, so 新一代信息技术, 生物产业 and 新能源汽车 are coded `dropped`. The item opens with 着力打造新兴支柱产业 (noted under 战略性新兴产业). The cut clause also contains 发展创业投资, which is coded as 风险投资 S+2 `new` with that **source-verified quote**. This is the only `quote_zh` not taken from the extract, and it is flagged `[source-verified quote]` in notes.
- 房地产业: own item （41）, framed as 推动房地产高质量发展 / 加快构建房地产发展新模式 → S0 3, `down` from R-demand 3. Its S+ components are 改善性住房 (new row, S+2) and 清理…住房等消费不合理限制性措施. Its R-demand component is 房地产…风险有序化解. 好房子 / 房屋品质提升工程 is a new S+3 row.
- Traditional-industry list (巩固提升矿业、冶金、化工、轻工、纺织、机械、船舶、建筑等产业…竞争力) → S+1 each. This reverses the P14 safety/relocation R-demand codes for 矿山 (矿业), 化工 and 建筑业 (R→S+, `up`). 机械 → 装备制造业. 冶金 and 轻工 / 纺织 reuse or split earlier names (十一五 冶金, 十五 轻纺).
- 石油天然气: 推动煤炭和石油消费达峰 → R-demand 2 (reversal from S+). 煤炭 reappears as R-demand 2. 行业碳管控 is coded under 高耗能产业 (R-supply 2; borderline concept match).
- 风光水核等多能并举 → S+1 each for 风能、太阳能 (reappear), 水电 (`down` from a named project), and 核电 (`up`, reversal from R-demand).
- 药品: 优化药品集采… → R-demand 2 (`down`). 创新药 is a separate new S+2 row. 中小金融企业: 中小金融机构…风险有序化解 → R-demand 2 (reversal from S+).
- 物业管理: 物业服务质量提升行动 is a named action but quality-upgrading wording → S0 3, coded `down` because the stance moved S+→S0 while intensity rose. 养老服务 → S+2 `down` (no named national strategy in this item). 托育服务 → S+3 `up` (托育服务补助示范试点).
- 内卷式竞争: 综合整治"内卷式"竞争 with no industry named → new broad row (none), R-supply 2.
- Successor mappings: 量子科技 → 量子信息; 数字金融 → 金融科技; 数字人民币 → 数字货币; 教育数字化战略 → 现代远程教育; 防治康管全链条服务 → 健康产业; 重大技术装备 → 高端装备制造; 城乡建设绿色低碳转型 → 节能建筑; 一体化国家战略体系 / 新质生产力同新质战斗力融合 → 军民融合.
- 中欧（亚）班列 → 铁路 (S+2, `down`). 西部陆海新通道 → 物流. 现代化水网 → 水利, coded 2 (not framed as a named major project).
- I did not code Hong Kong/Macao/Taiwan wording (as P13), 地方政府债务 (fiscal, not an industry), 专精特新 / 独角兽 firm support (seen only in the source-check summary, not verbatim), or 应用场景 / 消费新场景.

### Borderline SW mappings
- 智慧农业 → 801750/801103 (as P13 智慧城市); could be 801010.
- 量子信息 → 801770;801750 / 801102;801101.
- 北斗卫星导航 → 801740;801770 / 801741;801745;801102.
- 城市更新 → 801720 / 801721;801723; could be 801180.
- 好房子 → 801720;801180 / 801721;801181. 海绵城市 → 801720/801723.
- 智慧能源系统 → 智能电网 (801730/801738).
- 线上线下消费融合 → 电子商务 (801200/801206).
- 研发设计 → 801210/801218.
- 网络安全 → 801750 / 801104;801103.
- 金融科技 → 801790;801750 / 801191;801103. 科技金融 → 801780;801790 / 801191. 普惠金融 → 801780;801790 (no L2). 养老金融 → 801790 / 801194;801191.
- 塑料制品 (白色污染治理) → 801030/801036.
- 矿山 → 801950;801050 / 801951;801055.
- 糖料 → 801016 (farm-supply framing).
- 低空经济 → 801740;801170 / 801742;801991 (as 通用航空).
- 生物制造 → 801030;801150 / 801034;801152.
- 氢能 → 801730/801733. 核聚变能 → 801160/801161. 脑机接口 → 801150/801153. 具身智能 → 801890/801078.
- 算力 → 801750 / 801101;801103.
- 仪器仪表 → 801890 (L1 only; no clear L2).
- 平台经济 → 801200/801206 (as B24b/B25). 工业互联网 → 801750/801103 (as B15). 人工智能 → 801750 / 801103;801104 (as B16).

### Concepts coded `none` (broad concepts or not an SW industry)
- P14: 制造业、设备更新和技术改造、战略性新兴产业、互联网+、数字经济、分享经济、新型基础设施、现代服务业、生产性服务业、生活性服务业、服务业、银发经济、垄断行业、海洋经济、能源、碳排放交易、数字货币、传统工艺、矿产资源开发. Dropped rows that inherit `none`: 过剩产能行业、劳动密集型产业、资本和技术密集型产业、政府和社会资本合作、众创空间、高耗能产业、服务贸易.
- P15: 新质生产力、制造业、战略性新兴产业、未来产业、高新技术产业、数字经济、新型基础设施、服务业、生产性服务业、生活性服务业、现代服务业、银发经济、海洋经济、能源、高耗能产业、碳排放交易、数字货币、服务贸易、数字贸易、矿产资源开发、内卷式竞争. Dropped rows that inherit `none`: 设备更新和技术改造、互联网+、分享经济、垄断行业、传统工艺.

[unofficial translation] applies to all `quote_en` (marked in the first row's notes in each file).
