# Blind coding protocol v1 — policy wording → industry events

Frozen: 2026-10-26 (before any price data is joined to any event).
Owner: coding agent (separate from the backtest agent).

## 0. Blindness rules (read first)

1. Code **only from the text of the documents**. Do not look up, open, or consider any stock price, index level,
   fund flow, earnings, or any other market outcome after a document's date. Do not open any file under
   `/tmp/claude-0/` or any folder named `data` — those hold price data and are off-limits to you.
2. You will remember how some industries performed later (e.g. which sectors boomed or crashed). That memory is
   exactly the bias this study is trying to remove. Ignore it. Code the words as written on the day they were
   published, the same way for famous and obscure industries.
3. Code **exhaustively**: every industry / sector that receives specific wording in a document's economic and
   industrial chapters gets a row — not just the well-known ones. Do not drop an industry because it seems
   unimportant or because you think nothing happened to it.
4. If a judgement call is needed, apply the rubric below and write the reason in `notes`. Never resolve a call by
   thinking about later market performance.

## 1. Document universe

### A. Five-year plans — complete universe (primary test)
For each plan: 十五 (2001–05), 十一五 (2006–10), 十二五 (2011–15), 十三五 (2016–20), 十四五 (2021–25), 十五五 (2026–30):
- **A1 建议**: 中共中央关于制定…五年计划/规划的建议. `event_date` = the date the full text was first published
  (Xinhua / People's Daily), not the plenum date if they differ. Verify the date from a dated source.
- **A2 纲要**: 国民经济和社会发展第…个五年计划/规划纲要. `event_date` = date the full text was first published
  (usually 1–3 days after NPC approval in March).
Code A1 fully. For A2, add a row only where the outline's wording for a concept **materially differs** from A1
(stronger/weaker stance, a new quantitative target, a concept not in A1). Mark those rows `doc_type=FYP_outline`.

### B. Other national-level industry documents — seed list (secondary, exploratory)
Inclusion criteria: issued or approved by the CPC Central Committee, State Council (incl. 国发/国办发),
the Politburo, the Central Economic Work Conference (CEWC), or the Central Financial and Economic Affairs
Commission; or a ministry document that was explicitly approved by one of those bodies; **and** explicitly
targeting named industries. Seed list (verify each date and title; drop any you cannot verify):

| id | approx. date | document |
|---|---|---|
| B01 | 2000-06 | 国发〔2000〕18号 鼓励软件产业和集成电路产业发展的若干政策 |
| B02 | 2003-12 | 国办发〔2003〕103号 制止钢铁电解铝水泥行业盲目投资若干意见 |
| B03 | 2006-02 | 国发〔2006〕8号 关于加快振兴装备制造业的若干意见 |
| B04 | 2006-03 | 国发〔2006〕11号 关于加快推进产能过剩行业结构调整的通知 |
| B05 | 2009-01/02 | 十大产业调整和振兴规划 (汽车、钢铁、纺织、装备制造、船舶、电子信息、轻工、石化、有色金属、物流) — one row per industry, dated by each plan's publication |
| B06 | 2009-09 | 国发〔2009〕38号 抑制部分行业产能过剩和重复建设 |
| B07 | 2010-04 | 国发〔2010〕10号 坚决遏制部分城市房价过快上涨（国十条） |
| B08 | 2010-10 | 国发〔2010〕32号 加快培育和发展战略性新兴产业的决定 |
| B09 | 2011-01 | 国发〔2011〕4号 进一步鼓励软件产业和集成电路产业发展的若干政策 |
| B10 | 2012-06/07 | 国发〔2012〕22号 节能与新能源汽车产业发展规划（2012—2020年） |
| B11 | 2013-07 | 国发〔2013〕24号 关于促进光伏产业健康发展的若干意见 |
| B12 | 2013-08 | 国发〔2013〕30号 关于加快发展节能环保产业的意见 |
| B13 | 2013-10 | 国发〔2013〕41号 关于化解产能严重过剩矛盾的指导意见 |
| B14 | 2014-06 | 国家集成电路产业发展推进纲要 |
| B15 | 2015-05 | 国发〔2015〕28号 中国制造2025 |
| B16 | 2015-07 | 国发〔2015〕40号 关于积极推进"互联网+"行动的指导意见 |
| B17 | 2016-02 | 国发〔2016〕6号 钢铁行业化解过剩产能；国发〔2016〕7号 煤炭行业化解过剩产能 |
| B18 | 2016-12 | 中央经济工作会议（"房子是用来住的、不是用来炒的"） |
| B19 | 2017-07 | 国发〔2017〕35号 新一代人工智能发展规划 |
| B20 | 2018-11 | 国家组织药品集中采购试点（"4+7"），经中央全面深化改革委员会审议 |
| B21 | 2020-08 | 重点房地产企业资金监测和融资管理规则（"三条红线"） |
| B22 | 2020-09 | 碳达峰、碳中和目标宣布（第七十五届联合国大会一般性辩论） |
| B23 | 2020-11 | 国办发〔2020〕39号 新能源汽车产业发展规划（2021—2035年） |
| B24 | 2020-12 | 中央政治局会议/中央经济工作会议（"强化反垄断和防止资本无序扩张"） |
| B25 | 2021-02 | 国务院反垄断委员会关于平台经济领域的反垄断指南 |
| B26 | 2021-07 | 中办国办 关于进一步减轻义务教育阶段学生作业负担和校外培训负担的意见（"双减"） |
| B27 | 2021-10 | 中共中央 国务院 关于完整准确全面贯彻新发展理念做好碳达峰碳中和工作的意见；国发〔2021〕23号 2030年前碳达峰行动方案 |
| B28 | 2022-11 | 关于做好当前金融支持房地产市场平稳健康发展工作的通知（"金融16条"） |
| B29 | 2022-12 | 中央经济工作会议（支持平台企业、房地产等表述） |
| B30 | 2023-07 | 中共中央 国务院 关于促进民营经济发展壮大的意见；7月24日中央政治局会议 |
| B31 | 2024-03 | 国发〔2024〕7号 推动大规模设备更新和消费品以旧换新行动方案 |
| B32 | 2024-04 | 国发〔2024〕10号 关于加强监管防范风险推动资本市场高质量发展的若干意见（"新国九条"） |
| B33 | 2024-07 | 二十届三中全会决定；7月30日中央政治局会议（"防止内卷式恶性竞争"） |
| B34 | 2024-09 | 9月26日中央政治局会议（"促进房地产市场止跌回稳"） |
| B35 | 2024-12 | 中央经济工作会议（"综合整治内卷式竞争"等） |
| B36 | 2025-07 | 中央财经委员会第六次会议（"依法依规治理企业低价无序竞争"） |
| B37 | 2025-08 | 国发〔2025〕11号 关于深入实施"人工智能+"行动的意见 |

You may add documents that meet the inclusion criteria (e.g. 2026 documents after the 十五五 outline), at most
10 additions, each with a one-line reason in `notes`. Additions must be justified by issuer and explicit industry
targeting — never by how markets reacted.

### C. Government Work Report first appearances (optional module, do after A and B)
For 2015–2026 政府工作报告: code only **first appearances** of a new industry term (e.g. a term never used in any
earlier GWR or FYP document) with `doc_type=GWR_first`. Use the report's delivery date.

## 2. Coding unit and fields

One row per (document, industry concept). Output CSV columns (UTF-8, header row, this order):

`event_id, doc_id, doc_name, doc_type, issuer, event_date, concept_zh, concept_en, sw_l1, sw_l2, stance, intensity,
change_vs_prev, pivot, quote_zh, quote_en, prev_quote_zh, source_url, notes`

- `doc_type`: FYP_proposal | FYP_outline | other | GWR_first
- `concept_zh/en`: the industry as the document frames it (e.g. 光伏 / solar PV; 集成电路 / integrated circuits).
- `sw_l1`, `sw_l2`: best-matching codes from `sw_taxonomy.csv` (SW2021). `sw_l2` may hold several codes separated by
  `;` when the concept spans them. Use the narrowest code(s) that cover the concept. If no SW code fits, write `none`.
  Map by what the concept is, not by which index you expect to have moved.
- `stance` (exactly one):
  - `S+` 扶持/扩张 — 大力发展、加快发展、培育壮大、积极发展、重点发展、支柱产业、战略性新兴产业、未来产业、前瞻布局、做大做强、打造…集群
  - `S0` 中性/规范 — 有序发展、适度发展、积极稳妥、规范发展、引导、合理布局、稳步推进
  - `R-supply` 供给约束 — 淘汰落后产能、严格控制新增产能、化解过剩产能、压减、禁止新建、治理低价无序竞争、防止内卷式竞争
  - `R-demand` 需求/监管约束 — 抑制投机、调控、房住不炒、整治、规范收费、反垄断、防止资本无序扩张、严格限制、不得
  - If both support and restriction appear for the same concept in one document, code the dominant one and write
    the other in `notes`.
- `intensity`: 3 = strongest wording or a named national programme / quantitative target / dedicated chapter;
  2 = explicit sentence with a clear verb; 1 = passing mention in a list.
- `change_vs_prev` (FYP rows): compare with the same concept in the previous plan's 建议 →
  `new` (first appearance), `up` (stronger stance or intensity), `same`, `down` (weaker), `dropped` (was in the
  previous plan, absent now — add a row for it with stance `S0`, intensity 1, quote `（未提及）`), `na` (十五 baseline
  or non-FYP rows).
- `pivot`: 1 if this row reverses direction relative to the concept's most recent prior coded stance in any document
  (support ↔ restriction); else 0.
- `quote_zh`: the exact key phrase as published, ≤ 40 汉字. Verify it against the source text; do not paraphrase.
- `quote_en`: a faithful translation of `quote_zh` (mark `[unofficial translation]` once in notes for the file).
- `prev_quote_zh`: the previous plan's wording for the concept (FYP rows), else empty.
- `source_url`: an official or reputable full-text source you actually opened.

## 3. Deliverables (write to `/home/claude/policy_bt/events/`)

1. `events_v1.csv` — the event table above.
2. `documents_v1.csv` — `doc_id, doc_name, doc_type, issuer, event_date, source_url, date_source, verified`.
3. `coding_log.md` — judgement calls, documents dropped and why, additions and why, known gaps.

When finished, compute `sha256sum` of `events_v1.csv` and `documents_v1.csv` and write them to
`/home/claude/policy_bt/events/FROZEN.sha256`. After that, the files must not change.
