(function () {
'use strict';
const D = JSON.parse(document.getElementById('pc-data').textContent);
const d3 = window.d3;

/* ================================================================ helpers */
const $ = (s, r = document) => r.querySelector(s);
const h = (tag, attrs, ...kids) => {
  const el = document.createElement(tag);
  if (attrs) for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'text') el.textContent = v;
    else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? '' : String(v));
  }
  for (const k of kids.flat(3)) { if (k == null || k === false) continue; el.append(k.nodeType ? k : document.createTextNode(String(k))); }
  return el;
};
const clear = el => { while (el.firstChild) el.removeChild(el.firstChild); return el; };
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const store = {
  get(k, d) { try { const v = localStorage.getItem('pc.' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('pc.' + k, JSON.stringify(v)); } catch (e) { /* storage unavailable */ } }
};
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const M = D.months, NM = M.length, MI = new Map(M.map((m, i) => [m, i]));
const IDX = D.idx, BENCH = D.bench;
const EV = D.events || [];
const EVBYID = new Map(EV.map(e => [e.id, e]));
const PLANS = D.plans || [];
const PLANBY = new Map(PLANS.map(p => [p.id, p]));
const RES = D.results || null;
const L1 = D.l1 || Object.keys(IDX).filter(c => IDX[c].lvl === 1);

const S = {
  lang: store.get('lang', 'zh'),
  conv: store.get('conv', null),
  ind: store.get('ind', D.defaultInd),
  range: 'all',
  scale: store.get('scale', 'log'),
  plan: store.get('plan', D.defaultPlan || (PLANS.length ? PLANS[PLANS.length - 2].id : null)),
  sel: null,
  winRule: 'S+|FYP_proposal'
};
if (!IDX[S.ind]) S.ind = D.defaultInd;
if (!PLANBY.has(S.plan)) S.plan = PLANS.length ? PLANS[0].id : null;
if (!S.conv) S.conv = S.lang === 'zh' ? 'cn' : 'intl';

/* ================================================================ i18n */
const I = {
zh: {
  'mast.k1': (a, b) => `申万行业指数 ${a}—${b}`,
  'mast.count': n => `政策措辞 ${n} 条`,
  'mast.k3': '预登记 · 盲编码 · 独立回测',
  'mast.title': '国策K线', 'mast.sub': 'Policy Candles',
  'mast.dek': '二十五年里，六部五年规划和数十份产业政策文件怎样描述各个行业，这些措辞之后申万行业指数又怎样走。行业时间线把每个行业的政策节点叠在月K线上；五年计划追踪逐期看被点名的行业；盲测回测回答「跟着政策买」的胜率。',
  'nav.overview': '总览', 'nav.industry': '行业时间线', 'nav.plans': '五年计划追踪', 'nav.backtest': '盲测回测', 'nav.data': '数据与局限',
  'conv.cn': '红涨绿跌', 'conv.intl': '绿涨红跌',
  'ov.h': '结论', 'ov.k': '回测要点',
  'lilu.h': '目标与代价',
  'lilu.p1': '李录在 2026 年 10 月哥伦比亚商学院格雷厄姆与多德论坛上谈到：中国大约每十年设定一组新的发展目标，为实现目标付出的代价总会落在某些人身上；某一阶段的目标，几年后可能变成代价。环境治理先是代价、后成目标；房地产先是目标、后成代价。',
  'lilu.p2': '他留给投资者的问题是：所投企业是目标的受益者，还是代价的买单者？本页把这个问题变成可以检验的形式：政策措辞有没有提前标出受益者（扶持类措辞）和买单者（约束类措辞），跟着措辞买卖，胜率又是多少。',
  'lilu.src': '来源：', 'lilu.link': '虎嗅转载的演讲整理稿（2026-10-12）',
  'tc.t': '目标：被扶持次数最多的行业', 'tc.c': '代价：被约束次数最多的行业', 'tc.n': n => `${n} 次`,
  'ind.h': '行业时间线', 'ind.k': '申万一级 31 个 · 二级 124 个',
  'ind.lede': '选择一个行业。上方是申万行业指数的月K线，阴影标出各期五年规划；中间一行是政策节点（▲ 扶持、● 中性或规范、▼ 约束）；下方是相对申万A指的强弱，以及成交额占全A的比例。点「回放」按月重走一遍，政策出现时会弹出原文。',
  'ind.search': '搜索行业', 'ind.log': '对数', 'ind.lin': '线性', 'ind.reset': '重置',
  'ind.hint': '拖动平移 · Ctrl/⌘ + 滚轮缩放 · 双击重置',
  'ind.table': '查看月度数据表',
  'ind.play': '▶ 回放', 'ind.pause': '❚❚ 暂停', 'ind.resume': '▶ 继续',
  'ind.meta': (code, lvl, since) => `${code} · 申万${lvl === 1 ? '一级' : '二级'} · 数据起于 ${since}`,
  'ind.l1all': '一级整体',
  'range.all': '全部',
  'pane.k': (n, sc) => `${n} · 月K线（${sc === 'log' ? '对数' : '线性'}坐标）`,
  'pane.lane': '政策', 'pane.rs': '相对申万A指（区间起点 = 100）', 'pane.ts': '成交额占全A',
  'tip.o': '开', 'tip.h': '高', 'tip.l': '低', 'tip.c': '收', 'tip.chg': '月涨跌', 'tip.rs': '相对A指', 'tip.ts': '成交占比',
  'tick.more': n => `同月另有 ${n} 条`,
  'k.empty': (n, since) => `${n}指数 ${since} 起才有数据，这一时段无法显示。`,
  'k.nolib': '图表库未能加载，下方的政策条目与表格仍可查看。',
  'k.src': '数据：申万宏源研究 · 申万行业指数月线（价格指数，不含分红），截至 2026-10-23',
  'leg.up': '上涨月', 'leg.dn': '下跌月',
  'ev.title': (name, n) => `${name}：${n} 条政策措辞`,
  'ev.hint': '点击条目，在K线上定位并标出之后 36 个月',
  'ev.empty': '这个行业在已编码的文件中没有被具体点名。',
  'ev.prev': '上一期：', 'ev.o12': '12个月超额', 'ev.o36': '36个月超额', 'ev.pre': '事前12个月',
  'ev.win': '胜', 'ev.loss': '负', 'ev.na': '没有对应的申万指数，未回测', 'ev.inc': '尚不满36个月',
  'ev.series': (n, c, l) => `回测指数：${n} ${c}（${l}）`, 'ev.source': '原文',
  'ev.hb': '供给约束按“回避”计胜负；若按“在位者受益”假设，胜负相反。',
  'ev.rangeOnly': p => `只显示 ${p} 区间内的条目`,
  'evf.main': '扶持与约束', 'evf.R': '约束', 'evf.all': '全部', 'evf.more': n => `显示其余 ${n} 条`,
  'st.S+': '扶持', 'st.S0': '中性/规范', 'st.R-supply': '供给约束', 'st.R-demand': '需求/监管约束',
  'ch.new': '新提出', 'ch.up': '加码', 'ch.same': '延续', 'ch.down': '减弱', 'ch.dropped': '不再提', 'ch.na': '',
  'dt.FYP_proposal': '规划建议', 'dt.FYP_outline': '规划纲要', 'dt.other': '专项文件', 'dt.GWR_first': '政府工作报告首提',
  'int.3': '强', 'int.2': '明确', 'int.1': '提及',
  'pl.h': '五年计划追踪', 'pl.k': '十五 → 十五五',
  'pl.lede': '每一期五年规划建议点名了哪些行业，措辞比上一期加码还是减弱，这些行业在规划发布后又怎样走。时间从规划建议全文发布后的第一个月末算起。',
  'pl.proposal': '建议全文发布', 'pl.outline': '纲要发布', 'pl.coded': '编码条目', 'pl.tested': '可回测',
  'pl.shifts': '措辞变化（对比上一期建议）', 'pl.shiftsHint': '点击行业，对比前后原文',
  'pl.col.new': '新提出', 'pl.col.up': '加码', 'pl.col.down': '减弱', 'pl.col.dropped': '不再提', 'pl.none': '无',
  'pl.qempty': '选择上方的行业，对比两期原文。', 'pl.qnow': '本期', 'pl.qprev': '上一期', 'pl.qnone': '（未提及）',
  'pl.race': '政策赛马：点名行业的累计超额收益', 'pl.raceNote': '横轴为相对申万A指的累计超额收益；▶ 按月播放，最多显示绝对值最大的 12 个。',
  'pl.raceLab': (k, m) => `第 ${k} 个月 · ${m}`,
  'pl.lines': '规划发布后各行业的累计超额收益路径', 'pl.avg': '扶持行业平均', 'pl.avgSub': n => `${n} 个被扶持行业的等权平均`, 'pl.linesHint': '阴影 = 规划期；竖线 = 第 36 个月；悬停查看行业',
  'pl.first': '十五是基准期，没有上一期可比。',
  'pl.noLines': '这一期点名的行业在当时都还没有对应的申万指数。',
  'sc.cap': '本期规划建议点名行业的成绩单（按 36 个月超额排序）', 'sc.allRows': n => `包括纲要与中性条目（共 ${n} 条）`, 'sc.lessRows': '只看规划建议中的扶持与约束', 'sc.concept': '行业（原文提法）', 'sc.stance': '措辞', 'sc.change': '变化', 'sc.int': '强度', 'sc.series': '回测指数',
  'sc.b12': '12个月', 'sc.b36': '36个月', 'sc.plan': '至规划期末', 'sc.res': '结果',
  'sc.note': '12 与 36 个月超额收益来自独立回测 agent；“至规划期末”为从入场到规划最后一年 12 月的超额收益，由本页按同一公式计算，仅作描述。',
  'bt.h': '盲测回测', 'bt.k': '预登记 · 两个独立 agent',
  'bt.lede': '为避免「揣着答案做题」，编码与回测交给两个互不相见的 agent。编码 agent 只读政策原文、看不到任何行情，按预先写定的规则把措辞编成事件表，写完即加哈希冻结。回测 agent 只拿冻结的事件表、行情数据和预登记的分析计划，不能增删或改动任何事件。胜负标准、持有期和安慰剂检验都在看到结果之前写定。',
  'bt.win': '胜率与随机对照', 'bt.winNote': '蓝点为实际胜率，竖线为按文件聚类的 95% 自助区间；灰色粗线为 2,000 次随机换行业的 5%–95% 区间，灰点为其中位数。',
  'bt.car': '事件时间的平均累计超额收益', 'bt.carNote': '第 0 个月为入场月末；左侧是发布前的走势。阴影为五年规划“扶持”组的 95% 区间。',
  'bt.port': '组合回测：持续跟随政策信号',
  'bt.portNote': 'P1：规划期内持有所有被五年规划“扶持”的行业；P2：任一扶持措辞后持有 36 个月；P3：P2 多头减去“需求/监管约束”行业空头。纵轴为相对申万A指的累计净值（P3 为多空净值），起点 = 100。等权，月度调仓，不计交易成本。',
  'bt.rule.S+|FYP_proposal': '扶持 · 五年规划建议（主检验）', 'bt.rule.S+|all': '扶持 · 全部文件',
  'bt.rule.R-demand|all': '需求/监管约束 · 回避', 'bt.rule.R-supply H-a|all': '供给约束 · 回避', 'bt.rule.R-supply H-b|all': '供给约束 · 在位者受益',
  'bt.rule.S+|FYP': '扶持 · 规划建议与纲要', 'bt.rule.S+|other': '扶持 · 专项文件（探索性）', 'bt.rule.S+|GWR_first': '扶持 · 政府工作报告首提',
  'bt.h1': '个月', 'bt.wr': '胜率', 'bt.n': 'n',
  'pt.h': '组合', 'pt.per': '区间', 'pt.ret': '年化', 'pt.b': '基准年化', 'pt.ex': '年化超额', 'pt.vol': '超额波动', 'pt.ir': '信息比率', 'pt.dd': '超额最大回撤', 'pt.hit': '月度胜率', 'pt.hold': '平均持仓',
  'pt.P1': 'P1 跟着规划买', 'pt.P2': 'P2 扶持后持有36个月', 'pt.P3': 'P3 扶持多 / 约束空',
  'sub.cap': '分组胜率（36 个月；默认只看扶持类）', 'sub.more': '加上约束类分组', 'sub.less': '只看扶持类', 'sub.na': '不适用（专项文件）', 'sub.dim': '分组', 'sub.val': '取值', 'sub.rule': '标准', 'sub.mean': '平均超额',
  'dim.plan': '规划期', 'dim.doc_type': '文件类型', 'dim.stance': '措辞', 'dim.intensity': '强度', 'dim.change_vs_prev': '变化', 'dim.pivot': '方向反转', 'dim.decade': '年代',
  'main.cap': '主要检验（36 个月）', 'main.test': '检验', 'main.perm': '随机行业', 'main.shift': '随机日期', 'main.p': 'p 值',
  'react.cap': '发布前的走势、短期反应与成交占比（平均超额）', 'react.g': '组别', 'react.pre12': '事前12月', 'react.pre3': '事前3月', 'react.d1': '2日', 'react.d5': '6日', 'react.d20': '21日', 'react.ts': '成交占比变化',
  'dt.h': '数据与局限', 'dt.k': '方法说明',
  'cov.cap': '申万一级指数的起始时间（决定早期政策能否回测）', 'cov.start': '数据起于', 'cov.list': '行业',
  'hash.h': '预登记与冻结文件（SHA-256）',
  'excl.cap': '未能回测的条目', 'excl.reason': '原因', 'excl.n': '条数',
  'excl.no_series_at_entry': '当时没有对应的申万指数', 'excl.no_sw_code': '无法对应到申万行业', 'excl.no_entry': '发布日期晚于最新数据', 'excl.other': '其他',
  'dt.src': '资料来源',
  'foot': '行情数据来自申万宏源研究公开发布的申万行业指数；政策原文来自中国政府网、国家发展改革委、新华网等官方渠道。本页仅作研究展示，不构成投资建议。',
  'pending': '回测结果生成中',
  'lim': [
    '申万行业指数是价格指数，不含分红；超额收益相对申万A指（同样不含分红）计算。',
    '现行申万指数中，银行、汽车、电力设备、计算机、传媒、通信、国防军工等一级行业 2014 年才开始编制，光伏设备、电池、白酒、教育等二级行业 2021 年底才有。更早的相关政策只能用更粗的指数代替，否则不回测。',
    '已停发的旧版申万指数没有使用，所以早期政策的样本偏少，结论更偏向 2014 年以后。',
    '五年规划的建议全文是完整样本（主检验）；专项文件清单由研究者事先挑选，挑选者知道后来的行情，结果只作探索性参考。',
    '编码 agent 是语言模型，训练中见过历史行情。规则要求它逐字按原文编码、穷尽列出所有被点名的行业，但无法完全排除记忆的影响。',
    '同一份文件里的多个行业不是独立样本；置信区间按文件聚类自助抽样计算。',
    '组合回测等权、月度调仓、不计交易成本和冲击成本，且行业指数本身不可直接交易。',
    '2026 年 10 月为不完整月份（截至 23 日）；十五五和十四五后期的条目尚不满 36 个月，不计入 36 个月统计。'
  ]
},
en: {
  'mast.k1': (a, b) => `SW industry indices ${a}–${b}`,
  'mast.count': n => `${n} coded policy statements`,
  'mast.k3': 'Pre-registered · blind-coded · independent backtest',
  'mast.title': '国策K线', 'mast.sub': 'Policy Candles',
  'mast.dek': 'Over 25 years, how six Five-Year Plans and dozens of industrial-policy documents described each industry, and what SW industry indices did next. Industry timelines lay each industry’s policy moments over its monthly candles; the plan tracker follows the industries each plan singled out; the blind backtest measures how often buying what the policy favoured paid off.',
  'nav.overview': 'Overview', 'nav.industry': 'Industry timelines', 'nav.plans': 'Plan tracker', 'nav.backtest': 'Blind backtest', 'nav.data': 'Data & limits',
  'conv.cn': 'Red = up', 'conv.intl': 'Green = up',
  'ov.h': 'Findings', 'ov.k': 'AT A GLANCE',
  'lilu.h': 'Targets and their costs',
  'lilu.p1': 'At Columbia Business School’s Graham & Dodd forum in October 2026, Li Lu described China as setting a new group of development targets about once a decade, with the cost of meeting them landing on someone. A target in one stage can become a cost a few years later: environmental protection moved from cost to target, property from target to cost.',
  'lilu.p2': 'His question for investors: is a business a beneficiary of the target, or the one paying the cost? This page makes that testable. Did policy wording flag the beneficiaries (supportive wording) and the payers (restrictive wording) in advance, and how often did trading on the wording work?',
  'lilu.src': 'Source:', 'lilu.link': 'transcript reprinted by Huxiu, 12 Oct 2026 (Chinese)',
  'tc.t': 'Targets: industries supported most often', 'tc.c': 'Costs: industries restricted most often', 'tc.n': n => `${n}×`,
  'ind.h': 'Industry timelines', 'ind.k': '31 SW LEVEL-1 · 124 LEVEL-2 INDICES',
  'ind.lede': 'Pick an industry. The top pane shows the SW industry index as monthly candles, with Five-Year Plan periods shaded. The strip below marks policy events (▲ support, ● neutral or regulating, ▼ restriction). Underneath are strength relative to the SW All-A index and the industry’s share of A-share turnover. Press Replay to walk through month by month; the policy text pops up as each event arrives.',
  'ind.search': 'Search industries', 'ind.log': 'Log', 'ind.lin': 'Linear', 'ind.reset': 'Reset',
  'ind.hint': 'Drag to pan · Ctrl/⌘ + scroll to zoom · double-click to reset',
  'ind.table': 'Show the monthly data table',
  'ind.play': '▶ Replay', 'ind.pause': '❚❚ Pause', 'ind.resume': '▶ Resume',
  'ind.meta': (code, lvl, since) => `${code} · SW level ${lvl} · data from ${since}`,
  'ind.l1all': 'Whole level 1',
  'range.all': 'All',
  'pane.k': (n, sc) => `${n} · monthly candles (${sc} scale)`,
  'pane.lane': 'Policy', 'pane.rs': 'Relative to SW All-A (start of range = 100)', 'pane.ts': 'Share of A-share turnover',
  'tip.o': 'O', 'tip.h': 'H', 'tip.l': 'L', 'tip.c': 'C', 'tip.chg': 'Month', 'tip.rs': 'vs All-A', 'tip.ts': 'Turnover share',
  'tick.more': n => `${n} more this month`,
  'k.empty': (n, since) => `The ${n} index starts in ${since}, so this period has no data.`,
  'k.nolib': 'The chart library did not load; the policy entries and tables below still work.',
  'k.src': 'Data: SWS Research · SW industry index monthly bars (price indices, ex-dividends), through 23 Oct 2026',
  'leg.up': 'Up month', 'leg.dn': 'Down month',
  'ev.title': (name, n) => `${name}: ${n} policy statements`,
  'ev.hint': 'Click an entry to locate it on the chart and mark the next 36 months',
  'ev.empty': 'No coded document names this industry specifically.',
  'ev.prev': 'Previous plan: ', 'ev.o12': '12-mo excess', 'ev.o36': '36-mo excess', 'ev.pre': 'Prior 12 mo',
  'ev.win': 'win', 'ev.loss': 'loss', 'ev.na': 'No matching SW index at the time; not tested', 'ev.inc': 'under 36 months so far',
  'ev.series': (n, c, l) => `Tested on: ${n} ${c} (${l})`, 'ev.source': 'Source',
  'ev.hb': 'Supply curbs are scored as "avoid"; under the "incumbents gain" hypothesis the result flips.',
  'ev.rangeOnly': p => `Showing entries within ${p} only`,
  'evf.main': 'Support & curbs', 'evf.R': 'Curbs', 'evf.all': 'All', 'evf.more': n => `Show ${n} more`,
  'st.S+': 'Support', 'st.S0': 'Neutral', 'st.R-supply': 'Supply curb', 'st.R-demand': 'Demand/regulatory curb',
  'ch.new': 'New', 'ch.up': 'Stronger', 'ch.same': 'Same', 'ch.down': 'Weaker', 'ch.dropped': 'Dropped', 'ch.na': '',
  'dt.FYP_proposal': 'Plan proposal', 'dt.FYP_outline': 'Plan outline', 'dt.other': 'Other document', 'dt.GWR_first': 'Work report, first mention',
  'int.3': 'strong', 'int.2': 'explicit', 'int.1': 'mention',
  'pl.h': 'Plan tracker', 'pl.k': '10TH → 15TH FIVE-YEAR PLAN',
  'pl.lede': 'Which industries each plan proposal singled out, whether the wording strengthened or weakened against the previous plan, and how those industries traded afterwards. Time runs from the first month-end after the proposal text was published.',
  'pl.proposal': 'Proposal published', 'pl.outline': 'Outline published', 'pl.coded': 'Coded statements', 'pl.tested': 'Testable',
  'pl.shifts': 'Wording shifts vs the previous plan', 'pl.shiftsHint': 'Click an industry to compare the wording',
  'pl.col.new': 'New', 'pl.col.up': 'Stronger', 'pl.col.down': 'Weaker', 'pl.col.dropped': 'Dropped', 'pl.none': 'None',
  'pl.qempty': 'Pick an industry above to compare the two plans’ wording.', 'pl.qnow': 'This plan', 'pl.qprev': 'Previous', 'pl.qnone': '(not mentioned)',
  'pl.race': 'Policy race: cumulative excess return of named industries', 'pl.raceNote': 'Bars show cumulative return in excess of SW All-A. Press ▶ to play month by month; the 12 largest moves either way are shown.',
  'pl.raceLab': (k, m) => `Month ${k} · ${m}`,
  'pl.lines': 'Excess-return paths after the plan proposal', 'pl.avg': 'Supported average', 'pl.avgSub': n => `equal-weight average of ${n} supported industries`, 'pl.linesHint': 'Shading = plan period; line = month 36; hover for the industry',
  'pl.first': 'The 10th plan is the baseline; there is no earlier plan to compare.',
  'pl.noLines': 'None of the industries named in this plan had a matching SW index at the time.',
  'sc.cap': 'Scorecard for the industries this plan proposal named (sorted by 36-month excess)', 'sc.allRows': n => `Include outline and neutral rows (${n} in all)`, 'sc.lessRows': 'Proposal support and curbs only', 'sc.concept': 'Industry (plan’s term)', 'sc.stance': 'Wording', 'sc.change': 'Change', 'sc.int': 'Strength', 'sc.series': 'Index tested',
  'sc.b12': '12 mo', 'sc.b36': '36 mo', 'sc.plan': 'To plan end', 'sc.res': 'Result',
  'sc.note': '12- and 36-month excess returns come from the independent backtest agent. "To plan end" is the excess return from entry to December of the plan’s final year, computed on this page with the same formula, for description only.',
  'bt.h': 'Blind backtest', 'bt.k': 'PRE-REGISTERED · TWO INDEPENDENT AGENTS',
  'bt.lede': 'To avoid grading with the answer key in hand, coding and testing went to two agents that never saw each other’s work. The coding agent read only the policy texts, with no market data, coded the wording into an event table under fixed rules, and froze it with a hash. The backtest agent received only the frozen table, the price data and the pre-registered plan, and could not add, drop or change any event. Win rules, holding periods and placebo tests were fixed before any result existed.',
  'bt.win': 'Win rate against placebo', 'bt.winNote': 'Blue dots are actual win rates, with 95% bootstrap intervals clustered by document. Grey bars span the 5th–95th percentile of 2,000 random-industry placebos; grey dots are their medians.',
  'bt.car': 'Average cumulative excess return in event time', 'bt.carNote': 'Month 0 is the entry month-end; the left side shows the run-up before publication. Shading is the 95% interval for Five-Year Plan "support" statements.',
  'bt.port': 'Portfolio backtest: following the signals continuously',
  'bt.portNote': 'P1 holds every industry a Five-Year Plan supports, through the plan period. P2 holds any industry for 36 months after a supportive statement. P3 is P2 long minus demand/regulatory-curb industries short. The axis shows cumulative value relative to SW All-A (P3: long-short value), starting at 100. Equal weights, monthly rebalancing, no trading costs.',
  'bt.rule.S+|FYP_proposal': 'Support · FYP proposals (primary)', 'bt.rule.S+|all': 'Support · all documents',
  'bt.rule.R-demand|all': 'Demand/regulatory curb · avoid', 'bt.rule.R-supply H-a|all': 'Supply curb · avoid', 'bt.rule.R-supply H-b|all': 'Supply curb · incumbents gain',
  'bt.rule.S+|FYP': 'Support · plan proposals and outlines', 'bt.rule.S+|other': 'Support · other documents (exploratory)', 'bt.rule.S+|GWR_first': 'Support · work report first mentions',
  'bt.h1': 'mo', 'bt.wr': 'Win rate', 'bt.n': 'n',
  'pt.h': 'Portfolio', 'pt.per': 'Period', 'pt.ret': 'Ann. return', 'pt.b': 'Benchmark', 'pt.ex': 'Ann. excess', 'pt.vol': 'Excess vol', 'pt.ir': 'Info ratio', 'pt.dd': 'Max DD (excess)', 'pt.hit': 'Hit rate', 'pt.hold': 'Avg holdings',
  'pt.P1': 'P1 follow the plan', 'pt.P2': 'P2 support, hold 36 mo', 'pt.P3': 'P3 support long / curb short',
  'sub.cap': 'Win rate by subgroup (36 months, each group’s own win rule)', 'sub.dim': 'Group', 'sub.val': 'Value', 'sub.rule': 'Rule', 'sub.mean': 'Mean excess',
  'dim.plan': 'Plan', 'dim.doc_type': 'Document type', 'dim.stance': 'Wording', 'dim.intensity': 'Strength', 'dim.change_vs_prev': 'Change', 'dim.pivot': 'Reversal', 'dim.decade': 'Decade',
  'main.cap': 'Main tests (36 months)', 'main.test': 'Test', 'main.perm': 'Random industry', 'main.shift': 'Random date', 'main.p': 'p',
  'react.cap': 'Run-up before publication, short-term reaction and turnover share (mean excess)', 'react.g': 'Group', 'react.pre12': 'Prior 12 mo', 'react.pre3': 'Prior 3 mo', 'react.d1': '2 days', 'react.d5': '6 days', 'react.d20': '21 days', 'react.ts': 'Turnover share change',
  'dt.h': 'Data & limits', 'dt.k': 'METHOD NOTES',
  'cov.cap': 'When each SW level-1 index starts (decides which early policies can be tested)', 'cov.start': 'Data from', 'cov.list': 'Industries',
  'hash.h': 'Pre-registered and frozen files (SHA-256)',
  'excl.cap': 'Statements that could not be tested', 'excl.reason': 'Reason', 'excl.n': 'Count',
  'excl.no_series_at_entry': 'No matching SW index at the time', 'excl.no_sw_code': 'No SW industry fits', 'excl.no_entry': 'Published after the latest data', 'excl.other': 'Other',
  'dt.src': 'Sources',
  'foot': 'Market data: SW industry indices published by SWS Research. Policy texts: gov.cn, the NDRC, Xinhua and other official sources. For research and illustration only; not investment advice.',
  'pending': 'Backtest results pending',
  'lim': [
    'SW industry indices are price indices without dividends; excess returns are measured against SW All-A, also without dividends.',
    'Among current SW indices, level-1 banks, autos, power equipment, computers, media, telecom and defence start only in 2014; level-2 solar equipment, batteries, baijiu and education start at the end of 2021. Earlier policies on those industries use a broader index where one exists, and are otherwise not tested.',
    'Discontinued older-generation SW indices were not used, so early policies are under-represented and the results lean towards the years after 2014.',
    'Five-Year Plan proposals are the complete sample (primary test). The list of other documents was picked by researchers who knew later market history; treat those results as exploratory.',
    'The coding agent is a language model that has seen market history in training. Its rules required verbatim, exhaustive coding of every industry a text names, but memory effects cannot be ruled out entirely.',
    'Several industries in one document are not independent observations; confidence intervals use a bootstrap clustered by document.',
    'Portfolios use equal weights and monthly rebalancing with no trading or impact costs, and industry indices cannot be traded directly.',
    'October 2026 is a partial month (to the 23rd). Statements from the 15th plan and late in the 14th plan have under 36 months of data and are left out of the 36-month statistics.'
  ]
}
};
const t = (k, ...a) => { const v = I[S.lang][k] ?? I.zh[k] ?? k; return typeof v === 'function' ? v(...a) : v; };

/* ================================================================ formatting */
const NUMLOC = () => S.lang === 'zh' ? 'zh-CN' : 'en-US';
const pct = (v, d = 1) => (v == null || !isFinite(v)) ? '—' : (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v * 100).toFixed(d) + '%';
const pct0 = (v, d = 0) => (v == null || !isFinite(v)) ? '—' : (v * 100).toFixed(d) + '%';
const num = (v, d = 0) => (v == null || !isFinite(v)) ? '—' : Number(v).toLocaleString(NUMLOC(), { minimumFractionDigits: d, maximumFractionDigits: d });
const sgn = v => (v == null || !isFinite(v)) ? 'flat' : v > 0 ? 'pos' : v < 0 ? 'neg' : 'flat';
const fmtDate = s => {
  if (!s) return '—';
  const [y, m, d] = s.split('-').map(Number);
  if (S.lang === 'zh') return d ? `${y}年${m}月${d}日` : `${y}年${m}月`;
  return d ? `${d} ${MON[m - 1]} ${y}` : `${MON[m - 1]} ${y}`;
};
const pFmt = p => (p == null || !isFinite(p)) ? '—' : p < 0.001 ? '<0.001' : p.toFixed(3);
const STC = { 'S+': 'sp', 'S0': 's0', 'R-supply': 'rs', 'R-demand': 'rd' };
const GLY = { 'S+': '▲', 'S0': '●', 'R-supply': '▼', 'R-demand': '▼' };
const grpOf = st => st === 'S+' ? 'up' : st === 'S0' ? 'mid' : 'dn';

function pal() {
  const cs = getComputedStyle(document.documentElement);
  const g = v => cs.getPropertyValue(v).trim();
  const P = {
    ink: g('--ink'), ink2: g('--ink-2'), muted: g('--muted'), rule: g('--rule'), rule2: g('--rule-2'),
    surface: g('--surface'), surface2: g('--surface-2'), red: g('--red'), green: g('--green'),
    sp: g('--s-plus'), rd: g('--r-demand'), rs: g('--r-supply'), s0: g('--s-zero'),
    accent: g('--accent'), band: g('--band'), sel: g('--sel'), seal: g('--seal')
  };
  P.up = S.conv === 'cn' ? P.red : P.green;
  P.dn = S.conv === 'cn' ? P.green : P.red;
  return P;
}
const stCol = (st, P) => st === 'S+' ? P.sp : st === 'R-demand' ? P.rd : st === 'R-supply' ? P.rs : P.s0;

/* ================================================================ data helpers */
const idxName = c => { const x = IDX[c]; return x ? (S.lang === 'zh' ? x.zh : x.en) : c; };
const evConcept = e => S.lang === 'zh' ? e.concept_zh : (e.concept_en || e.concept_zh);
const evDoc = e => S.lang === 'zh' ? e.doc_zh : (e.doc_en || e.doc_zh);
const evQuote = e => S.lang === 'zh' ? e.q_zh : (e.q_en || e.q_zh);
const evAltQuote = e => S.lang === 'zh' ? '' : e.q_zh;
const planName = p => S.lang === 'zh' ? p.zh : p.en;
const planYears = p => `${p.y0}–${String(p.y1).slice(2)}`;
const evMonth = e => { const mi = MI.get(e.date.slice(0, 7)); return mi == null ? (e.date < M[0] ? -1 : NM) : mi; };
const firstIdx = (X, from) => { for (let i = Math.max(0, from); i < NM; i++) if (X.c[i] != null) return i; return NM - 1; };
const EVCODE = new Map();
for (const e of EV) for (const c of new Set([...(e.l1 || []), ...(e.l2 || [])])) { if (!EVCODE.has(c)) EVCODE.set(c, []); EVCODE.get(c).push(e); }
for (const arr of EVCODE.values()) arr.sort((a, b) => a.date < b.date ? -1 : a.date > b.date ? 1 : 0);
const evsFor = c => EVCODE.get(c) || [];
function planRange(p) {
  const a = MI.get(`${p.y0 - 1}-01`) ?? 0;
  const bKey = `${p.y1 + 3}-12`;
  const b = MI.has(bKey) ? MI.get(bKey) : NM - 1;
  return [a, b];
}
function rangeFor(code) {
  const X = IDX[code]; const s = firstIdx(X, 0);
  if (S.range === 'all') return [s, NM - 1, false];
  const p = PLANBY.get(S.range); const [a, b] = planRange(p);
  if (b < s) return [a, b, true];
  return [Math.max(a, s), b, false];
}
function winOf(e, h) {
  const v = e['b' + h];
  if (v == null || e.excl) return null;
  if (e.stance === 'S+') return v > 0;
  if (e.stance === 'R-demand' || e.stance === 'R-supply') return v < 0;
  return null;
}
/* equal-weight, monthly-rebalanced index path of several series, anchored at t0 = 1 */
function pathOf(codes, t0, kmin, kmax) {
  const out = new Map(); out.set(0, 1);
  const r = i => { let s = 0, n = 0; for (const c of codes) { const X = IDX[c]; if (X && X.c[i] != null && X.c[i - 1] != null) { s += X.c[i] / X.c[i - 1] - 1; n++; } } return n ? s / n : null; };
  let v = 1;
  for (let k = 1; k <= kmax && t0 + k < NM; k++) { const rr = r(t0 + k); if (rr == null) break; v *= 1 + rr; out.set(k, v); }
  v = 1;
  for (let k = 0; k > kmin && t0 + k - 1 >= 0; k--) { const rr = r(t0 + k); if (rr == null) break; v /= 1 + rr; out.set(k - 1, v); }
  return out;
}
function excessPath(codes, t0, kmin, kmax) {
  const a = pathOf(codes, t0, kmin, kmax), b = pathOf([BENCH], t0, kmin, kmax); const out = [];
  for (let k = kmin; k <= kmax; k++) if (a.has(k) && b.has(k)) out.push([k, a.get(k) - b.get(k)]);
  return out;
}

/* ================================================================ chart: K-line */
function KChart(host, cb) {
  const root = d3.select(host);
  const svg = root.append('svg').attr('tabindex', 0);
  const defs = svg.append('defs');
  const mk = id => defs.append('clipPath').attr('id', id).append('rect');
  const cK = mk('pcK'), cA = mk('pcA'), cU = mk('pcU'), cD = mk('pcD');
  const gGrid = svg.append('g'), gBand = svg.append('g').attr('clip-path', 'url(#pcA)'), gSel = svg.append('g').attr('clip-path', 'url(#pcA)');
  const gK = svg.append('g').attr('clip-path', 'url(#pcK)'), gRS = svg.append('g').attr('clip-path', 'url(#pcA)'), gTS = svg.append('g').attr('clip-path', 'url(#pcA)');
  const gAx = svg.append('g'), gLab = svg.append('g'), gX = svg.append('g').style('pointer-events', 'none');
  const gLane = svg.append('g').attr('clip-path', 'url(#pcA)');
  const tip = root.append('div').attr('class', 'k-tip').attr('hidden', '');
  const ticker = root.append('div').attr('class', 'k-ticker').attr('aria-live', 'polite');
  const empty = root.append('div').attr('class', 'k-empty').attr('hidden', '');
  const st = { code: null, i0: 0, i1: 0, evs: [], cursor: null, newest: null, sel: null, va: 0, vb: 0, kb: null, emptyMsg: null };
  let W = 0, H = 0, L = null, x0 = d3.scaleLinear(), x = x0, timer = null, tickT = null, speed = 1, dragging = false;
  const zoom = d3.zoom().scaleExtent([1, 40])
    .filter(ev => ev.type === 'wheel' ? (ev.ctrlKey || ev.metaKey) : ev.type === 'touchstart' ? ev.touches.length > 1 : ev.type !== 'dblclick' && !ev.button)
    .on('start', ev => { if (ev.sourceEvent && ev.sourceEvent.type === 'mousedown') { dragging = true; hideCross(); } })
    .on('zoom', ev => { x = ev.transform.rescaleX(x0); draw(); })
    .on('end', () => { dragging = false; });
  svg.call(zoom).on('dblclick.zoom', null).on('dblclick', () => resetZoom(true));

  function layout() {
    W = Math.max(300, Math.round(host.getBoundingClientRect().width)); const nar = W < 640;
    H = nar ? 440 : 548;
    const m = { l: 8, r: nar ? 48 : 62, t: 26, b: 26 }, laneH = 30, gap = 10;
    const avail = H - m.t - m.b - laneH - gap * 3;
    const kH = Math.round(avail * 0.58), rsH = Math.round(avail * 0.26), tsH = avail - kH - rsH;
    const kY = m.t, laneY = kY + kH + gap, rsY = laneY + laneH + gap, tsY = rsY + rsH + gap, axY = tsY + tsH;
    L = { m, x0: m.l, x1: W - m.r, iw: W - m.l - m.r, kY, kH, laneY, laneH, rsY, rsH, tsY, tsH, axY, nar };
    svg.attr('viewBox', `0 0 ${W} ${H}`).attr('height', H);
    cK.attr('x', L.x0).attr('y', kY).attr('width', L.iw).attr('height', kH);
    cA.attr('x', L.x0).attr('y', kY).attr('width', L.iw).attr('height', axY - kY);
    x0.range([L.x0, L.x1]);
    zoom.extent([[L.x0, 0], [L.x1, H]]).translateExtent([[L.x0, -Infinity], [L.x1, Infinity]]);
  }
  function resize() {
    if (!st.code) { layout(); return; }
    const dom = x.domain(); layout();
    const a = dom[0] + 0.5, b = dom[1] - 0.5;
    if (Math.abs(a - st.i0) < 1e-6 && Math.abs(b - st.i1) < 1e-6) { svg.call(zoom.transform, d3.zoomIdentity); x = x0; draw(); }
    else zoomTo(a, b, false);
  }
  function setData(code, i0, i1, evs, emptyMsg) {
    stop(true);
    Object.assign(st, { code, i0, i1, evs, sel: null, emptyMsg: emptyMsg || null, kb: null });
    if (!L) layout();
    x0.domain([i0 - 0.5, i1 + 0.5]); x = x0;
    svg.call(zoom.transform, d3.zoomIdentity);
    hideCross(); draw();
  }
  function zoomTo(a, b, anim) {
    a = Math.max(st.i0, a); b = Math.min(st.i1, b);
    if (b - a < 8) { const c = (a + b) / 2; a = Math.max(st.i0, Math.round(c - 4)); b = Math.min(st.i1, a + 8); }
    const k = L.iw / (x0(b + 0.5) - x0(a - 0.5)), tx = L.x0 - k * x0(a - 0.5);
    const tf = d3.zoomIdentity.translate(tx, 0).scale(k);
    (anim ? svg.transition().duration(420) : svg).call(zoom.transform, tf);
  }
  function resetZoom(anim) { (anim ? svg.transition().duration(380) : svg).call(zoom.transform, d3.zoomIdentity); }
  function zoomBy(f) { svg.transition().duration(260).call(zoom.scaleBy, f, [(L.x0 + L.x1) / 2, H / 2]); }

  function cellsFor(last) {
    const map = new Map();
    for (const e of st.evs) {
      const mi = evMonth(e); if (mi < st.i0 || mi > st.i1 || mi > last) continue;
      const g = grpOf(e.stance), key = mi + g;
      if (!map.has(key)) map.set(key, { key, mi, g, evs: [], st: e.stance, size: 0 });
      const c = map.get(key); c.evs.push(e);
      if (e.stance === 'R-demand') c.st = 'R-demand';
      c.size = Math.max(c.size, [0, 46, 72, 104][e.intensity || 1]);
    }
    return Array.from(map.values());
  }
  const laneY = g => g === 'up' ? L.laneY + 8 : g === 'mid' ? L.laneY + L.laneH / 2 : L.laneY + L.laneH - 8;

  function draw() {
    if (!st.code || !L) return;
    const P = pal(), X = IDX[st.code], B = IDX[BENCH];
    empty.attr('hidden', st.emptyMsg ? null : '').text(st.emptyMsg || '');
    const last = st.cursor != null ? st.cursor : st.i1;
    const a = Math.max(st.i0, Math.ceil(x.invert(L.x0) - 0.5)), b = Math.min(st.i1, Math.floor(x.invert(L.x1) + 0.5));
    st.va = a; st.vb = b;
    const all = st.emptyMsg ? [] : d3.range(a, b + 1).filter(i => X.c[i] != null && B.c[i] != null);
    const vis = all.filter(i => i <= last);
    const step = x(1) - x(0), bw = Math.max(1, Math.min(18, step * 0.64));
    let lo = d3.min(all, i => X.l[i]), hi = d3.max(all, i => X.h[i]);
    if (lo == null) { lo = 900; hi = 1100; }
    const yK = (S.scale === 'log' ? d3.scaleLog().domain([lo / 1.035, hi * 1.035]) : d3.scaleLinear().domain([lo - (hi - lo) * 0.05, hi + (hi - lo) * 0.05])).range([L.kY + L.kH - 2, L.kY + 18]);
    const base = firstIdx(X, st.i0), br = X.c[base] / B.c[base];
    const rsv = i => 100 * (X.c[i] / B.c[i]) / br;
    let [rlo, rhi] = d3.extent(all.map(rsv).concat([100])); const rp = (rhi - rlo) * 0.1 || 6;
    const yR = d3.scaleLinear().domain([rlo - rp, rhi + rp]).range([L.rsY + L.rsH - 1, L.rsY + 14]);
    const tmax = d3.max(all, i => X.t[i]) || 1;
    const yT = d3.scaleLinear().domain([0, tmax * 1.12]).range([L.tsY + L.tsH, L.tsY + 14]);

    /* year grid + x labels */
    const pxYear = step * 12; const stepY = pxYear >= 46 ? 1 : pxYear >= 22 ? 2 : pxYear >= 9 ? 5 : 10;
    const quarterly = pxYear > 300;
    const ticks = [];
    for (let i = a; i <= b; i++) {
      const mm = M[i].slice(5), yy = +M[i].slice(0, 4);
      if (quarterly ? ['01', '04', '07', '10'].includes(mm) : (mm === '01' && yy % stepY === 0)) ticks.push(i);
    }
    gGrid.selectAll('line').data(ticks, i => i).join('line')
      .attr('x1', i => x(i - 0.5)).attr('x2', i => x(i - 0.5)).attr('y1', L.kY).attr('y2', L.axY)
      .attr('stroke', P.rule).attr('stroke-width', 1);
    gAx.selectAll('text.xt').data(ticks, i => i).join('text').attr('class', 'xt')
      .attr('x', i => x(i - 0.5) + 3).attr('y', L.axY + 16).attr('fill', P.muted).attr('font-size', 11).attr('font-family', 'IBM Plex Mono, ui-monospace, monospace')
      .text(i => quarterly ? (M[i].slice(5) === '01' ? M[i].slice(0, 4) : M[i].slice(5)) : M[i].slice(0, 4));

    /* plan bands */
    const bands = PLANS.map((p, k) => ({ p, k, a: MI.get(`${p.y0}-01`), b: MI.has(`${p.y1}-12`) ? MI.get(`${p.y1}-12`) : NM - 1 }))
      .filter(d => d.a != null && d.b >= st.i0 && d.a <= st.i1);
    gBand.selectAll('rect').data(bands, d => d.p.id).join('rect')
      .attr('x', d => x(d.a - 0.5)).attr('width', d => Math.max(0, x(d.b + 0.5) - x(d.a - 0.5)))
      .attr('y', L.kY).attr('height', L.axY - L.kY).attr('fill', d => d.k % 2 === 0 ? P.band : 'none');
    gBand.selectAll('text').data(bands, d => d.p.id).join('text')
      .attr('x', d => Math.max(L.x0 + 4, x(d.a - 0.5) + 6)).attr('y', L.kY + 12)
      .attr('fill', P.muted).attr('font-size', 11)
      .text(d => (x(d.b + 0.5) - x(d.a - 0.5)) > 120 ? `${planName(d.p)} ${planYears(d.p)}` : planName(d.p));

    /* selection window */
    const se = st.sel ? EVBYID.get(st.sel) : null; const sd = [];
    if (se) { const mi = evMonth(se), t0 = se.entry && MI.has(se.entry) ? MI.get(se.entry) : mi; sd.push({ mi, t0, t1: Math.min(NM - 1, t0 + 36) }); }
    gSel.selectAll('rect').data(sd).join('rect').attr('x', d => x(d.t0)).attr('width', d => Math.max(0, x(d.t1) - x(d.t0))).attr('y', L.kY).attr('height', L.axY - L.kY).attr('fill', P.sel);
    gSel.selectAll('line').data(sd).join('line').attr('x1', d => x(d.mi)).attr('x2', d => x(d.mi)).attr('y1', L.kY).attr('y2', L.axY).attr('stroke', P.accent).attr('stroke-width', 1.25);
    gSel.selectAll('text').data(sd).join('text').attr('x', d => x(d.t1) - 6).attr('y', L.kY + L.kH - 8).attr('text-anchor', 'end').attr('fill', P.accent).attr('font-size', 11)
      .text(S.lang === 'zh' ? '入场后 36 个月' : '36 months after entry');

    /* candles */
    const up = i => X.c[i] >= X.o[i];
    const hollow = S.conv === 'cn' && bw > 3;
    const cs = gK.selectAll('g.c').data(vis, i => i);
    cs.exit().remove();
    const ce = cs.enter().append('g').attr('class', 'c'); ce.append('line'); ce.append('rect');
    const cm = ce.merge(cs);
    cm.select('line').attr('x1', i => x(i)).attr('x2', i => x(i)).attr('y1', i => yK(X.h[i])).attr('y2', i => yK(X.l[i]))
      .attr('stroke', i => up(i) ? P.up : P.dn).attr('stroke-width', 1);
    cm.select('rect').attr('x', i => x(i) - bw / 2).attr('width', bw)
      .attr('y', i => yK(Math.max(X.o[i], X.c[i]))).attr('height', i => Math.max(1, Math.abs(yK(X.o[i]) - yK(X.c[i]))))
      .attr('fill', i => up(i) ? (hollow ? P.surface : P.up) : P.dn).attr('stroke', i => up(i) ? P.up : P.dn).attr('stroke-width', 1);
    if (st.newest != null && st.cursor != null && vis.includes(st.newest)) {
      const i = st.newest, r = cm.filter(d => d === i).select('rect');
      const y1 = yK(Math.max(X.o[i], X.c[i])), hh = Math.max(1, Math.abs(yK(X.o[i]) - yK(X.c[i])));
      r.attr('y', yK(X.o[i])).attr('height', 0).transition().duration(Math.max(60, 60 / speed)).attr('y', y1).attr('height', hh);
    }

    /* relative strength */
    const pts = d3.range(a, Math.min(b, last) + 1).map(i => (i >= base && X.c[i] != null && B.c[i] != null) ? [x(i), yR(rsv(i))] : null); const y100 = yR(100);
    cU.attr('x', L.x0).attr('y', L.rsY).attr('width', L.iw).attr('height', Math.max(0, y100 - L.rsY));
    cD.attr('x', L.x0).attr('y', y100).attr('width', L.iw).attr('height', Math.max(0, L.rsY + L.rsH - y100));
    const area = d3.area().defined(d => !!d).x(d => d[0]).y0(y100).y1(d => d[1]), line = d3.line().defined(d => !!d).x(d => d[0]).y(d => d[1]);
    gRS.selectAll('path.u').data([pts]).join('path').attr('class', 'u').attr('clip-path', 'url(#pcU)').attr('d', area).attr('fill', P.up).attr('fill-opacity', 0.13);
    gRS.selectAll('path.d').data([pts]).join('path').attr('class', 'd').attr('clip-path', 'url(#pcD)').attr('d', area).attr('fill', P.dn).attr('fill-opacity', 0.13);
    gRS.selectAll('line.r').data([0]).join('line').attr('class', 'r').attr('x1', L.x0).attr('x2', L.x1).attr('y1', y100).attr('y2', y100).attr('stroke', P.rule2);
    gRS.selectAll('path.l').data([pts]).join('path').attr('class', 'l').attr('d', line).attr('fill', 'none').attr('stroke', P.ink2).attr('stroke-width', 1.5).attr('stroke-linejoin', 'round');

    /* turnover share */
    gTS.selectAll('rect').data(vis, i => i).join('rect').attr('x', i => x(i) - bw / 2).attr('width', bw)
      .attr('y', i => yT(X.t[i] || 0)).attr('height', i => Math.max(0, yT(0) - yT(X.t[i] || 0))).attr('fill', P.muted).attr('fill-opacity', 0.5);

    /* right axis labels */
    const kt = (S.scale === 'log' ? yK.ticks(6) : yK.ticks(5)).filter(v => v > 0);
    const kts = []; let lastY = -1e9;
    for (const v of kt.slice().sort((p, q) => q - p)) { const yy = yK(v); if (yy - lastY >= 22) { kts.push(v); lastY = yy; } }
    const lab = (cls, data, yf, fmt) => gAx.selectAll('text.' + cls).data(data).join('text').attr('class', cls)
      .attr('x', L.x1 + 6).attr('y', d => yf(d) + 4).attr('fill', P.muted).attr('font-size', 11).attr('font-family', 'IBM Plex Mono, ui-monospace, monospace').text(fmt);
    lab('ky', kts, yK, v => v >= 1000 ? d3.format(',.0f')(v) : d3.format('.3~g')(v));
    gGrid.selectAll('line.kg').data(kts).join('line').attr('class', 'kg').attr('x1', L.x0).attr('x2', L.x1).attr('y1', d => yK(d)).attr('y2', d => yK(d)).attr('stroke', P.rule).attr('stroke-opacity', 0.7);
    lab('ry', yR.ticks(3), yR, d3.format('.0f'));
    lab('ty', yT.ticks(2).filter(v => v > 0), yT, v => d3.format('.1~f')(v) + '%');
    gAx.selectAll('text.ln').data([0]).join('text').attr('class', 'ln').attr('x', L.x1 + 6).attr('y', L.laneY + L.laneH / 2 + 4).attr('fill', P.muted).attr('font-size', 11).text(t('pane.lane'));
    gAx.selectAll('line.sep').data([L.laneY - 5, L.rsY - 5, L.tsY - 5]).join('line').attr('class', 'sep').attr('x1', L.x0).attr('x2', W - 4).attr('y1', d => d).attr('y2', d => d).attr('stroke', P.rule);

    /* pane titles */
    const titles = [[t('pane.k', idxName(st.code), S.scale), L.kY - 9], [t('pane.rs'), L.rsY + 11], [t('pane.ts'), L.tsY + 11]];
    gLab.selectAll('text').data(titles).join('text').attr('x', L.x0 + 4).attr('y', d => d[1]).attr('fill', (d, i) => i === 0 ? P.ink2 : P.muted)
      .attr('font-size', (d, i) => i === 0 ? 12 : 11).attr('font-weight', (d, i) => i === 0 ? 500 : 400).text(d => d[0]);

    /* policy lane */
    const cells = cellsFor(last).filter(c => c.mi >= a - 1 && c.mi <= b + 1);
    const sym = d3.symbol();
    gLane.selectAll('path').data(cells, c => c.key).join(
      en => en.append('path').style('cursor', 'pointer')
        .on('click', (ev, c) => cb.onSelect(c.evs[0].id))
        .on('pointerenter', (ev, c) => laneTip(ev, c)).on('pointerleave', hideTip)
    ).attr('d', c => sym.type(c.g === 'mid' ? d3.symbolCircle : d3.symbolTriangle).size(c.g === 'mid' ? c.size * 0.6 : c.size)())
      .attr('transform', c => `translate(${x(c.mi)},${laneY(c.g)})${c.g === 'dn' ? ' rotate(180)' : ''}`)
      .attr('fill', c => stCol(c.st, P)).attr('stroke', c => c.evs.some(e => e.id === st.sel) ? P.ink : P.surface).attr('stroke-width', c => c.evs.some(e => e.id === st.sel) ? 2 : 1.5);

    svg.attr('aria-label', t('pane.k', idxName(st.code), S.scale));
    if (st.kb != null) showCross(st.kb);
  }

  /* crosshair + tooltip */
  function hideCross() { gX.selectAll('*').remove(); tip.attr('hidden', ''); }
  function hideTip() { tip.attr('hidden', ''); }
  function placeTip(px) {
    const node = tip.node(); tip.attr('hidden', null);
    const w = node.offsetWidth; let left = px + 16; if (left + w > W - 6) left = px - w - 16; left = Math.max(6, left);
    tip.style('left', left + 'px').style('top', (L.kY + 16) + 'px');
  }
  function showCross(i) {
    const X = IDX[st.code], B = IDX[BENCH]; if (!X || X.c[i] == null || B.c[i] == null) { hideCross(); return; }
    const P = pal(), xx = x(i);
    gX.selectAll('line').data([0]).join('line').attr('x1', xx).attr('x2', xx).attr('y1', L.kY).attr('y2', L.axY).attr('stroke', P.ink2).attr('stroke-opacity', 0.45);
    const node = clear(tip.node());
    const chg = X.c[i - 1] != null ? X.c[i] / X.c[i - 1] - 1 : null;
    const base = firstIdx(X, st.i0), rs = 100 * (X.c[i] / B.c[i]) / (X.c[base] / B.c[base]);
    node.append(h('div', { class: 'd' }, M[i]));
    node.append(h('div', { class: 'ohlc' }, h('span', null, t('tip.o')), h('span', null, num(X.o[i], 0)), h('span', null, t('tip.h')), h('span', null, num(X.h[i], 0)),
      h('span', null, t('tip.l')), h('span', null, num(X.l[i], 0)), h('span', null, t('tip.c')), h('span', null, num(X.c[i], 0))));
    node.append(h('div', { class: 'row' }, h('span', { class: 'muted' }, t('tip.chg')), h('span', { class: sgn(chg) }, pct(chg))));
    node.append(h('div', { class: 'row' }, h('span', { class: 'muted' }, t('tip.rs')), h('span', null, rs.toFixed(1))));
    if (X.t[i] != null) node.append(h('div', { class: 'row' }, h('span', { class: 'muted' }, t('tip.ts')), h('span', null, X.t[i].toFixed(2) + '%')));
    const evs = st.evs.filter(e => evMonth(e) === i);
    if (evs.length) node.append(h('div', { class: 'ev' }, evs.slice(0, 3).map(e => h('div', null, h('span', { class: 'g g-' + STC[e.stance] }, GLY[e.stance]), h('span', null, `${evConcept(e)} · ${evDoc(e)}`)))));
    placeTip(xx);
  }
  function laneTip(ev, c) {
    const node = clear(tip.node());
    node.append(h('div', { class: 'd' }, M[c.mi]));
    node.append(h('div', { class: 'ev', style: 'border:0;margin:0;padding:0' }, c.evs.slice(0, 4).map(e => h('div', null, h('span', { class: 'g g-' + STC[e.stance] }, GLY[e.stance]),
      h('span', null, h('b', null, evConcept(e)), ' · ', evDoc(e), h('br'), h('span', { class: 'muted' }, (evQuote(e) || '').slice(0, 60)))))));
    placeTip(x(c.mi));
  }
  svg.on('pointermove', ev => {
    if (dragging || !st.code || st.emptyMsg) return;
    if (ev.target && ev.target.closest && ev.target.closest('path') && ev.target.parentNode === gLane.node()) return;
    const [mx] = d3.pointer(ev, svg.node());
    if (mx < L.x0 || mx > L.x1) { hideCross(); return; }
    const last = st.cursor != null ? st.cursor : st.vb;
    st.kb = null; showCross(clamp(Math.round(x.invert(mx)), st.va, Math.min(st.vb, last)));
  }).on('pointerleave', () => { if (st.kb == null) hideCross(); });
  svg.on('keydown', ev => {
    if (ev.key === 'ArrowLeft' || ev.key === 'ArrowRight') {
      const last = st.cursor != null ? st.cursor : st.vb;
      st.kb = clamp((st.kb == null ? Math.min(st.vb, last) : st.kb) + (ev.key === 'ArrowLeft' ? -1 : 1), st.va, Math.min(st.vb, last));
      showCross(st.kb); ev.preventDefault();
    } else if (ev.key === 'Escape') { st.kb = null; hideCross(); }
  });

  /* replay */
  function flash(evs) {
    const e = evs[0], node = clear(ticker.node());
    const card = h('div', { class: 'card' },
      h('div', { class: 'd' }, `${e.date} · ${evDoc(e)}`),
      h('div', null, h('span', { class: 'g g-' + STC[e.stance] }, GLY[e.stance] + ' '), h('b', null, evConcept(e)), ' ', evQuote(e) || ''),
      evs.length > 1 ? h('div', { class: 'd' }, t('tick.more', evs.length - 1)) : null);
    node.append(card); ticker.classed('on', true);
    clearTimeout(tickT); tickT = setTimeout(() => ticker.classed('on', false), 2400 / Math.sqrt(speed));
  }
  function tick() {
    st.newest = st.cursor; draw();
    const evs = st.evs.filter(e => evMonth(e) === st.cursor);
    if (evs.length) flash(evs);
    if (st.cursor >= st.i1) { timer = null; setTimeout(() => { st.cursor = null; st.newest = null; draw(); }, 400); cb.onState('done'); return; }
    timer = setTimeout(() => { st.cursor++; tick(); }, (evs.length ? 1100 : 75) / speed);
  }
  function play() {
    if (timer) { clearTimeout(timer); timer = null; cb.onState('paused'); return; }
    if (!st.code || st.emptyMsg) return;
    if (st.cursor == null) { st.cursor = firstIdx(IDX[st.code], st.i0); resetZoom(false); }
    hideCross(); cb.onState('playing'); tick();
  }
  function stop(silent) { clearTimeout(timer); timer = null; st.cursor = null; st.newest = null; ticker.classed('on', false); if (!silent) { cb.onState('done'); draw(); } }
  function select(id) {
    st.sel = id; const e = EVBYID.get(id);
    if (e) { const mi = evMonth(e); zoomTo(mi - 24, mi + 48, true); }
    draw();
  }
  layout();
  return { setData, draw, resize, select, play, stop, zoomBy, reset: () => resetZoom(true), setSpeed: s => { speed = s; }, playing: () => !!timer, paused: () => !timer && st.cursor != null };
}

/* ================================================================ chart: generic lines */
function LineChart(host, opt) {
  const root = d3.select(host); const svg = root.append('svg');
  const tip = root.append('div').attr('class', 'c-tip').attr('hidden', '');
  const legend = root.insert('div', 'svg').attr('class', 'legend').style('margin', '0 0 6px 2px');
  let data = null;
  function render() {
    if (!data) return;
    const P = pal(); const W = Math.max(300, Math.round(host.getBoundingClientRect().width)); const H = opt.height(W);
    legend.selectAll('*').remove();
    if (data.legend) for (const s of data.series) { const sp = legend.append('span'); sp.append('i').attr('class', 'key').style('display', 'inline-block').style('width', '14px').style('height', '2px').style('background', s.color || P.muted); sp.append('span').text(s.label); }
    svg.attr('viewBox', `0 0 ${W} ${H}`).attr('height', H).attr('role', 'img').attr('aria-label', data.title || '');
    svg.selectAll('*').remove();
    const many = data.series.length > 6;
    const m = { l: 46, r: data.endLabels ? (W < 560 ? 96 : 150) : 14, t: 14, b: 28 };
    const xs = d3.scaleLinear().domain(data.xDomain).range([m.l, W - m.r]);
    const ys0 = data.series.flatMap(s => s.values.map(v => v[1]).concat((s.band || []).flatMap(b => [b[1], b[2]]))).concat(data.yInclude || []);
    const [y0, y1] = d3.extent(ys0.length ? ys0 : [0, 1]); const pad = (y1 - y0) * 0.06 || 0.05;
    const ys = d3.scaleLinear().domain([y0 - pad, y1 + pad]).nice(5).range([H - m.b, m.t]);
    const g = svg.append('g');
    for (const vb of (data.vbands || [])) {
      const xa = xs(Math.max(vb.x0, data.xDomain[0])), xb = xs(Math.min(vb.x1, data.xDomain[1])); if (xb <= xa) continue;
      g.append('rect').attr('x', xa).attr('y', m.t).attr('width', xb - xa).attr('height', H - m.b - m.t).attr('fill', P.band);
      if (vb.label) g.append('text').attr('x', xa + 6).attr('y', m.t + 12).attr('fill', P.muted).attr('font-size', 11).text(vb.label);
    }
    const yt = ys.ticks(5);
    g.selectAll('line.gy').data(yt).join('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', d => ys(d)).attr('y2', d => ys(d)).attr('stroke', P.rule);
    g.selectAll('text.gy').data(yt).join('text').attr('x', m.l - 6).attr('y', d => ys(d) + 4).attr('text-anchor', 'end').attr('fill', P.muted).attr('font-size', 11).attr('font-family', 'IBM Plex Mono, ui-monospace, monospace').text(opt.yFmt);
    if (data.refY != null) g.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', ys(data.refY)).attr('y2', ys(data.refY)).attr('stroke', P.rule2).attr('stroke-width', 1.25);
    const xt = (opt.xTicks ? opt.xTicks(data.xDomain, W - m.l - m.r) : xs.ticks(6));
    g.selectAll('text.gx').data(xt).join('text').attr('x', d => xs(d)).attr('y', H - m.b + 17).attr('text-anchor', 'middle').attr('fill', P.muted).attr('font-size', 11).attr('font-family', 'IBM Plex Mono, ui-monospace, monospace').text(opt.xFmt);
    for (const vl of (data.vlines || [])) {
      if (vl.x < data.xDomain[0] || vl.x > data.xDomain[1]) continue;
      g.append('line').attr('x1', xs(vl.x)).attr('x2', xs(vl.x)).attr('y1', m.t).attr('y2', H - m.b).attr('stroke', P.ink2).attr('stroke-opacity', 0.5);
      if (vl.label) g.append('text').attr('x', xs(vl.x) + 4).attr('y', H - m.b - 6).attr('fill', P.muted).attr('font-size', 11).text(vl.label);
    }
    const line = d3.line().x(d => xs(d[0])).y(d => ys(d[1])).curve(d3.curveMonotoneX);
    const area = d3.area().x(d => xs(d[0])).y0(d => ys(d[1])).y1(d => ys(d[2])).curve(d3.curveMonotoneX);
    for (const s of data.series) if (s.band) g.append('path').attr('d', area(s.band)).attr('fill', s.color || P.accent).attr('fill-opacity', 0.12);
    const lg = g.append('g');
    const paths = lg.selectAll('path').data(data.series, s => s.key).join('path')
      .attr('d', s => line(s.values)).attr('fill', 'none').attr('stroke-linejoin', 'round').attr('stroke-linecap', 'round')
      .attr('stroke', s => s.color || P.muted).attr('stroke-width', s => s.width || (many ? 1.4 : 2)).attr('stroke-opacity', s => s.dim ? 0.55 : 1);
    /* end labels */
    if (data.endLabels) {
      let labs = data.series.filter(s => s.values.length).map(s => ({ s, v: s.values[s.values.length - 1] }));
      if (many) { const keep = labs.filter(o => o.s.always); labs = labs.filter(o => !o.s.always); labs.sort((p, q) => q.v[1] - p.v[1]); labs = labs.slice(0, 3).concat(labs.length > 6 ? labs.slice(-3) : labs.slice(3)).concat(keep); }
      labs = labs.map(o => ({ ...o, y: ys(o.v[1]), x: xs(o.v[0]) })).sort((p, q) => p.y - q.y);
      for (let i = 1; i < labs.length; i++) if (labs[i].y - labs[i - 1].y < 13) labs[i].y = labs[i - 1].y + 13;
      const over = labs.length ? labs[labs.length - 1].y - (H - m.b) : 0; if (over > 0) labs.forEach(o => { o.y -= over; });
      const eg = g.append('g');
      for (const o of labs) {
        eg.append('line').attr('x1', o.x + 3).attr('x2', W - m.r + 8).attr('y1', ys(o.v[1])).attr('y2', o.y).attr('stroke', P.rule2);
        eg.append('text').attr('x', W - m.r + 11).attr('y', o.y + 4).attr('fill', P.ink2).attr('font-size', 11.5).text(`${o.s.label} ${opt.vFmt(o.v[1])}`);
      }
    }
    /* hover */
    const hov = g.append('g').style('pointer-events', 'none');
    const ov = svg.append('rect').attr('x', m.l).attr('y', m.t).attr('width', W - m.l - m.r).attr('height', H - m.t - m.b).attr('fill', 'transparent');
    const xr = data.xDomain;
    const hide = () => { hov.selectAll('*').remove(); tip.attr('hidden', ''); paths.attr('stroke', s => s.color || P.muted).attr('stroke-width', s => s.width || (many ? 1.4 : 2)).attr('stroke-opacity', s => s.dim ? 0.55 : 1); };
    ov.on('pointermove', ev => {
      const [mx, my] = d3.pointer(ev, svg.node());
      const xv = clamp(Math.round(xs.invert(mx)), xr[0], xr[1]);
      const rows = data.series.map(s => { const p = s.values.find(v => v[0] === xv); return p ? { s, v: p[1] } : null; }).filter(Boolean);
      if (!rows.length) { hide(); return; }
      hov.selectAll('*').remove();
      hov.append('line').attr('x1', xs(xv)).attr('x2', xs(xv)).attr('y1', m.t).attr('y2', H - m.b).attr('stroke', P.ink2).attr('stroke-opacity', 0.4);
      const node = clear(tip.node()); node.append(h('div', { class: 'd' }, opt.tipX(xv)));
      if (many) {
        let best = rows[0]; for (const r of rows) if (Math.abs(ys(r.v) - my) < Math.abs(ys(best.v) - my)) best = r;
        paths.attr('stroke', s => s === best.s ? P.accent : (s.color || P.muted)).attr('stroke-opacity', s => s === best.s ? 1 : 0.35).attr('stroke-width', s => s === best.s ? 2.5 : 1.2);
        paths.filter(s => s === best.s).raise();
        hov.append('circle').attr('cx', xs(xv)).attr('cy', ys(best.v)).attr('r', 4).attr('fill', P.accent).attr('stroke', P.surface).attr('stroke-width', 2);
        node.append(h('div', { class: 'r' }, h('span', { class: 'n' }, best.s.label), h('span', { class: 'v ' + (opt.signed ? sgn(best.v) : '') }, opt.vFmt(best.v))));
        if (best.s.sub) node.append(h('div', { class: 'muted', style: 'font-size:11.5px' }, best.s.sub));
      } else {
        rows.sort((p, q) => q.v - p.v);
        for (const r of rows) {
          hov.append('circle').attr('cx', xs(xv)).attr('cy', ys(r.v)).attr('r', 4).attr('fill', r.s.color || P.muted).attr('stroke', P.surface).attr('stroke-width', 2);
          node.append(h('div', { class: 'r' }, h('span', { class: 'n' }, h('i', { class: 'key', style: `background:${r.s.color || P.muted}` }), r.s.label), h('span', { class: 'v ' + (opt.signed ? sgn(r.v) : '') }, opt.vFmt(r.v))));
        }
      }
      tip.attr('hidden', null); const w = tip.node().offsetWidth; let left = xs(xv) + 14; if (left + w > W - 4) left = xs(xv) - w - 14;
      tip.style('left', Math.max(4, left) + 'px').style('top', (m.t + 4) + 'px');
    }).on('pointerleave', hide);
  }
  return { setData(d) { data = d; render(); }, render };
}

/* ================================================================ chart: race */
function RaceChart(host, cb) {
  const root = d3.select(host); const svg = root.append('svg');
  let items = [], kmax = 0, k = 0, timer = null, t0 = 0;
  const N = 12, barH = 22, gap = 6;
  function frame(anim) {
    const P = pal(); const W = Math.max(300, Math.round(host.getBoundingClientRect().width));
    const rows = items.map(it => ({ it, v: it.vals.get(k) })).filter(d => d.v != null);
    let shown = rows.slice().sort((p, q) => Math.abs(q.v) - Math.abs(p.v)).slice(0, N).sort((p, q) => q.v - p.v);
    const H = 34 + Math.max(1, shown.length) * (barH + gap) + 34;
    svg.attr('viewBox', `0 0 ${W} ${H}`).attr('height', H).attr('role', 'img');
    const nameW = Math.min(150, W * 0.3), m = { l: nameW + 12, r: 64, t: 26 };
    const vmax = d3.max(rows, d => Math.abs(d.v)) || 0.1;
    const lo = Math.min(0, d3.min(rows, d => d.v) ?? 0), hi = Math.max(0, d3.max(rows, d => d.v) ?? 0);
    const xs = d3.scaleLinear().domain([Math.min(lo, -vmax * 0.15), Math.max(hi, vmax * 0.15)]).nice().range([m.l, W - m.r]);
    const dur = anim ? 260 : 0;
    const g = svg.selectAll('g.root').data([0]).join('g').attr('class', 'root');
    const ax = g.selectAll('g.ax').data([0]).join('g').attr('class', 'ax');
    const tk = xs.ticks(4);
    ax.selectAll('line').data(tk, d => d).join('line').attr('y1', m.t - 4).attr('y2', H - 34).attr('stroke', d => d === 0 ? P.rule2 : P.rule).attr('stroke-width', d => d === 0 ? 1.25 : 1)
      .transition().duration(dur).attr('x1', d => xs(d)).attr('x2', d => xs(d));
    ax.selectAll('text').data(tk, d => d).join('text').attr('y', m.t - 10).attr('text-anchor', 'middle').attr('fill', P.muted).attr('font-size', 11).attr('font-family', 'IBM Plex Mono, ui-monospace, monospace')
      .text(d => pct(d, 0)).transition().duration(dur).attr('x', d => xs(d));
    const yOf = r => m.t + r * (barH + gap);
    const bars = g.selectAll('g.bar').data(shown, d => d.it.key);
    const be = bars.enter().append('g').attr('class', 'bar').attr('transform', `translate(0,${H})`).attr('opacity', 0);
    be.append('rect').attr('rx', 3); be.append('text').attr('class', 'nm'); be.append('text').attr('class', 'vl');
    bars.exit().transition().duration(dur).attr('opacity', 0).remove();
    const bm = be.merge(bars);
    bm.transition().duration(dur).ease(d3.easeLinear).attr('transform', (d, r) => `translate(0,${yOf(r)})`).attr('opacity', 1);
    bm.select('rect').attr('height', barH).attr('fill', d => stCol(d.it.stance, P)).attr('fill-opacity', 0.85)
      .transition().duration(dur).ease(d3.easeLinear).attr('x', d => Math.min(xs(0), xs(d.v))).attr('width', d => Math.max(1, Math.abs(xs(d.v) - xs(0))));
    bm.select('text.nm').attr('x', m.l - 8).attr('y', barH / 2 + 4).attr('text-anchor', 'end').attr('fill', P.ink).attr('font-size', 12.5)
      .text(d => { const s = d.it.label; const max = Math.floor(nameW / (S.lang === 'zh' ? 13 : 7)); return s.length > max ? s.slice(0, max - 1) + '…' : s; });
    bm.select('text.vl').attr('y', barH / 2 + 4).attr('font-size', 12).attr('font-family', 'IBM Plex Mono, ui-monospace, monospace').attr('fill', P.ink2)
      .attr('text-anchor', 'start').text(d => pct(d.v, 0))
      .transition().duration(dur).ease(d3.easeLinear).attr('x', d => d.v >= 0 ? xs(d.v) + 5 : xs(0) + 5);
    bm.selectAll('title').remove(); bm.append('title').text(d => `${d.it.label}: ${pct(d.v)}`);
    g.selectAll('text.big').data([0]).join('text').attr('class', 'big').attr('x', W - 8).attr('y', H - 10).attr('text-anchor', 'end')
      .attr('fill', P.muted).attr('font-size', W < 500 ? 16 : 22).attr('font-weight', 600).attr('font-family', 'IBM Plex Mono, ui-monospace, monospace')
      .text(t0 + k < NM ? `+${k} · ${M[t0 + k]}` : '');
    svg.attr('aria-label', cb.label(k));
    cb.onFrame(k, t0 + k < NM ? M[t0 + k] : '');
  }
  function tickF() { if (k >= kmax) { timer = null; cb.onState('done'); return; } k++; frame(true); timer = setTimeout(tickF, 280); }
  return {
    setData(its, t0_, km, kStart) { this.pause(); items = its; t0 = t0_; kmax = km; k = Math.min(kStart, km); svg.selectAll('g.bar').remove(); frame(false); },
    play() { if (timer) { this.pause(); return; } if (k >= kmax) k = 0; cb.onState('playing'); frame(false); timer = setTimeout(tickF, 280); },
    pause() { if (timer) { clearTimeout(timer); timer = null; cb.onState('paused'); } },
    render() { frame(false); }
  };
}

/* ================================================================ chart: win rate vs placebo */
function WinChart(host) {
  const root = d3.select(host); const svg = root.append('svg'); const tip = root.append('div').attr('class', 'c-tip').attr('hidden', '');
  let rows = [];
  function render() {
    const P = pal(); const W = Math.max(300, Math.round(host.getBoundingClientRect().width)); const H = 260;
    svg.attr('viewBox', `0 0 ${W} ${H}`).attr('height', H).attr('role', 'img'); svg.selectAll('*').remove();
    const m = { l: 42, r: 10, t: 16, b: 40 };
    const xs = d3.scaleBand().domain(rows.map(r => String(r.h))).range([m.l, W - m.r]).padding(0.3);
    const ys = d3.scaleLinear().domain([0, 1]).range([H - m.b, m.t]);
    const g = svg.append('g');
    for (const v of [0, 0.25, 0.5, 0.75, 1]) {
      g.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', ys(v)).attr('y2', ys(v)).attr('stroke', v === 0.5 ? P.rule2 : P.rule).attr('stroke-width', v === 0.5 ? 1.25 : 1);
      g.append('text').attr('x', m.l - 6).attr('y', ys(v) + 4).attr('text-anchor', 'end').attr('fill', P.muted).attr('font-size', 11).attr('font-family', 'IBM Plex Mono, ui-monospace, monospace').text(pct0(v));
    }
    for (const r of rows) {
      const cx = xs(String(r.h)) + xs.bandwidth() / 2;
      g.append('text').attr('x', cx).attr('y', H - m.b + 16).attr('text-anchor', 'middle').attr('fill', P.ink2).attr('font-size', 11.5).text(`${r.h} ${t('bt.h1')}`);
      g.append('text').attr('x', cx).attr('y', H - m.b + 30).attr('text-anchor', 'middle').attr('fill', P.muted).attr('font-size', 10.5).attr('font-family', 'IBM Plex Mono, ui-monospace, monospace').text(`n=${r.n}`);
      if (r.p05 != null) {
        g.append('line').attr('x1', cx - 9).attr('x2', cx - 9).attr('y1', ys(r.p05)).attr('y2', ys(r.p95)).attr('stroke', P.muted).attr('stroke-opacity', 0.45).attr('stroke-width', 6).attr('stroke-linecap', 'round');
        g.append('circle').attr('cx', cx - 9).attr('cy', ys(r.pmed)).attr('r', 3.5).attr('fill', P.muted).attr('stroke', P.surface).attr('stroke-width', 1.5);
      }
      if (r.win != null) {
        if (r.lo != null) g.append('line').attr('x1', cx + 9).attr('x2', cx + 9).attr('y1', ys(r.lo)).attr('y2', ys(r.hi)).attr('stroke', P.accent).attr('stroke-width', 1.5);
        g.append('circle').attr('cx', cx + 9).attr('cy', ys(r.win)).attr('r', 5).attr('fill', P.accent).attr('stroke', P.surface).attr('stroke-width', 2);
        g.append('text').attr('x', cx + 18).attr('y', ys(r.win) + 4).attr('fill', P.ink).attr('font-size', 11.5).attr('font-weight', 600).text(pct0(r.win));
      }
      g.append('rect').attr('x', xs(String(r.h)) - 6).attr('y', m.t).attr('width', xs.bandwidth() + 12).attr('height', H - m.t - m.b).attr('fill', 'transparent')
        .on('pointerenter', () => {
          const node = clear(tip.node());
          node.append(h('div', { class: 'd' }, `${r.h} ${t('bt.h1')} · n=${r.n}`));
          node.append(h('div', { class: 'r' }, h('span', { class: 'n' }, t('bt.wr')), h('span', { class: 'v' }, `${pct0(r.win)} [${pct0(r.lo)}, ${pct0(r.hi)}]`)));
          node.append(h('div', { class: 'r' }, h('span', { class: 'n' }, t('main.perm')), h('span', { class: 'v' }, `${pct0(r.pmed)} [${pct0(r.p05)}, ${pct0(r.p95)}]`)));
          node.append(h('div', { class: 'r' }, h('span', { class: 'n' }, t('main.p')), h('span', { class: 'v' }, pFmt(r.p))));
          tip.attr('hidden', null); const w = tip.node().offsetWidth; let left = cx + 16; if (left + w > W) left = cx - w - 16;
          tip.style('left', Math.max(4, left) + 'px').style('top', '10px');
        }).on('pointerleave', () => tip.attr('hidden', ''));
    }
  }
  return { setData(r) { rows = r; render(); }, render };
}

/* ================================================================ app state + chrome */
function applyStatic() {
  document.documentElement.lang = S.lang === 'zh' ? 'zh-CN' : 'en';
  document.body.classList.toggle('conv-cn', S.conv === 'cn'); document.body.classList.toggle('conv-intl', S.conv !== 'cn');
  document.querySelectorAll('[data-i18n]').forEach(el => { const v = t(el.dataset.i18n); if (typeof v === 'string') el.textContent = v; });
  $('#langZh').setAttribute('aria-pressed', S.lang === 'zh'); $('#langEn').setAttribute('aria-pressed', S.lang === 'en');
  $('#convCn').setAttribute('aria-pressed', S.conv === 'cn'); $('#convIntl').setAttribute('aria-pressed', S.conv !== 'cn');
  $('#scLog').setAttribute('aria-pressed', S.scale === 'log'); $('#scLin').setAttribute('aria-pressed', S.scale !== 'log');
  $('#indSearch').placeholder = t('ind.search');
  const m = D.meta || {};
  $('.docno').firstElementChild.textContent = t('mast.k1', m.first || M[0], m.last || M[NM - 1]);
  $('#mastCount').textContent = t('mast.count', EV.length);
  $('#kSource').textContent = t('k.src');
  const P = pal();
  const leg = clear($('#kLegend'));
  for (const s of ['S+', 'S0', 'R-supply', 'R-demand']) leg.append(h('span', null, h('span', { class: 'g g-' + STC[s] }, GLY[s]), t('st.' + s)));
  leg.append(h('span', null, h('span', { style: `display:inline-block;width:8px;height:10px;border:1px solid ${P.up};background:${S.conv === 'cn' ? 'transparent' : P.up}` }), t('leg.up')));
  leg.append(h('span', null, h('span', { style: `display:inline-block;width:8px;height:10px;background:${P.dn}` }), t('leg.dn')));
  setPlayLabel(kchart && kchart.playing() ? 'playing' : kchart && kchart.paused() ? 'paused' : 'done');
}

/* ---------------- overview */
function wr(subset, rule, hz) { return RES && RES.win_rates ? RES.win_rates.find(r => r.subset === subset && r.rule === rule && r.h === hz) : null; }
function renderOverview() {
  const f = clear($('#finding')), tiles = clear($('#tiles')), note = $('#tileNote');
  const a = wr('FYP_proposal', 'S+', 36), a12 = wr('FYP_proposal', 'S+', 12), b = wr('all', 'R-demand', 36);
  const P2 = RES && RES.portfolios ? RES.portfolios.P2 : null, P3 = RES && RES.portfolios ? RES.portfolios.P3 : null;
  const pre = RES && RES.pre_drift ? RES.pre_drift.find(r => r.group === 'S+ FYP_proposal' && r.window === 3) : null;
  const tv = RES && RES.turnover ? RES.turnover.find(r => r.group === 'S+ FYP_proposal') : null;
  const Z = S.lang === 'zh';
  const tk = clear($('#takeaways'));
  if (!a) { f.textContent = t('pending'); note.textContent = ''; }
  else {
    const sig = a.p_perm_win != null && a.p_perm_win < 0.05;
    if (Z) {
      f.append('按五年规划建议的「扶持」措辞买入对应的申万行业指数、持有三年：', h('b', null, `${a.n} 次里只有 ${pct0(a.win_rate)} 跑赢申万A指`),
        `，平均超额 ${pct(a.mean_bhar)}。同一时点随机换成其他行业，胜率中位数是 ${pct0(a.perm_win_median)}`,
        sig ? `，差距显著（p = ${pFmt(a.p_perm_win)}）。` : `（p = ${pFmt(a.p_perm_win)}）。扶持措辞没有提前标出赢家`,
        a12 && !sig ? `；第一年更差，12 个月胜率只有 ${pct0(a12.win_rate)}。` : '。');
    } else {
      f.append('Buying the SW index of each industry a Five-Year Plan proposal supports and holding it for three years ', h('b', null, `beat SW All-A in only ${pct0(a.win_rate)} of ${a.n} cases`),
        `, with an average excess return of ${pct(a.mean_bhar)}. Random industries on the same dates won ${pct0(a.perm_win_median)} of the time`,
        sig ? ` and the gap is significant (p = ${pFmt(a.p_perm_win)}).` : ` (p = ${pFmt(a.p_perm_win)}). Supportive wording did not pick winners in advance`,
        a12 && !sig ? `, and the first year was worse: a 12-month win rate of just ${pct0(a12.win_rate)}.` : '.');
    }
    note.textContent = Z
      ? '胜率：文件全文发布后第一个月末买入、持有至第 36 个月末，行业指数涨幅超过申万A指的比例。随机对照：同日期随机换成其他行业，重复 2,000 次；p 值为单侧，越接近 1 说明越不像有效信号。'
      : 'Win rate: share of cases where the industry index, bought at the first month-end after the text was published and held 36 months, rose more than SW All-A. Placebo: the same dates with randomly substituted industries, 2,000 draws; one-sided p-values, where values near 1 mean the signal looks no better than chance.';
    const items = Z ? [
      ['扶持没有变成超额收益。', `被五年规划点名扶持的行业，三年后跑赢和跑输的概率与随机挑行业相当；前 1、3、6、12 个月甚至系统性落后（12 个月平均 ${pct(a12 ? a12.mean_bhar : null)}）。这个落后是事后观察到的，预登记只检验了"跑赢"方向，所以只作探索性结论。`],
      ['约束也没有标出输家。', `被"需求/监管约束"点名的行业，三年平均超额 ${pct(b ? b.mean_bhar : null)}；"扶持多、约束空"的组合年化 ${pct(P3 ? P3.ann_excess : null)}，回避被约束的行业反而吃亏。`],
      ['唯一的亮点是描述性的。', `持续持有所有出现过扶持措辞的行业 36 个月（组合 P2），年化超额 ${pct(P2 ? P2.ann_excess : null)}、信息比率 ${P2 ? P2.info_ratio.toFixed(2) : '—'}；但单个事件的中位数为负，收益集中在少数大赢家，且这一项没有预登记显著性检验。`],
      ['发布前后没有看到资金涌入。', `扶持行业在建议发布前 3 个月平均落后 ${pre ? (Math.abs(pre.mean_pre) * 100).toFixed(1) + "%" : "—"}，发布后一年成交额占全A的比例反而下降 ${tv ? Math.abs(tv.change_pp_1_12 * 100).toFixed(2) : '—'} 个百分点。`],
      ['回到李录的框架。', '被扶持的行业是"目标"所在，但目标往往靠大量投资、产能扩张和价格竞争实现，利润被摊薄，代价可能恰恰落在这些行业的股东身上。这是一种解释，本研究没有直接检验它。']
    ] : [
      ['Support did not turn into excess returns.', `Industries a Five-Year Plan singled out for support were as likely to beat the market over three years as randomly picked ones, and lagged systematically at 1, 3, 6 and 12 months (12-month mean ${pct(a12 ? a12.mean_bhar : null)}). The lag was observed after the fact; the pre-registered test only looked for outperformance, so treat it as exploratory.`],
      ['Restrictions did not flag losers either.', `Industries named for demand or regulatory curbs averaged ${pct(b ? b.mean_bhar : null)} excess over three years; a portfolio long supported and short curbed industries returned ${pct(P3 ? P3.ann_excess : null)} a year, so avoiding curbed industries cost money.`],
      ['The one bright spot is descriptive.', `Holding every industry with a supportive statement for 36 months (portfolio P2) earned ${pct(P2 ? P2.ann_excess : null)} a year over the benchmark, information ratio ${P2 ? P2.info_ratio.toFixed(2) : '—'}. But the median event was negative, gains came from a few big winners, and this had no pre-registered significance test.`],
      ['No sign of money rushing in.', `Supported industries lagged by ${pre ? (Math.abs(pre.mean_pre) * 100).toFixed(1) + "%" : "—"} on average in the three months before a proposal was published, and their share of A-share turnover fell by ${tv ? Math.abs(tv.change_pp_1_12 * 100).toFixed(2) : '—'} percentage points in the following year.`],
      ['Back to Li Lu’s framing.', 'Supported industries are where the targets sit, but targets are usually met through heavy investment, new capacity and price competition, which thin out profits; the cost may land on those industries’ own shareholders. That is an interpretation; this study does not test it directly.']
    ];
    for (const [hd, tx] of items) tk.append(h('li', null, h('b', null, hd), ' ', tx));
  }
  const tile = (lab, val, sub, cls) => h('div', { class: 'tile' }, h('div', { class: 'lab' }, lab), h('div', { class: 'val ' + (cls || '') }, val), h('div', { class: 'sub' }, sub));
  tiles.append(
    tile(Z ? '五年规划「扶持」→ 三年胜率' : 'FYP "support" → 3-year win rate', a ? pct0(a.win_rate) : '—', a ? (Z ? `随机行业 ${pct0(a.perm_win_median)} · p = ${pFmt(a.p_perm_win)} · n = ${a.n}` : `random industries ${pct0(a.perm_win_median)} · p = ${pFmt(a.p_perm_win)} · n = ${a.n}`) : t('pending')),
    tile(Z ? '第一年（12 个月）胜率' : 'First-year (12-month) win rate', a12 ? pct0(a12.win_rate) : '—', a12 ? (Z ? `平均超额 ${pct(a12.mean_bhar)} · 随机行业 ${pct0(a12.perm_win_median)}` : `mean excess ${pct(a12.mean_bhar)} · random ${pct0(a12.perm_win_median)}`) : ''),
    tile(Z ? '被「需求/监管约束」的行业，三年平均超额' : 'Demand/regulatory-curbed industries, 3-year mean excess', b ? pct(b.mean_bhar) : '—', b ? (Z ? `回避它们的胜率 ${pct0(b.win_rate)} · n = ${b.n}` : `avoiding them won ${pct0(b.win_rate)} · n = ${b.n}`) : '', b ? sgn(b.mean_bhar) : ''),
    tile(Z ? '持有全部扶持行业（P2）年化超额' : 'Holding all supported industries (P2), annual excess', P2 ? pct(P2.ann_excess) : '—', P2 ? (Z ? `信息比率 ${P2.info_ratio.toFixed(2)} · 描述性，未预登记检验` : `info ratio ${P2.info_ratio.toFixed(2)} · descriptive, not pre-registered`) : '', P2 ? sgn(P2.ann_excess) : '')
  );
  /* target vs cost */
  const tc = clear($('#targetCost'));
  const count = (pred) => { const m = new Map(); for (const e of EV) if (pred(e)) for (const c of (e.l1 || [])) m.set(c, (m.get(c) || 0) + 1); return Array.from(m.entries()).sort((p, q) => q[1] - p[1]).slice(0, 6); };
  const col = (hd, rows, st) => h('div', null, h('div', { class: 'hd' }, hd), h('ul', null, rows.map(([c, n]) => h('li', null, h('span', { class: 'g g-' + STC[st] }, GLY[st]),
    h('a', { href: '#industry', onclick: () => { S.ind = c; S.range = 'all'; renderIndustry(); } }, idxName(c)), h('span', { class: 'muted mono', style: 'font-size:12px' }, t('tc.n', n))))));
  tc.append(col(t('tc.t'), count(e => e.stance === 'S+'), 'S+'), col(t('tc.c'), count(e => e.stance === 'R-supply' || e.stance === 'R-demand'), 'R-demand'));
  /* plan strip */
  const ps = clear($('#planStrip'));
  for (const p of PLANS) {
    const terms = EV.filter(e => e.plan === p.id && e.type === 'FYP_proposal' && (e.change === 'new' || (p.id === PLANS[0].id && e.intensity >= 3)) && e.stance === 'S+')
      .sort((x1, x2) => (x2.intensity || 0) - (x1.intensity || 0)).slice(0, 4);
    const curbs = EV.filter(e => e.plan === p.id && e.type === 'FYP_proposal' && (e.stance === 'R-supply' || e.stance === 'R-demand') && (e.change === 'new' || e.change === 'up')).slice(0, 2);
    ps.append(h('button', { type: 'button', onclick: () => { S.plan = p.id; store.set('plan', S.plan); renderPlan(); document.getElementById('plans').scrollIntoView({ behavior: 'smooth' }); } },
      h('span', { class: 'pn' }, planName(p)), h('span', { class: 'py' }, `${p.y0}–${p.y1}`),
      h('span', { class: 'terms' }, terms.concat(curbs).map(e => h('span', { class: 'chip' }, h('span', { class: 'g g-' + STC[e.stance] }, GLY[e.stance]), evConcept(e))))));
  }
}

/* ---------------- industry */
let kchart = null;
function setPlayLabel(s) { const b = $('#playBtn'); if (!b) return; b.textContent = s === 'playing' ? t('ind.pause') : s === 'paused' ? t('ind.resume') : t('ind.play'); }
function renderRail() {
  const ul = clear($('#indList')), q = ($('#indSearch').value || '').trim().toLowerCase();
  const sel = clear($('#indSelect'));
  const P = pal();
  for (const c of L1) {
    const X = IDX[c]; const n = evsFor(c).length;
    sel.append(h('option', { value: c, selected: c === S.ind || IDX[S.ind].p === c }, `${idxName(c)}（${n}）`));
    if (q && !(X.zh.includes(q) || X.en.toLowerCase().includes(q) || c.includes(q))) continue;
    const btn = h('button', { type: 'button', 'aria-current': (c === S.ind || IDX[S.ind].p === c) ? 'true' : 'false', onclick: () => { S.ind = c; S.range = 'all'; S.sel = null; store.set('ind', c); renderIndustry(); } },
      h('span', { class: 'nm' }, idxName(c)), h('span', { class: 'ct' }, n || ''));
    btn.append(sparkline(c, P));
    ul.append(h('li', null, btn));
  }
}
function sparkline(c, P) {
  const X = IDX[c], B = IDX[BENCH]; const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg'); svg.setAttribute('viewBox', '0 0 100 20'); svg.setAttribute('preserveAspectRatio', 'none'); svg.setAttribute('aria-hidden', 'true');
  const s = firstIdx(X, 0); const pts = [];
  for (let i = s; i < NM; i += 2) if (X.c[i] != null && B.c[i] != null) pts.push([i, Math.log(X.c[i] / B.c[i])]);
  if (pts.length < 2) return svg;
  const xs = d3.scaleLinear().domain([0, NM - 1]).range([0, 100]); const ys = d3.scaleLinear().domain(d3.extent(pts, p => p[1])).range([18, 2]);
  const p = document.createElementNS(ns, 'path'); p.setAttribute('d', d3.line().x(d => xs(d[0])).y(d => ys(d[1]))(pts));
  p.setAttribute('fill', 'none'); p.setAttribute('stroke', P.muted); p.setAttribute('stroke-width', '1.2'); p.setAttribute('vector-effect', 'non-scaling-stroke');
  svg.append(p);
  for (const e of evsFor(c)) {
    const mi = evMonth(e); if (mi < s || mi >= NM || e.intensity < 3) continue;
    const dot = document.createElementNS(ns, 'rect'); dot.setAttribute('x', xs(mi) - 0.6); dot.setAttribute('y', e.stance === 'S+' ? 0 : 17); dot.setAttribute('width', 1.2); dot.setAttribute('height', 3);
    dot.setAttribute('fill', stCol(e.stance, P)); svg.append(dot);
  }
  return svg;
}
function renderIndustry() {
  if (kchart) kchart.stop(true);
  renderRail();
  const code = S.ind, X = IDX[code];
  const l1code = X.lvl === 1 ? code : X.p;
  $('#indName').textContent = idxName(code) + (X.lvl === 2 ? (S.lang === 'zh' ? `（${idxName(X.p)}）` : ` (${idxName(X.p)})`) : '');
  $('#indMeta').textContent = t('ind.meta', code, X.lvl, M[firstIdx(X, 0)]);
  const l2 = clear($('#l2row'));
  const kids = Object.keys(IDX).filter(c => IDX[c].lvl === 2 && IDX[c].p === l1code);
  if (kids.length) {
    l2.append(h('button', { type: 'button', class: 'chip', 'aria-pressed': code === l1code, onclick: () => { S.ind = l1code; S.sel = null; store.set('ind', S.ind); renderIndustry(); } }, t('ind.l1all')));
    for (const c of kids) {
      const n = evsFor(c).length;
      l2.append(h('button', { type: 'button', class: 'chip', 'aria-pressed': code === c, title: `${c} · ${M[firstIdx(IDX[c], 0)]}`, onclick: () => { S.ind = c; S.sel = null; store.set('ind', S.ind); renderIndustry(); } },
        idxName(c), n ? h('span', { class: 'mono', style: 'opacity:.7' }, n) : null));
    }
  }
  const rg = clear($('#ranges'));
  rg.append(h('button', { type: 'button', class: 'btn sm', 'aria-pressed': S.range === 'all', onclick: () => { S.range = 'all'; renderIndustry(); } }, t('range.all')));
  for (const p of PLANS) rg.append(h('button', { type: 'button', class: 'btn sm', 'aria-pressed': S.range === p.id, onclick: () => { S.range = p.id; renderIndustry(); } }, planName(p)));
  const [i0, i1, isEmpty] = rangeFor(code);
  const evs = evsFor(code);
  if (kchart) kchart.setData(code, isEmpty ? i0 : i0, i1, evs, isEmpty ? t('k.empty', idxName(code), M[firstIdx(X, 0)]) : null);
  if (kchart && S.sel && evs.some(e => e.id === S.sel)) kchart.select(S.sel);
  renderEvents(code, i0, i1);
  if ($('#kTableD').open) renderKTable();
  setPlayLabel('done');
}
function outcomeBits(e) {
  const bits = [];
  if (e.excl) { bits.push(h('span', { class: 'muted', style: 'font-family:inherit' }, t('ev.na'))); return bits; }
  const w36 = winOf(e, 36);
  bits.push(h('span', null, h('span', { class: 'k' }, t('ev.o12')), h('span', { class: sgn(e.b12) }, pct(e.b12))));
  bits.push(h('span', null, h('span', { class: 'k' }, t('ev.o36')), e.b36 == null ? h('span', { class: 'muted', style: 'font-family:inherit' }, t('ev.inc')) : h('span', { class: sgn(e.b36) }, pct(e.b36)),
    w36 == null ? null : h('span', { class: 'mark ' + (w36 ? 'w' : 'l') }, w36 ? '✓ ' + t('ev.win') : '✗ ' + t('ev.loss'))));
  if (e.pre12 != null) bits.push(h('span', null, h('span', { class: 'k' }, t('ev.pre')), h('span', { class: sgn(e.pre12) }, pct(e.pre12))));
  return bits;
}
function renderEvents(code, i0, i1) {
  const box = clear($('#evCards'));
  let evs = evsFor(code);
  const inRange = S.range === 'all' ? evs : evs.filter(e => { const mi = evMonth(e); return mi >= i0 && mi <= i1; });
  $('#evTitle').textContent = t('ev.title', idxName(code), inRange.length);
  $('#evHint').textContent = S.range === 'all' ? t('ev.hint') : t('ev.rangeOnly', planName(PLANBY.get(S.range)));
  if (!inRange.length) { box.append(h('p', { class: 'muted' }, t('ev.empty'))); return; }
  const cntOf = f => inRange.filter(e => f === 'all' || (f === 'S0' ? e.stance === 'S0' : f === 'S+' ? e.stance === 'S+' : e.stance.startsWith('R'))).length;
  if (!['all', 'S+', 'R', 'S0'].includes(S.evf)) S.evf = 'main';
  const fbar = h('div', { class: 'evfilter', role: 'group' });
  for (const [k, lab] of [['main', t('evf.main')], ['S+', t('st.S+')], ['R', t('evf.R')], ['S0', t('st.S0')], ['all', t('evf.all')]]) {
    const n = k === 'main' ? inRange.filter(e => e.stance !== 'S0').length : cntOf(k);
    fbar.append(h('button', { type: 'button', class: 'chip', 'aria-pressed': S.evf === k, onclick: () => { S.evf = k; S.evMore = false; renderEvents(code, i0, i1); } }, lab, h('span', { class: 'mono', style: 'opacity:.7' }, n)));
  }
  box.append(fbar);
  const shown = inRange.filter(e => S.evf === 'all' ? true : S.evf === 'main' ? e.stance !== 'S0' : S.evf === 'S0' ? e.stance === 'S0' : S.evf === 'S+' ? e.stance === 'S+' : e.stance.startsWith('R'));
  const LIMIT = 14;
  const list = S.evMore || shown.length <= LIMIT + 4 ? shown : shown.slice(0, LIMIT);
  for (const e of list) {
    const seriesTxt = e.series ? t('ev.series', e.series.split(';').map(idxName).join(' + '), e.series, e.level || '') : '';
    const art = h('article', { class: 'ev', 'aria-selected': S.sel === e.id ? 'true' : 'false', tabindex: 0, 'data-id': e.id,
      onclick: ev => { if (ev.target.closest('a')) return; selectEvent(e.id); }, onkeydown: ev => { if (ev.key === 'Enter') selectEvent(e.id); } },
      h('time', { datetime: e.date }, e.date),
      h('div', { style: 'min-width:0' },
        h('div', { class: 'top' }, h('span', { class: 'concept' }, evConcept(e)),
          h('span', { class: 'chip' }, h('span', { class: 'g g-' + STC[e.stance] }, GLY[e.stance]), t('st.' + e.stance)),
          e.change && e.change !== 'na' && t('ch.' + e.change) ? h('span', { class: 'chip' }, t('ch.' + e.change)) : null,
          h('span', { class: 'doc' }, `${t('dt.' + e.type)} · ${evDoc(e)}`)),
        h('blockquote', null, `“${evQuote(e) || ''}”`),
        evAltQuote(e) ? h('div', { class: 'alt' }, e.q_zh) : null,
        e.prev_zh ? h('div', { class: 'prev' }, t('ev.prev'), `“${e.prev_zh}”`) : null,
        h('div', { class: 'out' }, outcomeBits(e)),
        e.stance === 'R-supply' && !e.excl ? h('div', { class: 'src' }, t('ev.hb')) : null,
        h('div', { class: 'src' }, seriesTxt, seriesTxt && e.url ? ' · ' : '', e.url ? h('a', { href: e.url, target: '_blank', rel: 'noopener' }, t('ev.source')) : null)));
    box.append(art);
  }
  if (list.length < shown.length) box.append(h('button', { type: 'button', class: 'btn', style: 'margin:12px 0 0 8px', onclick: () => { S.evMore = true; renderEvents(code, i0, i1); } }, t('evf.more', shown.length - list.length)));
}
function selectEvent(id) {
  S.sel = id;
  document.querySelectorAll('#evCards .ev').forEach(el => el.setAttribute('aria-selected', el.dataset.id === id ? 'true' : 'false'));
  const e = EVBYID.get(id); if (!e) return;
  if (S.range !== 'all') { const [a, b] = rangeFor(S.ind); const mi = evMonth(e); if (mi < a || mi > b) { S.range = 'all'; renderIndustry(); } }
  if (kchart) kchart.select(id);
  let card = document.querySelector(`#evCards .ev[data-id="${CSS.escape(id)}"]`);
  if (!card) { S.evf = 'all'; S.evMore = true; const [a, b] = rangeFor(S.ind); renderEvents(S.ind, a, b); card = document.querySelector(`#evCards .ev[data-id="${CSS.escape(id)}"]`); }
  const kw = $('#kwrap').getBoundingClientRect();
  if (kw.bottom < 60 || kw.top > innerHeight) $('#kwrap').scrollIntoView({ behavior: 'smooth', block: 'center' });
  else if (card) card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
function renderKTable() {
  const box = clear($('#kTable')), X = IDX[S.ind], B = IDX[BENCH];
  const tbl = h('table', { class: 'tbl' });
  const Z = S.lang === 'zh';
  tbl.append(h('thead', null, h('tr', null, [Z ? '月份' : 'Month', t('tip.o'), t('tip.h'), t('tip.l'), t('tip.c'), t('tip.chg'), Z ? '超额' : 'Excess', t('tip.ts')].map((s, i) => h('th', { class: i ? 'r' : '' }, s)))));
  const tb = h('tbody');
  for (let i = NM - 1; i >= 0; i--) {
    if (X.c[i] == null) continue;
    const chg = X.c[i - 1] != null ? X.c[i] / X.c[i - 1] - 1 : null, bc = B.c[i - 1] != null ? B.c[i] / B.c[i - 1] - 1 : null;
    tb.append(h('tr', null, h('td', { class: 'mono' }, M[i]), h('td', { class: 'r mono' }, num(X.o[i], 1)), h('td', { class: 'r mono' }, num(X.h[i], 1)), h('td', { class: 'r mono' }, num(X.l[i], 1)), h('td', { class: 'r mono' }, num(X.c[i], 1)),
      h('td', { class: 'r mono ' + sgn(chg) }, pct(chg)), h('td', { class: 'r mono ' + sgn(chg != null && bc != null ? chg - bc : null) }, chg != null && bc != null ? pct(chg - bc) : '—'), h('td', { class: 'r mono' }, X.t[i] != null ? X.t[i].toFixed(2) + '%' : '—')));
  }
  tbl.append(tb); box.append(tbl);
}

/* ---------------- plans */
function avgSeries(items, P) {
  const sp = items.filter(it => it.stance === 'S+'); if (sp.length < 2) return [];
  const by = new Map();
  for (const it of sp) for (const [k, v] of it.path) { if (!by.has(k)) by.set(k, []); by.get(k).push(v); }
  const vals = Array.from(by.entries()).filter(([, a]) => a.length >= Math.max(2, sp.length * 0.5)).map(([k, a]) => [k, a.reduce((x, y) => x + y, 0) / a.length]).sort((p, q) => p[0] - q[0]);
  return [{ key: 'avg', label: t('pl.avg'), sub: t('pl.avgSub', sp.length), values: vals, color: P.accent, width: 2.8, always: true }];
}
let race = null, plines = null;
function planEvents(pid) { return EV.filter(e => e.plan === pid && (e.type === 'FYP_proposal' || e.type === 'FYP_outline')); }
function renderPlan() {
  const p = PLANBY.get(S.plan); if (!p) return;
  const tabs = clear($('#ptabs'));
  for (const q of PLANS) tabs.append(h('button', { type: 'button', role: 'tab', 'aria-selected': q.id === p.id, onclick: () => { S.plan = q.id; store.set('plan', q.id); renderPlan(); } },
    h('span', { class: 'a' }, planName(q)), h('span', { class: 'b' }, `${q.y0}–${q.y1}`)));
  const evs = planEvents(p.id), props = evs.filter(e => e.type === 'FYP_proposal');
  const tested = evs.filter(e => !e.excl && e.series).length;
  const ph = clear($('#phead'));
  ph.append(h('h3', null, `${planName(p)} · ${p.y0}–${p.y1}`),
    h('div', { class: 'facts' },
      h('span', null, t('pl.proposal'), ' ', h('b', null, p.proposal || '—')),
      p.outline ? h('span', null, t('pl.outline'), ' ', h('b', null, p.outline)) : null,
      h('span', null, t('pl.coded'), ' ', h('b', null, evs.length)),
      h('span', null, t('pl.tested'), ' ', h('b', null, tested))));
  /* shifts */
  const sh = clear($('#shifts')); const q = clear($('#qcmp'));
  q.append(h('div', { class: 't' }, PLANS[0] && p.id === PLANS[0].id ? t('pl.first') : t('pl.qempty')));
  for (const col of ['new', 'up', 'down', 'dropped']) {
    const list = props.filter(e => e.change === col);
    const chips = list.map(e => h('button', { type: 'button', class: 'chip', 'aria-pressed': 'false', onclick: ev => {
      sh.querySelectorAll('button.chip').forEach(b => b.setAttribute('aria-pressed', 'false')); ev.currentTarget.setAttribute('aria-pressed', 'true'); showCompare(e);
    } }, h('span', { class: 'g g-' + STC[e.stance] }, GLY[e.stance]), evConcept(e)));
    sh.append(h('div', { class: 'col' }, h('h4', null, `${t('pl.col.' + col)} · ${list.length}`), h('div', { class: 'chips' }, chips.length ? chips : h('span', { class: 'empty' }, t('pl.none')))));
  }
  function showCompare(e) {
    clear(q);
    q.append(h('div', { class: 't' }, `${evConcept(e)} · ${t('st.' + e.stance)} · ${t('ch.' + e.change)}`));
    q.append(h('div', { class: 'pair' },
      h('span', null, t('pl.qprev')), e.prev_zh ? h('q', null, e.prev_zh) : h('span', { class: 'muted' }, t('pl.qnone')),
      h('span', null, t('pl.qnow')), e.change === 'dropped' ? h('span', { class: 'muted' }, t('pl.qnone')) : h('q', null, e.q_zh || ''),
      S.lang === 'en' && e.q_en && e.change !== 'dropped' ? h('span', null, 'EN') : null, S.lang === 'en' && e.q_en && e.change !== 'dropped' ? h('span', { class: 'muted' }, e.q_en) : null));
    q.append(h('div', { class: 'out', style: 'margin-top:8px;display:flex;gap:4px 14px;flex-wrap:wrap;font-family:var(--font-mono);font-size:12.5px' }, outcomeBits(e)));
  }
  /* tracked series */
  const tr = evs.filter(e => !e.excl && e.series && e.entry && MI.has(e.entry) && (e.stance === 'S+' || e.stance === 'R-supply' || e.stance === 'R-demand'));
  const bySeries = new Map();
  for (const e of tr) { const k = e.series; if (!bySeries.has(k)) bySeries.set(k, []); bySeries.get(k).push(e); }
  const t0 = MI.get((props[0] && props[0].entry) || (tr[0] && tr[0].entry)) ?? null;
  const planEnd = MI.has(`${p.y1}-12`) ? MI.get(`${p.y1}-12`) : NM - 1;
  const kmaxAll = t0 != null ? Math.min(96, NM - 1 - t0) : 0;
  const items = [];
  for (const [k, list] of bySeries) {
    list.sort((x1, x2) => (x2.intensity || 0) - (x1.intensity || 0));
    const lead = list[0]; const codes = k.split(';'); const tt = MI.get(lead.entry);
    const path = excessPath(codes, tt, -12, Math.min(96, NM - 1 - tt));
    const label = codes.map(idxName).join('+');
    items.push({ key: k, label, stance: lead.stance, concepts: list.map(evConcept).join('、'), path, vals: new Map(path.filter(d => d[0] >= 0)), t0: tt });
  }
  const P = pal();
  if (plines) {
    if (!items.length || t0 == null) { plines.setData({ series: [], xDomain: [-12, 36] }); $('#plines').querySelector('svg').setAttribute('height', 40); }
    plines.setData({
      title: t('pl.lines'),
      xDomain: [-12, Math.max(12, kmaxAll)], refY: 0, endLabels: true, yInclude: [0],
      vbands: t0 != null ? [{ x0: Math.max(-12, MI.get(`${p.y0}-01`) - t0), x1: planEnd - t0, label: planName(p) }] : [],
      vlines: [{ x: 0, label: S.lang === 'zh' ? '入场' : 'Entry' }, { x: 36, label: '+36' }],
      series: items.map(it => ({ key: it.key, label: it.label, sub: it.concepts, values: it.path, color: it.stance === 'S+' ? P.muted : stCol(it.stance, P), dim: true })).concat(avgSeries(items, P))
    });
  }
  if (race) {
    race.setData(items, t0 ?? 0, Math.max(0, kmaxAll), Math.min(36, Math.max(0, kmaxAll)));
  }
  $('#racePlay').textContent = '▶';
  /* scorecard */
  const tbl = clear($('#scorecard'));
  tbl.append(h('caption', null, t('sc.cap')));
  tbl.append(h('thead', null, h('tr', null, ['sc.concept', 'sc.stance', 'sc.change', 'sc.int', 'sc.series', 'sc.b12', 'sc.b36', 'sc.plan', 'sc.res'].map((k, i) => h('th', { class: i >= 5 && i <= 7 ? 'r' : '' }, t(k))))));
  const tb = h('tbody');
  const order = { 'S+': 0, 'S0': 1, 'R-supply': 2, 'R-demand': 3 };
  const scAll = S.scAll === S.plan;
  const pool = evs.filter(e => scAll || (e.type === 'FYP_proposal' && e.stance !== 'S0'));
  const sorted = pool.slice().sort((x1, x2) => ((x2.b36 ?? -9) - (x1.b36 ?? -9)) || (order[x1.stance] - order[x2.stance]));
  const SC_LIMIT = 30;
  const scList = S.scMore === S.plan || sorted.length <= SC_LIMIT + 5 ? sorted : sorted.slice(0, SC_LIMIT);
  for (const e of scList) {
    let toEnd = null;
    if (!e.excl && e.series && e.entry && MI.has(e.entry)) { const tt = MI.get(e.entry); const kk = Math.min(planEnd, NM - 1) - tt; if (kk > 0) { const pth = excessPath(e.series.split(';'), tt, 0, kk); const lastp = pth[pth.length - 1]; toEnd = lastp && lastp[0] === kk ? lastp[1] : null; } }
    const w = winOf(e, 36);
    tb.append(h('tr', null,
      h('td', null, evConcept(e), e.type === 'FYP_outline' ? h('span', { class: 'muted', style: 'font-size:11.5px' }, ` · ${t('dt.FYP_outline')}`) : null),
      h('td', null, h('span', { class: 'chip' }, h('span', { class: 'g g-' + STC[e.stance] }, GLY[e.stance]), t('st.' + e.stance))),
      h('td', null, t('ch.' + (e.change || 'na'))),
      h('td', { class: 'mono' }, '●'.repeat(e.intensity || 1) + '○'.repeat(3 - (e.intensity || 1))),
      h('td', null, e.excl ? h('span', { class: 'muted' }, t('ev.na')) : `${(e.series || '').split(';').map(idxName).join('+')}`),
      h('td', { class: 'r mono ' + sgn(e.b12) }, pct(e.b12)), h('td', { class: 'r mono ' + sgn(e.b36) }, pct(e.b36)), h('td', { class: 'r mono ' + sgn(toEnd) }, pct(toEnd)),
      h('td', null, w == null ? '' : h('span', { class: 'mark ' + (w ? 'w' : 'l'), style: 'margin:0' }, w ? '✓ ' + t('ev.win') : '✗ ' + t('ev.loss')))));
  }
  tbl.append(tb);
  const note = clear($('#scoreNote'));
  note.append(t('sc.note'), ' ');
  if (scList.length < sorted.length) note.append(h('button', { type: 'button', class: 'btn sm', onclick: () => { S.scMore = S.plan; renderPlan(); } }, t('evf.more', sorted.length - scList.length)), ' ');
  note.append(h('button', { type: 'button', class: 'btn sm', onclick: () => { S.scAll = scAll ? null : S.plan; S.scMore = null; renderPlan(); } }, scAll ? t('sc.lessRows') : t('sc.allRows', evs.length)));
}

/* ---------------- backtest */
let winChart = null, carChart = null, portChart = null;
function renderPipe() {
  const box = clear($('#pipe')); const P = pal(); const Z = S.lang === 'zh';
  const hm = D.meta && D.meta.hashes ? D.meta.hashes : {};
  const short = s => s ? s.slice(0, 10) + '…' : '';
  const boxes = [
    { id: 'a', x: 16, y: 26, w: 168, lines: Z ? ['政策原文', '六期规划建议与纲要', '另加专项文件'] : ['Policy texts', 'Six plan proposals', 'and outlines, plus', 'other documents'] },
    { id: 'b', x: 212, y: 26, w: 176, lines: Z ? ['编码 agent', '只读原文，按规则编码', '看不到任何行情'] : ['Coding agent', 'Reads the texts only', 'Codes by fixed rules', 'Sees no market data'], strong: true },
    { id: 'c', x: 416, y: 26, w: 168, lines: Z ? ['冻结事件表', `${EV.length} 条 · SHA-256`, short(hm.events)] : ['Frozen event table', `${EV.length} rows · SHA-256`, short(hm.events)] },
    { id: 'd', x: 612, y: 26, w: 172, lines: Z ? ['回测 agent', '只读事件表、行情、计划', '不能改动任何事件'] : ['Backtest agent', 'Reads table, prices', 'and plan only', 'Cannot edit events'], strong: true },
    { id: 'e', x: 212, y: 150, w: 176, lines: Z ? ['预登记分析计划', '胜负标准、持有期、安慰剂', `写定 ${hm.prereg_time || '2026-10-26'}`] : ['Pre-registered plan', 'Win rules, horizons,', 'placebos fixed', `${hm.prereg_time || '2026-10-26'}`] },
    { id: 'f', x: 416, y: 150, w: 168, lines: Z ? ['申万行业指数', '月线与日线', '2000—2026'] : ['SW industry indices', 'Monthly and daily', '2000–2026'] }
  ];
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg'); svg.setAttribute('viewBox', '0 0 800 250'); svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', Z ? '盲测流程：编码 agent 只读政策原文，冻结事件表后交给只读事件表、行情和计划的回测 agent' : 'Blind pipeline: the coding agent reads only policy texts; the frozen event table goes to a backtest agent that reads only the table, prices and the plan');
  const el = (tag, at, txt) => { const e = document.createElementNS(ns, tag); for (const [k, v] of Object.entries(at)) e.setAttribute(k, v); if (txt != null) e.textContent = txt; svg.append(e); return e; };
  const defs = el('defs', {}); const mk = document.createElementNS(ns, 'marker');
  for (const [k, v] of Object.entries({ id: 'pc-arrow', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: 'auto-start-reverse' })) mk.setAttribute(k, v);
  const mp = document.createElementNS(ns, 'path'); mp.setAttribute('d', 'M0 0L10 5L0 10z'); mp.setAttribute('fill', P.ink2); mk.append(mp); defs.append(mk);
  const BH = b => 34 + b.lines.length * 16;
  for (const b of boxes) {
    el('rect', { x: b.x, y: b.y, width: b.w, height: BH(b), rx: 8, fill: b.strong ? P.sel : 'none', stroke: b.strong ? P.accent : P.rule2, 'stroke-width': b.strong ? 1.5 : 1.2 });
    b.lines.forEach((ln, i) => el('text', { x: b.x + 14, y: b.y + 24 + i * 17, fill: i === 0 ? P.ink : P.ink2, 'font-size': i === 0 ? 14 : 12, 'font-weight': i === 0 ? 600 : 400, 'font-family': i === 2 && b.id === 'c' ? 'IBM Plex Mono, monospace' : 'inherit' }, ln));
  }
  const mid = b => b.y + BH(b) / 2;
  const by = Object.fromEntries(boxes.map(b => [b.id, b]));
  const arrow = d => el('path', { d, fill: 'none', stroke: P.ink2, 'stroke-width': 1.25, 'marker-end': 'url(#pc-arrow)' });
  arrow(`M${by.a.x + by.a.w} ${mid(by.a)}H${by.b.x - 2}`);
  arrow(`M${by.b.x + by.b.w} ${mid(by.b)}H${by.c.x - 2}`);
  arrow(`M${by.c.x + by.c.w} ${mid(by.c)}H${by.d.x - 2}`);
  const dBot = by.d.y + BH(by.d);
  arrow(`M${by.f.x + by.f.w} ${mid(by.f)}H${by.d.x + 50}V${dBot + 2}`);
  arrow(`M${by.e.x + by.e.w / 2} ${by.e.y + BH(by.e)}V${by.e.y + BH(by.e) + 14}H${by.d.x + 120}V${dBot + 2}`);
  el('line', { x1: by.b.x + by.b.w / 2, x2: by.b.x + by.b.w / 2, y1: by.b.y + BH(by.b) + 6, y2: by.e.y - 6, stroke: P.seal, 'stroke-width': 1.5, 'stroke-dasharray': '4 4' });
  el('text', { x: by.b.x + by.b.w / 2 + 8, y: (by.b.y + BH(by.b) + by.e.y) / 2 + 4, fill: P.seal, 'font-size': 11.5 }, Z ? '互不相见' : 'no contact');
  box.append(svg);
}
function renderBacktest() {
  renderPipe();
  const sel = $('#winSel'); const cur = S.winRule;
  clear(sel);
  for (const k of ['S+|FYP_proposal', 'S+|FYP', 'S+|all', 'R-demand|all', 'R-supply H-a|all', 'R-supply H-b|all']) sel.append(h('option', { value: k, selected: k === cur }, t('bt.rule.' + k)));
  drawWin();
  const P = pal();
  if (carChart) {
    const cp = RES && RES.car_paths ? RES.car_paths : null;
    if (cp) {
      const mk = (g, label, color, band) => { const c = cp[g]; if (!c) return null; return { key: g, label: `${label} (n=${d3.max(c.n) || 0})`, color, values: c.k.map((k, i) => [k, c.mean[i]]).filter(v => v[1] != null), band: band ? c.k.map((k, i) => [k, c.lo[i], c.hi[i]]).filter(v => v[1] != null) : null }; };
      carChart.setData({ title: t('bt.car'), xDomain: [-12, 36], refY: 0, endLabels: false, legend: true, vlines: [{ x: 0, label: S.lang === 'zh' ? '入场' : 'Entry' }],
        series: [mk('S+ FYP_proposal', S.lang === 'zh' ? '扶持·规划建议' : 'Support·FYP', P.sp, true), mk('R-demand all', t('st.R-demand'), P.rd), mk('R-supply all', t('st.R-supply'), P.rs)].filter(Boolean) });
    } else carChart.setData({ series: [], xDomain: [-12, 36] });
  }
  /* portfolio */
  if (portChart && D.portfolio) {
    const pm = D.portfolio; const series = [];
    const cols = { P1: P.sp, P2: P.muted, P3: P.rs };
    for (const k of ['P1', 'P2', 'P3']) if (pm[k]) series.push({ key: k, label: t('pt.' + k).split(' ')[0], color: cols[k], values: pm[k] });
    portChart.setData({ title: t('bt.port'), xDomain: d3.extent(series.flatMap(s => s.values.map(v => v[0]))), refY: 100, endLabels: true, series });
  }
  const pt = clear($('#portTbl'));
  if (RES && RES.portfolios) {
    pt.append(h('thead', null, h('tr', null, ['pt.h', 'pt.per', 'pt.ret', 'pt.b', 'pt.ex', 'pt.vol', 'pt.ir', 'pt.dd', 'pt.hit', 'pt.hold'].map((k, i) => h('th', { class: i > 1 ? 'r' : '' }, t(k))))));
    const tb = h('tbody');
    for (const k of ['P1', 'P2', 'P3']) {
      const r = RES.portfolios[k]; if (!r) continue;
      tb.append(h('tr', null, h('td', null, t('pt.' + k)), h('td', { class: 'mono' }, `${r.start}—${r.end}`),
        h('td', { class: 'r mono ' + sgn(r.ann_return) }, pct(r.ann_return)), h('td', { class: 'r mono' }, k === 'P3' ? '—' : pct(r.ann_bench)), h('td', { class: 'r mono ' + sgn(r.ann_excess) }, pct(r.ann_excess)),
        h('td', { class: 'r mono' }, pct0(r.vol_excess, 1)), h('td', { class: 'r mono' }, r.info_ratio != null ? r.info_ratio.toFixed(2) : '—'), h('td', { class: 'r mono neg' }, pct(r.max_drawdown_excess)),
        h('td', { class: 'r mono' }, pct0(r.hit_rate)), h('td', { class: 'r mono' }, r.avg_holdings != null ? r.avg_holdings.toFixed(1) : '—')));
    }
    pt.append(tb);
  }
  /* subgroup table */
  const st = clear($('#subTbl'));
  st.append(h('caption', null, t('sub.cap')));
  st.append(h('thead', null, h('tr', null, [t('sub.dim'), t('sub.val'), t('sub.rule'), 'n', t('bt.wr'), t('sub.mean')].map((s, i) => h('th', { class: i >= 3 ? 'r' : '' }, s)))));
  const tb2 = h('tbody');
  if (RES && RES.subgroups) {
    const valLabel = (dim, v) => v === 'other' ? t('dt.other') : v === 'na' ? t('sub.na') : dim === 'plan' ? (PLANBY.get(v) ? planName(PLANBY.get(v)) : v) : dim === 'doc_type' ? t('dt.' + v) : dim === 'stance' ? t('st.' + v) : dim === 'change_vs_prev' ? (t('ch.' + v) || v) : dim === 'intensity' ? t('int.' + v) : dim === 'pivot' ? (v === '1' || v === 1 ? (S.lang === 'zh' ? '是' : 'yes') : (S.lang === 'zh' ? '否' : 'no')) : v;
    const ruleLabel = r => r === 'S+' ? t('st.S+') : r === 'R-demand' ? t('st.R-demand') : r === 'R-supply H-a' ? t('st.R-supply') : r;
    const allRules = !!S.subAll;
    for (const r of RES.subgroups.filter(r => r.h === 36 && r.n >= 5 && r.dim !== 'stance' && (r.rule === 'S+' || (allRules && (r.rule === 'R-demand' || r.rule === 'R-supply H-a'))))) {
      tb2.append(h('tr', null, h('td', null, t('dim.' + r.dim)), h('td', null, valLabel(r.dim, String(r.value))), h('td', null, ruleLabel(r.rule)), h('td', { class: 'r mono' }, r.n),
        h('td', { class: 'r mono' }, pct0(r.win_rate), h('span', { class: 'wbar', 'aria-hidden': 'true' }, h('i', { style: `width:${Math.round((r.win_rate || 0) * 100)}%` }), h('b'))),
        h('td', { class: 'r mono ' + sgn(r.mean_bhar) }, pct(r.mean_bhar))));
    }
  }
  st.append(tb2);
  const stc = st.querySelector('caption');
  if (stc) stc.append(' ', h('button', { type: 'button', class: 'btn sm', onclick: () => { S.subAll = !S.subAll; renderBacktest(); } }, S.subAll ? t('sub.less') : t('sub.more')));
  /* main tests */
  const mt = clear($('#mainTbl'));
  mt.append(h('caption', null, t('main.cap')));
  mt.append(h('thead', null, h('tr', null, [t('main.test'), 'n', t('bt.wr'), t('main.perm'), t('main.p'), t('main.shift'), t('main.p')].map((s, i) => h('th', { class: i ? 'r' : '' }, s)))));
  const tb3 = h('tbody');
  for (const k of ['S+|FYP_proposal', 'S+|FYP', 'S+|other', 'S+|GWR_first', 'S+|all', 'R-demand|all', 'R-supply H-a|all', 'R-supply H-b|all']) {
    const [rule, subset] = k.split('|'); const r = wr(subset, rule, 36); if (!r || !r.n) continue;
    const lab = t('bt.rule.' + k) !== 'bt.rule.' + k ? t('bt.rule.' + k) : `${rule} · ${t('dt.' + subset) !== 'dt.' + subset ? t('dt.' + subset) : subset}`;
    tb3.append(h('tr', null, h('td', null, lab), h('td', { class: 'r mono' }, r.n), h('td', { class: 'r mono' }, pct0(r.win_rate)), h('td', { class: 'r mono' }, pct0(r.perm_win_median)), h('td', { class: 'r mono' }, pFmt(r.p_perm_win)),
      h('td', { class: 'r mono' }, pct0(r.shift_win_median)), h('td', { class: 'r mono' }, pFmt(r.p_shift_win))));
  }
  mt.append(tb3);
  /* short-window + turnover */
  const rt = clear($('#reactTbl'));
  rt.append(h('caption', null, t('react.cap')));
  rt.append(h('thead', null, h('tr', null, [t('react.g'), t('react.pre12'), t('react.pre3'), t('react.d1'), t('react.d5'), t('react.d20'), t('react.ts')].map((s, i) => h('th', { class: i ? 'r' : '' }, s)))));
  const tb4 = h('tbody');
  if (RES && RES.short_window) {
    const groups = Array.from(new Set(RES.short_window.map(r => r.group)));
    for (const g of groups) {
      const cell = k => { const r = RES.short_window.find(x => x.group === g && x.k === k); return r ? h('td', { class: 'r mono ' + sgn(r.mean_car) }, pct(r.mean_car, 2)) : h('td', { class: 'r' }, '—'); };
      const tv = (RES.turnover || []).find(x => x.group === g);
      const pd = w => { const r = (RES.pre_drift || []).find(x => x.group === g && x.window === w); return r ? h('td', { class: 'r mono ' + sgn(r.mean_pre) }, pct(r.mean_pre, 1)) : h('td', { class: 'r' }, '—'); };
      tb4.append(h('tr', null, h('td', null, groupLabel(g)), pd(12), pd(3), cell(1), cell(5), cell(20), h('td', { class: 'r mono ' + (tv ? sgn(tv.change_pp_1_12) : '') }, tv ? `${tv.change_pp_1_12 > 0 ? '+' : ''}${(tv.change_pp_1_12 * 100).toFixed(2)}pp` : '—')));
    }
  }
  rt.append(tb4);
}
function groupLabel(g) {
  const [rule, subset] = g.split(' ');
  const r = rule === 'S+' ? t('st.S+') : rule === 'R-demand' ? t('st.R-demand') : rule === 'R-supply' ? t('st.R-supply') : rule === 'S0' ? t('st.S0') : rule === 'pivot' ? (S.lang === 'zh' ? '方向反转' : 'Reversals') : rule;
  const s = subset === 'all' ? (S.lang === 'zh' ? '全部' : 'all') : (t('dt.' + subset) !== 'dt.' + subset ? t('dt.' + subset) : subset || '');
  return `${r} · ${s}`;
}
function drawWin() {
  if (!winChart) return;
  const [rule, subset] = S.winRule.split('|');
  const rows = [1, 3, 6, 12, 24, 36].map(hz => { const r = wr(subset, rule, hz); return r ? { h: hz, n: r.n, win: r.win_rate, lo: r.ci_lo, hi: r.ci_hi, pmed: r.perm_win_median, p05: r.perm_win_p05, p95: r.perm_win_p95, p: r.p_perm_win } : null; }).filter(Boolean);
  winChart.setData(rows);
}

/* ---------------- data & limits */
function renderData() {
  const lim = clear($('#limits')); for (const s of t('lim')) lim.append(h('li', null, s));
  const cov = clear($('#covTbl')); cov.append(h('caption', null, t('cov.cap')));
  cov.append(h('thead', null, h('tr', null, h('th', null, t('cov.start')), h('th', null, t('cov.list')))));
  const groups = new Map();
  for (const c of L1) { const s = M[firstIdx(IDX[c], 0)]; const k = s.slice(0, 4) <= '2000' ? '2000-01' : s; if (!groups.has(k)) groups.set(k, []); groups.get(k).push(c); }
  const tb = h('tbody'); for (const [k, list] of Array.from(groups.entries()).sort()) tb.append(h('tr', null, h('td', { class: 'mono' }, k), h('td', null, list.map(idxName).join(S.lang === 'zh' ? '、' : ', '))));
  cov.append(tb);
  const hs = clear($('#hashes')); const hm = (D.meta && D.meta.hashes) || {};
  hs.append(h('h3', { style: 'font-size:14px;margin-bottom:8px' }, h('span', { class: 'stamp' }, S.lang === 'zh' ? '冻结' : 'FROZEN'), t('hash.h')));
  for (const [k, v] of Object.entries(hm.files || {})) hs.append(h('div', { style: 'margin-bottom:6px' }, h('div', { style: 'font-size:12.5px' }, k), h('div', { class: 'hash' }, v)));
  if (hm.prereg_time) hs.append(h('div', { class: 'note' }, (S.lang === 'zh' ? '预登记时间（UTC）：' : 'Pre-registered at (UTC): ') + hm.prereg_time));
  const ex = clear($('#exclTbl')); ex.append(h('caption', null, t('excl.cap')));
  ex.append(h('thead', null, h('tr', null, h('th', null, t('excl.reason')), h('th', { class: 'r' }, t('excl.n')))));
  const tb2 = h('tbody'); const exm = (RES && RES.meta && RES.meta.excluded) || {};
  for (const [k, v] of Object.entries(exm)) tb2.append(h('tr', null, h('td', null, t('excl.' + k) !== 'excl.' + k ? t('excl.' + k) : k), h('td', { class: 'r mono' }, v)));
  ex.append(tb2);
  const sr = clear($('#srcs'));
  for (const s of (D.sources || [])) sr.append(h('li', null, s.url ? h('a', { href: s.url, target: '_blank', rel: 'noopener' }, S.lang === 'zh' ? s.zh : (s.en || s.zh)) : (S.lang === 'zh' ? s.zh : (s.en || s.zh)), s.date ? h('span', { class: 'muted' }, ` · ${s.date}`) : null));
  $('#foot').textContent = t('foot');
}

/* ================================================================ init */
function renderAll() {
  applyStatic(); renderOverview(); renderIndustry(); renderPlan(); renderBacktest(); renderData();
}
function rerenderCharts() { applyStatic(); if (kchart) kchart.draw(); if (plines) plines.render(); if (race) race.render(); if (winChart) winChart.render(); if (carChart) carChart.render(); if (portChart) portChart.render(); renderRail(); renderPipe(); }

function init() {
  if (d3) {
    kchart = KChart($('#kwrap'), {
      onSelect: id => selectEvent(id),
      onState: s => setPlayLabel(s)
    });
    plines = LineChart($('#plines'), { height: W => W < 600 ? 300 : 360, yFmt: v => pct(v, 0), vFmt: v => pct(v, 0), xFmt: v => v === 0 ? '0' : (v > 0 ? '+' : '') + v, tipX: k => S.lang === 'zh' ? `入场后第 ${k} 个月` : `Month ${k} after entry`, signed: true, xTicks: (dom) => d3.range(Math.ceil(dom[0] / 12) * 12, dom[1] + 1, 12) });
    race = RaceChart($('#race'), { onFrame: (k, m) => { $('#raceLabel').textContent = t('pl.raceLab', k, m || ''); }, onState: s => { $('#racePlay').textContent = s === 'playing' ? '❚❚' : '▶'; }, label: k => t('pl.race') + ' · ' + k });
    winChart = WinChart($('#winChart'));
    carChart = LineChart($('#carChart'), { height: () => 260, yFmt: v => pct(v, 0), vFmt: v => pct(v, 1), xFmt: v => v === 0 ? '0' : (v > 0 ? '+' : '') + v, tipX: k => S.lang === 'zh' ? `第 ${k} 个月` : `Month ${k}`, signed: true, xTicks: () => [-12, -6, 0, 6, 12, 18, 24, 30, 36] });
    portChart = LineChart($('#portChart'), { height: W => W < 600 ? 280 : 340, yFmt: v => d3.format('.0f')(v), vFmt: v => d3.format('.0f')(v), xFmt: i => M[i] ? M[i].slice(0, 4) : '', tipX: i => M[i] || '', signed: false, xTicks: (dom, w) => { const out = []; const stepY = w < 500 ? 4 : 2; for (let i = Math.ceil(dom[0]); i <= dom[1]; i++) if (M[i] && M[i].slice(5) === '01' && (+M[i].slice(0, 4)) % stepY === 0) out.push(i); return out; } });
  } else {
    $('#kwrap').append(h('div', { class: 'noscript', style: 'margin:12px' }, t('k.nolib')));
  }
  $('#langZh').onclick = () => { S.lang = 'zh'; store.set('lang', 'zh'); renderAll(); };
  $('#langEn').onclick = () => { S.lang = 'en'; store.set('lang', 'en'); renderAll(); };
  $('#convCn').onclick = () => { S.conv = 'cn'; store.set('conv', 'cn'); rerenderCharts(); renderIndustry(); renderPlan(); renderBacktest(); renderOverview(); };
  $('#convIntl').onclick = () => { S.conv = 'intl'; store.set('conv', 'intl'); rerenderCharts(); renderIndustry(); renderPlan(); renderBacktest(); renderOverview(); };
  $('#scLog').onclick = () => { S.scale = 'log'; store.set('scale', 'log'); applyStatic(); kchart && kchart.draw(); };
  $('#scLin').onclick = () => { S.scale = 'lin'; store.set('scale', 'lin'); applyStatic(); kchart && kchart.draw(); };
  $('#indSearch').addEventListener('input', renderRail);
  $('#indSelect').addEventListener('change', ev => { S.ind = ev.target.value; S.range = 'all'; S.sel = null; store.set('ind', S.ind); renderIndustry(); });
  $('#playBtn').onclick = () => kchart && kchart.play();
  $('#speed').onchange = ev => kchart && kchart.setSpeed(+ev.target.value);
  $('#zIn').onclick = () => kchart && kchart.zoomBy(1.6);
  $('#zOut').onclick = () => kchart && kchart.zoomBy(1 / 1.6);
  $('#zReset').onclick = () => kchart && kchart.reset();
  $('#racePlay').onclick = () => race && race.play();
  $('#winSel').onchange = ev => { S.winRule = ev.target.value; drawWin(); };
  $('#kTableD').addEventListener('toggle', () => { if ($('#kTableD').open) renderKTable(); });
  /* nav highlight */
  const links = Array.from(document.querySelectorAll('#navLinks a'));
  const io = new IntersectionObserver(ents => { for (const en of ents) if (en.isIntersecting) links.forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + en.target.id)); }, { rootMargin: '-45% 0px -50% 0px' });
  document.querySelectorAll('main section').forEach(s => io.observe(s));
  /* theme changes */
  const mq = matchMedia('(prefers-color-scheme: dark)');
  if (mq.addEventListener) mq.addEventListener('change', rerenderCharts);
  new MutationObserver(rerenderCharts).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  /* resize */
  let rt = null; let lastW = 0;
  const ro = new ResizeObserver(() => { const w = document.documentElement.clientWidth; if (w === lastW) return; lastW = w; clearTimeout(rt); rt = setTimeout(() => { kchart && kchart.resize(); plines && plines.render(); race && race.render(); winChart && winChart.render(); carChart && carChart.render(); portChart && portChart.render(); }, 120); });
  ro.observe(document.body);
  renderAll();
  const hash = (location.hash || '').slice(1); if (hash && document.getElementById(hash)) document.getElementById(hash).scrollIntoView();
}
init();
})();
