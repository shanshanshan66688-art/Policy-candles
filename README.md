# 国策K线 · Policy Candles

二十五年来，六部五年规划和数十份产业政策文件怎样描述各个行业？这些措辞之后，申万行业指数又怎样走？跟着政策买，胜率究竟多少？

**交互页面：** https://shanshanshan66688-art.github.io/policy-candles/ （中英双语，可回放的行业月K线、五年计划逐期追踪、盲测回测结果）

English summary below.

---

## 结论

主检验（事先登记）：按五年规划**建议**中的「扶持」措辞，在全文发布后的第一个月末买入对应申万行业指数，持有 36 个月，与申万A指比较。

| 检验 | 样本 | 胜率 | 平均超额 | 随机换行业（中位数） | p 值 |
|---|---|---|---|---|---|
| 扶持 · 五年规划建议 · 36 个月（主检验） | 279 次 / 5 部建议 | 44.4% | −1.0% | 45.5% | 0.71 |
| 扶持 · 五年规划建议 · 12 个月 | 371 次 / 6 部建议 | 34.2% | −3.9% | 45.8% | 1.00 |
| 扶持 · 规划建议与纲要 · 36 个月 | 581 次 | 46.8% | +3.7% | 45.8% | 0.26 |
| 扶持 · 专项文件 · 36 个月（探索性） | 260 次 | 50.0% | +1.8% | 51.0% | 0.67 |
| 回避「需求/监管约束」· 36 个月 | 73 次 | 52.1% | 被约束行业 +5.8% | 50.7% | 0.46 |

- **扶持没有变成超额收益。** 被五年规划点名扶持的行业，三年后跑赢的概率与随机挑行业相当；第一年甚至系统性落后。落后是事后观察到的，预登记只检验了「跑赢」方向，只作探索性结论。
- **约束也没有标出输家。** 被需求/监管约束点名的行业，三年平均反而跑赢；「扶持多、约束空」组合年化 −3.6%。
- **唯一亮点是描述性的。** 持续持有所有出现过扶持措辞的行业 36 个月（组合 P2），年化超额 3.5%、信息比率 0.36；但单个事件中位数为负，收益集中在少数大赢家，且没有预登记显著性检验。
- **发布前后没有看到资金涌入。** 扶持行业在建议发布前 3 个月平均落后 2.6%，发布后一年成交额占全A比例下降 0.38 个百分点。

完整数字见 [`backtest/report.md`](backtest/report.md) 与 [`backtest/results.json`](backtest/results.json)。

## 方法：避免「揣着答案做题」

1. **预登记**（[`prereg/`](prereg/)）：编码规则、分析计划、胜负标准、安慰剂检验在任何事件被编码、任何行情被关联之前写定，并记录 SHA-256 与时间（[`prereg/PREREG.sha256`](prereg/PREREG.sha256)）。之后的补充说明同样先于结果写定、单独记录。
2. **逐字摘录**（[`coding_work/texts/`](coding_work/texts/)）：多个 agent 读取官方原文，只逐字摘出点名具体行业的句子或关键短句，不做判断，看不到任何行情。
3. **盲编码**（[`coding_work/rows/`](coding_work/rows/)）：编码 agent 只读摘录，按规则判断每个行业的措辞方向（扶持 / 中性 / 供给约束 / 需求约束）、强度、与上一期相比的变化。
4. **机械合并与冻结**（[`scripts/merge_events.py`](scripts/merge_events.py)）：分配编号、按申万代码机械计算「方向反转」，生成 [`events/events_v1.csv`](events/events_v1.csv)（64 份文件、2,234 条），写入 [`events/FROZEN.sha256`](events/FROZEN.sha256)。
5. **独立回测**（[`backtest/`](backtest/)）：另一个 agent 只拿冻结事件表、行情数据和预登记计划，先核对全部哈希，再执行计划；不能增删或改动事件。包括按文件聚类的自助法置信区间、随机换行业与随机挪日期两种安慰剂（各 2,000 次）、事件时间路径和三个组合。
6. **交叉核对**：用独立代码重算 50 个超额收益，与回测结果完全一致。

过程记录（包括中途的打断、改为两阶段编码等）见 [`coding_work/README.md`](coding_work/README.md)。

## 仓库结构

| 路径 | 内容 |
|---|---|
| `index.html` | 交互页面（单文件，行情月线内嵌） |
| `prereg/` | 编码协议、摘录协议、分析计划及补充说明、输出规范、申万分类表、哈希 |
| `coding_work/texts/` | 64 份文件的逐字摘录（含来源链接与发布日期出处） |
| `coding_work/rows/` | 各文件的编码结果与编码日志 |
| `events/` | 冻结的事件表、文件清单、合并报告、哈希 |
| `backtest/` | 回测代码、逐事件结果、汇总结果、组合月度收益、安慰剂抽样、报告 |
| `data/` | 申万行业指数月线与日线（见下方说明） |
| `page/` | 页面源码（模板、脚本、构建与截图测试） |
| `scripts/` | 行情整理与事件合并脚本 |

## 复现

```bash
python3 scripts/prep_data.py          # data/raw → data/sw_monthly.csv, sw_daily.csv
python3 scripts/merge_events.py       # 校验 coding_work/rows（加 --freeze 生成事件表）
python3 backtest/backtest.py          # 生成 backtest/ 下全部结果（约 1 分钟）
python3 page/build_page.py --standalone --out index.html
```

`scripts/merge_events.py`、`scripts/prep_data.py` 与 `backtest/backtest.py` 保留了运行时的原样（含绝对路径 `/home/claude/policy_bt`，以保持与哈希记录一致）；在本地复现时请把文件开头的路径改成仓库所在目录。依赖：Python 3.11+、pandas、numpy、scipy。

## 局限

- 申万行业指数是价格指数，不含分红；超额收益相对申万A指（同样不含分红）。
- 现行申万指数中，银行、汽车、电力设备、计算机、传媒、通信、国防军工等一级行业 2014 年才开始编制，光伏设备、电池、白酒、教育等二级行业 2021 年底才有；没有使用已停发的旧版指数。2,234 条中 335 条因当时没有对应指数未能回测，292 条是泛指概念（如「战略性新兴产业」）无法对应单个行业。
- 主检验只有 5 部规划建议，按文件数计样本很少；聚类自助区间在簇少时偏窄，安慰剂比较更可靠。
- 专项文件清单由研究者事先挑选，挑选者知道后来的行情，相关结果只作探索性参考。
- 编码由语言模型完成，规则要求逐字、穷尽，但无法完全排除模型对历史行情的记忆影响。
- 部分原文只能读到公开的删减版或摘要版；十五计划纲要第二十六章末尾、十五五纲要第二十七章与第九篇未能读取；纲要的专栏方框多为图片未能摘录。
- 证券Ⅱ、煤炭开采两个指数在源数据中有长段缺失，按预登记规则处理。
- 组合回测等权、月度调仓、不计交易成本，行业指数本身不可直接交易。

## 数据来源与说明

- 行情：申万宏源研究公开发布的申万行业指数（https://www.swsresearch.com），2026-10-26 获取。指数数据的相关权利归申万宏源研究所有，本仓库仅用于研究复现，使用前请自行确认其使用条款。
- 政策原文：中国政府网、国家发展改革委、新华网、人民网等官方或权威转载渠道，链接见各摘录文件头部。
- 李录「目标与代价」的论述来自其 2026 年 10 月哥伦比亚商学院格雷厄姆与多德论坛演讲整理稿（虎嗅转载）。
- 本项目仅作研究展示，不构成投资建议。

## 许可

代码、编码规则与分析文档以 [MIT 许可](LICENSE) 发布。`data/` 中的行情数据与 `coding_work/texts/` 中的政策原文摘录不在此许可范围内，其权利归各自来源。

---

## English summary

**Question.** When China's Five-Year Plans and other national policy documents describe an industry favourably or restrictively, does that wording predict the industry's later stock-market performance?

**Primary pre-registered test.** Buy the SW industry index of every industry a Five-Year Plan *proposal* supports, at the first month-end after the text is published, and hold for 36 months against the SW All-A index.

| Test | n | Win rate | Mean excess | Random-industry placebo (median) | p |
|---|---|---|---|---|---|
| Support · FYP proposals · 36 mo (primary) | 279 (5 proposals) | 44.4% | −1.0% | 45.5% | 0.71 |
| Support · FYP proposals · 12 mo | 371 | 34.2% | −3.9% | 45.8% | 1.00 |
| Support · proposals + outlines · 36 mo | 581 | 46.8% | +3.7% | 45.8% | 0.26 |
| Support · other documents · 36 mo (exploratory) | 260 | 50.0% | +1.8% | 51.0% | 0.67 |
| Avoid demand/regulatory curbs · 36 mo | 73 | 52.1% | curbed +5.8% | 50.7% | 0.46 |

Supportive wording did not pick winners (and lagged in the first year — an exploratory, after-the-fact observation); restrictive wording did not pick losers. Holding every industry with a supportive statement for 36 months earned +3.5% a year over the benchmark (information ratio 0.36), a descriptive result driven by a few large winners and not pre-registered as a test.

**Method.** Pre-registered protocols and analysis plan with SHA-256 timestamps; verbatim extraction of industry wording from official texts by agents with no market data; blind coding into 2,234 events from 64 documents; mechanical merge and freeze; an independent backtest agent that could only read the frozen events, the price data and the plan; doc-clustered bootstrap and two placebo tests (random industries, shifted dates). See `prereg/`, `events/`, `backtest/report.md`.

**Data.** SW industry indices published by SWS Research (rights remain with SWS Research; included for research reproducibility only). Policy texts from gov.cn, NDRC, Xinhua and other official sources. Not investment advice.

**License.** Code, coding rules and analysis documents are released under the [MIT License](LICENSE). The market data in `data/` and the policy-text extracts in `coding_work/texts/` are not covered; their rights stay with their sources.
