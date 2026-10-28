import csv, gzip, json, sys
from pathlib import Path
ROOT = Path('/home/claude/policy_bt')
raw = json.loads(gzip.decompress((ROOT / 'data/raw/sw_index_data_20261026.json.gz').read_bytes()))
tax = {r['code']: r for r in csv.DictReader(open(ROOT / 'prereg/sw_taxonomy.csv', encoding='utf-8'))}
names = {}
for ty, arr in raw['lists'].items():
    for code, name in arr:
        names[code] = (name, {'一级行业': 'L1', '二级行业': 'L2', '市场表征': 'MKT'}[ty])
issues = []
with open(ROOT / 'data/sw_monthly.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['code', 'name', 'level', 'parent_l1', 'bar_date', 'month', 'open', 'high', 'low', 'close', 'turnover_100m_cny'])
    for code, rows in raw['monthly'].items():
        nm, lv = names[code]
        months = []
        for r in rows:
            if r[0] < '2000-01-01':
                continue  # 1999-12-30 base row (index = 1000)
            months.append(r[0][:7])
            w.writerow([code, nm, lv, tax.get(code, {}).get('parent_l1', ''), r[0][:10], r[0][:7], r[1], r[2], r[3], r[4], r[5]])
        # gaps
        if len(set(months)) != len(months):
            issues.append(f'{code} duplicate months')
        ys = [(int(m[:4]) * 12 + int(m[5:]) - 1) for m in months]
        gaps = [months[i] for i in range(1, len(ys)) if ys[i] - ys[i - 1] != 1]
        if gaps:
            issues.append(f'{code} month gaps before {gaps[:5]}')
n = 0
with open(ROOT / 'data/sw_daily.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['code', 'date', 'close'])
    for code, rows in raw['daily'].items():
        last = None
        for d, c in rows:
            ds = f'{d[:4]}-{d[4:6]}-{d[6:]}'
            if last and ds <= last:
                issues.append(f'{code} daily order {ds}')
            last = ds
            w.writerow([code, ds, c])
            n += 1
with open(ROOT / 'data/sw_lineage.csv', 'w', newline='', encoding='utf-8') as f:
    csv.writer(f).writerow(['old_code', 'new_code', 'from_month', 'to_month', 'note'])
print('daily rows', n, 'codes', len(raw['daily']), 'monthly codes', len(raw['monthly']))
print('issues', len(issues), issues[:20])
