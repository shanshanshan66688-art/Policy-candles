"""Assemble the Policy Candles page from SW data, the frozen event table and backtest outputs.

usage: python3 build_page.py [--mock] [--out PATH]
"""
import csv, gzip, hashlib, json, math, random, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from names import EN, PLANS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'page'
RAW = ROOT / 'data' / 'raw' / 'sw_index_data_20261026.json.gz'
BENCH = '801003'
MARKET_KEEP = {'801003', '801001', '801300', '801005'}


def taxonomy():
    rows = list(csv.DictReader(open(ROOT / 'prereg' / 'sw_taxonomy.csv', encoding='utf-8')))
    return {r['code']: r for r in rows}


def clean_zh(name):
    return name.replace('Ⅱ', '').replace('Ａ', 'A').strip()


def build_idx(raw):
    tax = taxonomy()
    names = {}
    for ty, arr in raw['lists'].items():
        for code, name in arr:
            names[code] = (name, ty)
    months = sorted({r[0][:7] for rows in raw['monthly'].values() for r in rows if r[0] >= '2000-01-01'})
    mi = {m: i for i, m in enumerate(months)}
    n = len(months)
    bench_t = [None] * n
    for r in raw['monthly'][BENCH]:
        if r[0] >= '2000-01-01':
            bench_t[mi[r[0][:7]]] = r[5]
    idx = {}
    last_bar = {}
    for code, rows in raw['monthly'].items():
        name, ty = names.get(code, (code, ''))
        if ty == '市场表征' and code not in MARKET_KEEP:
            continue
        lvl = 1 if ty == '一级行业' else 2 if ty == '二级行业' else 0
        o, h, l, c, t = ([None] * n for _ in range(5))
        for r in rows:
            if r[0] < '2000-01-01':
                continue
            i = mi[r[0][:7]]
            o[i], h[i], l[i], c[i] = (round(float(v), 2) for v in r[1:5])
            bt = bench_t[i]
            t[i] = round(100.0 * float(r[5]) / bt, 3) if bt else None
            last_bar[code] = r[0]
        parent = tax.get(code, {}).get('parent_l1') or None
        idx[code] = dict(zh=clean_zh(name), en=EN.get(code, clean_zh(name)), lvl=lvl, p=parent, o=o, h=h, l=l, c=c, t=t)
    return months, idx, last_bar


# ------------------------------------------------------------------ mock inputs (layout testing only)
LATE = {'2014-02': '801710 801720 801730 801740 801750 801760 801770 801780 801790 801880 801890 801950 801053 801054 801055 801076 801203 801204 801711 801712 801713 801721 801722 801723 801724 801731 801733 801741 801742 801743 801744 801881 801951'.split(),
        '2021-12': '801960 801970 801980 801038 801039 801043 801044 801045 801056 801077 801078 801086 801095 801096 801103 801104 801113 801114 801115 801116 801125 801126 801127 801128 801129 801133 801145 801179 801183 801206 801218 801219 801726 801735 801736 801737 801738 801745 801764 801765 801766 801767 801769 801782 801783 801784 801785 801952 801962 801963 801971 801972 801981 801982 801991 801992 801993 801994 801995'.split(),
        '2011-10': '801017 801018 801085 801124'.split()}


def mock_raw():
    rnd = random.Random(7)
    tax = taxonomy()
    start = {}
    for m, codes in LATE.items():
        for c in codes:
            start[c] = m
    lists = {'一级行业': [], '二级行业': [], '市场表征': [[BENCH, '申万Ａ指'], ['801001', '申万50']]}
    for code, r in tax.items():
        lists['一级行业' if r['level'] == 'L1' else '二级行业'].append([code, r['name']])
    months = [f'{y}-{m:02d}' for y in range(2000, 2027) for m in range(1, 13) if f'{y}-{m:02d}' <= '2026-10']
    mkt = []
    lvl = 1000.0
    for m in months:
        r = rnd.gauss(0.008, 0.075)
        mkt.append(r)
    monthly = {}
    for code in [BENCH, '801001'] + list(tax.keys()):
        beta = 1 if code == BENCH else rnd.uniform(0.7, 1.3)
        drift = 0 if code == BENCH else rnd.gauss(0.0, 0.004)
        lvl = 1000.0
        rows = [['1999-12-30', 1000, 1000, 1000, 1000, 1.0]]
        for i, m in enumerate(months):
            r = beta * mkt[i] + drift + (0 if code == BENCH else rnd.gauss(0, 0.045))
            o = lvl
            c = max(50, lvl * (1 + r))
            hi = max(o, c) * (1 + abs(rnd.gauss(0, 0.03)))
            lo = min(o, c) * (1 - abs(rnd.gauss(0, 0.03)))
            lvl = c
            if code in start and m < start[code]:
                continue
            day = '23' if m == '2026-10' else '28'
            rows.append([f'{m}-{day}', o, hi, lo, c, rnd.uniform(50, 900) * (40 if code == BENCH else 1)])
        monthly[code] = rows
    return {'lists': lists, 'monthly': monthly}


def mock_events(months, idx):
    rnd = random.Random(11)
    l1 = [c for c, x in idx.items() if x['lvl'] == 1]
    out = []
    docs = []
    prop_dates = {'P10': '2000-10-19', 'P11': '2005-10-19', 'P12': '2010-10-28', 'P13': '2015-11-03', 'P14': '2020-11-03', 'P15': '2025-10-28'}
    eid = 0
    for p in PLANS:
        for k in range(30):
            c1 = rnd.choice(l1)
            kids = [c for c, x in idx.items() if x['p'] == c1]
            c2 = rnd.choice(kids) if kids and rnd.random() < 0.6 else None
            st = rnd.choices(['S+', 'S0', 'R-supply', 'R-demand'], [0.62, 0.14, 0.12, 0.12])[0]
            eid += 1
            out.append(dict(event_id=f'E{eid:04d}', doc_id=f'{p["id"]}-A1', doc_name=f'{p["zh"]}规划建议（测试）', doc_type='FYP_proposal', issuer='中共中央',
                            event_date=prop_dates[p['id']], concept_zh=f'测试行业{eid}', concept_en=f'Test concept {eid}', sw_l1=c1, sw_l2=c2 or '',
                            stance=st, intensity=str(rnd.choice([1, 2, 2, 3])), change_vs_prev='na' if p['id'] == 'P10' else rnd.choice(['new', 'up', 'same', 'down', 'dropped']),
                            pivot='0', quote_zh='（测试用占位文本，非真实原文）', quote_en='(placeholder text for layout testing)', prev_quote_zh='', source_url='', notes=''))
    for k in range(40):
        y = rnd.randint(2003, 2025)
        d = f'{y}-{rnd.randint(1, 12):02d}-{rnd.randint(1, 27):02d}'
        c1 = rnd.choice(l1)
        eid += 1
        out.append(dict(event_id=f'E{eid:04d}', doc_id=f'B{k:02d}', doc_name=f'专项文件{k}（测试）', doc_type='other', issuer='国务院', event_date=d,
                        concept_zh=f'测试行业{eid}', concept_en=f'Test concept {eid}', sw_l1=c1, sw_l2='', stance=rnd.choice(['S+', 'R-demand', 'R-supply']),
                        intensity=str(rnd.choice([2, 3])), change_vs_prev='na', pivot=str(int(rnd.random() < 0.2)), quote_zh='（测试用占位文本）', quote_en='(placeholder)',
                        prev_quote_zh='', source_url='', notes=''))
    return out


def mock_event_level(events, months, idx):
    mi = {m: i for i, m in enumerate(months)}
    out = []
    for e in events:
        m = e['event_date'][:7]
        i = mi.get(m)
        t0 = i + 1 if i is not None and i + 1 < len(months) else None
        codes = [c for c in [e['sw_l2'], e['sw_l1']] if c]
        use = None
        for c in codes:
            if t0 is not None and idx[c]['c'][t0] is not None:
                use = c
                break
        row = dict(event_id=e['event_id'], entry_month=months[t0] if t0 is not None else '', series_used=use or '', level_used=('L2' if use == e['sw_l2'] else 'L1') if use else '',
                   excluded_reason='' if use else 'no_series_at_entry')
        for h in [1, 3, 6, 12, 24, 36]:
            if use and t0 + h < len(months):
                a = idx[use]['c'][t0 + h] / idx[use]['c'][t0]
                b = idx[BENCH]['c'][t0 + h] / idx[BENCH]['c'][t0]
                row[f'bhar_{h}'] = a - b
            else:
                row[f'bhar_{h}'] = ''
        row['pre_12'] = ''
        if use and t0 - 12 >= 0 and idx[use]['c'][t0 - 12] is not None:
            row['pre_12'] = idx[use]['c'][t0] / idx[use]['c'][t0 - 12] - idx[BENCH]['c'][t0] / idx[BENCH]['c'][t0 - 12]
        out.append(row)
    return out


def mock_results():
    rnd = random.Random(3)
    wr = []
    for subset in ['FYP_proposal', 'FYP', 'other', 'GWR_first', 'all']:
        for rule in ['S+', 'R-demand', 'R-supply H-a', 'R-supply H-b']:
            for h in [1, 3, 6, 12, 24, 36]:
                w = rnd.uniform(0.4, 0.62)
                wr.append(dict(subset=subset, rule=rule, h=h, n=rnd.randint(20, 120), n_docs=6, win_rate=w, ci_lo=w - 0.09, ci_hi=w + 0.09,
                               mean_bhar=rnd.gauss(0.02, 0.05), mean_ci_lo=-0.05, mean_ci_hi=0.08, median_bhar=rnd.gauss(0, 0.03),
                               perm_win_median=0.49, perm_win_p05=0.4, perm_win_p95=0.58, p_perm_win=rnd.uniform(0.02, 0.6),
                               perm_mean_median=0, perm_mean_p05=-0.04, perm_mean_p95=0.04, p_perm_mean=0.3,
                               shift_win_median=0.5, shift_win_p05=0.41, shift_win_p95=0.59, p_shift_win=0.4,
                               shift_mean_median=0, shift_mean_p05=-0.04, shift_mean_p95=0.04, p_shift_mean=0.4))
    k = list(range(-12, 37))
    car = {}
    for g in ['S+ FYP_proposal', 'S+ all', 'R-demand all', 'R-supply all', 'S0 all', 'pivot all']:
        v = 0
        mean = []
        for kk in k:
            v += rnd.gauss(0.001, 0.006)
            mean.append(v if kk != 0 else 0)
        car[g] = dict(k=k, mean=mean, lo=[x - 0.04 for x in mean], hi=[x + 0.04 for x in mean], n=[50] * len(k))
    sub = []
    for dim, vals in {'plan': ['P10', 'P11', 'P12', 'P13', 'P14'], 'intensity': ['1', '2', '3'], 'change_vs_prev': ['new', 'up', 'same', 'down']}.items():
        for v in vals:
            sub.append(dict(dim=dim, value=v, rule='S+', h=36, n=rnd.randint(5, 40), win_rate=rnd.uniform(0.3, 0.7), mean_bhar=rnd.gauss(0, 0.05), median_bhar=0, ci_lo=0.2, ci_hi=0.8))
    sw = [dict(group=g, k=k_, n=40, mean_car=rnd.gauss(0, 0.01), ci_lo=-0.01, ci_hi=0.01, pos_rate=0.5) for g in ['S+ FYP_proposal', 'S+ all', 'R-demand all'] for k_ in [1, 5, 20]]
    to = [dict(group=g, n=40, share_pre=0.03, share_post_1_12=0.032, share_post_25_36=0.031, change_pp_1_12=rnd.gauss(0, 0.003), ci_lo=-0.001, ci_hi=0.001) for g in ['S+ FYP_proposal', 'S+ all', 'R-demand all']]
    port = {k_: dict(start='2001-01', end='2026-10', months=310, ann_return=0.08, ann_bench=0.06, ann_excess=rnd.gauss(0.01, 0.02), vol_excess=0.06, info_ratio=0.2, max_drawdown_excess=-0.25, hit_rate=0.52, avg_holdings=9.5) for k_ in ['P1', 'P2', 'P3']}
    return dict(meta=dict(n_events=220, n_tested=180, excluded={'no_series_at_entry': 40}, first_entry='2000-11', last_bar='2026-10-23', hash_check=dict(events=True, prereg=True)),
                win_rates=wr, subgroups=sub, car_paths=car, short_window=sw, turnover=to, portfolios=port)


def mock_portfolio(months):
    rnd = random.Random(5)
    rows = []
    for i, m in enumerate(months):
        if i == 0:
            continue
        b = rnd.gauss(0.008, 0.07)
        rows.append(dict(month=m, bench_ret=b, P1_ret=b + rnd.gauss(0.001, 0.02), P2_ret=b + rnd.gauss(0.0005, 0.02), P3_ret=rnd.gauss(0.001, 0.03)))
    return rows


# ------------------------------------------------------------------ real inputs
def read_csv(p):
    with open(p, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def fnum(v):
    try:
        x = float(v)
        return None if math.isnan(x) else x
    except (TypeError, ValueError):
        return None


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def assemble(mock=False):
    if mock:
        raw = mock_raw()
    else:
        raw = json.loads(gzip.decompress(RAW.read_bytes()))
    months, idx, last_bar = build_idx(raw)
    if mock:
        events = mock_events(months, idx)
        level = {r['event_id']: r for r in mock_event_level(events, months, idx)}
        results = mock_results()
        pm = mock_portfolio(months)
        docs = []
        doc_en = {}
    else:
        events = read_csv(ROOT / 'events' / 'events_v1.csv')
        level = {r['event_id']: r for r in read_csv(ROOT / 'backtest' / 'event_level.csv')}
        results = json.loads((ROOT / 'backtest' / 'results.json').read_text(encoding='utf-8'))
        zh2id = {p['zh']: p['id'] for p in PLANS}
        for g in results.get('subgroups', []):
            if g.get('dim') == 'plan' and g.get('value') in zh2id:
                g['value'] = zh2id[g['value']]
        for k, v in list(results.get('portfolios', {}).items()):
            results['portfolios'][k] = {kk: vv for kk, vv in v.items() if not isinstance(vv, (dict, list))}
        keep_meta = {k: results['meta'][k] for k in ('n_events', 'n_tested', 'excluded', 'first_entry', 'last_bar', 'hash_check', 'seeds', 'incomplete_by_h') if k in results['meta']}
        results['meta'] = keep_meta
        results['subgroups'] = [g for g in results.get('subgroups', []) if g.get('h') in (12, 36)]
        results['win_rates'] = [{k: (round(v, 5) if isinstance(v, float) else v) for k, v in w.items()} for w in results['win_rates']]
        expl = results.get('exploratory', {})
        results['exploratory'] = {'placebo1_relabel': expl.get('placebo1_relabel', [])}
        pm = read_csv(ROOT / 'backtest' / 'portfolio_monthly.csv')
        docs = read_csv(ROOT / 'events' / 'documents_v1.csv')
        doc_en = json.loads((PAGE / 'doc_en.json').read_text(encoding='utf-8')) if (PAGE / 'doc_en.json').exists() else {}
    mi = {m: i for i, m in enumerate(months)}

    # plan of each FYP document
    plan_of_doc = {}
    for e in events:
        if e['doc_type'] in ('FYP_proposal', 'FYP_outline'):
            pid = e['doc_id'][:3]
            if any(p['id'] == pid for p in PLANS):
                plan_of_doc[e['doc_id']] = pid
            else:
                y = int(e['event_date'][:4])
                for p in PLANS:
                    if (e['doc_type'] == 'FYP_proposal' and p['y0'] - 1 == y) or (e['doc_type'] == 'FYP_outline' and p['y0'] == y):
                        plan_of_doc[e['doc_id']] = p['id']
    out_events = []
    for e in events:
        lv = level.get(e['event_id'], {})
        excl = bool(lv.get('excluded_reason'))
        item = dict(id=e['event_id'], doc=e['doc_id'], doc_zh=e['doc_name'], doc_en=doc_en.get(e['doc_id'], ''), type=e['doc_type'], date=e['event_date'],
                    concept_zh=e['concept_zh'], concept_en=e.get('concept_en', ''),
                    l1=[c for c in (e.get('sw_l1') or '').split(';') if c and c != 'none' and c in idx],
                    l2=[c for c in (e.get('sw_l2') or '').split(';') if c and c != 'none' and c in idx],
                    stance=e['stance'], intensity=int(fnum(e.get('intensity')) or 1), change=e.get('change_vs_prev') or 'na', pivot=int(fnum(e.get('pivot')) or 0),
                    q_zh=e.get('quote_zh', ''), q_en=e.get('quote_en', ''), prev_zh=e.get('prev_quote_zh', ''), url=e.get('source_url', ''),
                    plan=plan_of_doc.get(e['doc_id']), entry=lv.get('entry_month') or None, series=lv.get('series_used') or None,
                    level=lv.get('level_used') or None, excl=excl or not lv.get('series_used'),
                    pre12=fnum(lv.get('pre_12')))
        for h in [1, 3, 6, 12, 24, 36]:
            item[f'b{h}'] = fnum(lv.get(f'bhar_{h}'))
        out_events.append(item)

    # plans with dates
    plans = []
    for p in PLANS:
        q = dict(p)
        props = [e for e in events if e['doc_type'] == 'FYP_proposal' and plan_of_doc.get(e['doc_id']) == p['id']]
        outs = [e for e in events if e['doc_type'] == 'FYP_outline' and plan_of_doc.get(e['doc_id']) == p['id']]
        q['proposal'] = min((e['event_date'] for e in props), default=None)
        q['outline'] = min((e['event_date'] for e in outs), default=None)
        if not q['outline']:
            for d in docs:
                if d.get('doc_type') == 'FYP_outline' and d.get('event_date', '')[:4] == str(p['y0']):
                    q['outline'] = d['event_date']
        plans.append(q)

    # portfolio cumulative relative index
    port = {}
    for k in ['P1', 'P2', 'P3']:
        v = 100.0
        series = []
        started = False
        for r in pm:
            pr = fnum(r.get(f'{k}_ret'))
            br = fnum(r.get('bench_ret'))
            if pr is None or (k != 'P3' and br is None):
                continue
            n_hold = fnum(r.get(f'{k}_n')) if k != 'P3' else fnum(r.get('P3_long_n'))
            if not started and (n_hold == 0 or (n_hold is None and not mock)):
                continue
            if not started:
                started = True
                m0 = mi.get(r['month'])
                if m0 is not None and m0 > 0:
                    series.append([m0 - 1, 100.0])
            v = v * (1 + pr) / (1 if k == 'P3' else (1 + br))
            if r['month'] in mi:
                series.append([mi[r['month']], round(v, 3)])
        if series:
            port[k] = series

    # default industry: L1 with most events and data from 2000
    cnt = {}
    for e in out_events:
        for c in e['l1']:
            cnt[c] = cnt.get(c, 0) + 1
    l1 = [c for c, x in idx.items() if x['lvl'] == 1]
    l1.sort()
    early = [c for c in l1 if idx[c]['c'][0] is not None]
    default_ind = max(early, key=lambda c: cnt.get(c, 0)) if early else l1[0]

    hashes = {'files': {}, 'prereg_time': '2026-10-26 13:23 UTC'}
    if not mock:
        for f in ['prereg/coding_protocol_v1.md', 'prereg/analysis_plan_v1.md', 'prereg/analysis_plan_v1_clarifications.md', 'prereg/analysis_plan_v1_clarifications_2.md', 'prereg/extraction_protocol_v1.md', 'prereg/coding_stage2_v1.md', 'events/events_v1.csv', 'events/documents_v1.csv']:
            hashes['files'][f] = sha(ROOT / f)
        hashes['events'] = hashes['files']['events/events_v1.csv']
        hashes['files']['data/sw_index_data_20261026.json.gz'] = sha(RAW)
    else:
        hashes['events'] = 'mock'

    sources = [dict(zh='申万宏源研究 · 申万指数历史行情', en='SWS Research · SW index history', url='https://www.swsresearch.com/institute_sw/allIndex/releasedIndex', date='2026-10-26'),
               dict(zh='李录 2026 年哥伦比亚商学院格雷厄姆与多德论坛演讲整理（虎嗅转载）', en='Li Lu at Columbia Business School’s Graham & Dodd forum, 2026 (Huxiu reprint, Chinese)', url='https://m.huxiu.com/article/4896732.html', date='2026-10-12')]
    seen = set()
    for d in docs:
        url = d.get('source_url')
        if not url or url in seen:
            continue
        seen.add(url)
        sources.append(dict(zh=d['doc_name'], en=doc_en.get(d['doc_id'], ''), url=url, date=d.get('event_date')))

    data = dict(meta=dict(first=months[0], last=months[-1], last_bar=last_bar.get(BENCH), hashes=hashes, mock=mock),
                months=months, bench=BENCH, idx=idx, l1=sorted(l1), events=out_events, plans=plans, results=results, portfolio=port,
                defaultInd='801180' if '801180' in idx else default_ind, defaultPlan='P12', sources=sources)
    return data


def render(data, out, standalone=False):
    tpl = (PAGE / 'template.html').read_text(encoding='utf-8')
    app = (PAGE / 'app.js').read_text(encoding='utf-8')
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = tpl.replace('__PC_DATA__', js).replace('/*__APP_JS__*/', app)
    if standalone:  # full HTML document for GitHub Pages (the artifact host adds this skeleton itself)
        cut = html.index('</style>') + len('</style>')
        head, body = html[:cut], html[cut:]
        html = ('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
                + head + '\n</head>\n<body>\n' + body + '\n</body>\n</html>\n')
    Path(out).write_text(html, encoding='utf-8')
    return len(html.encode('utf-8'))


if __name__ == '__main__':
    mock = '--mock' in sys.argv
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else str(PAGE / ('page_mock.html' if mock else 'page.html'))
    d = assemble(mock)
    size = render(d, out, standalone='--standalone' in sys.argv)
    print(f'wrote {out} ({size / 1e6:.2f} MB), events={len(d["events"])}, idx={len(d["idx"])}, months={len(d["months"])}, default={d["defaultInd"]}')
