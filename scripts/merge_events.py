"""Mechanical merge of stage-2 row files into the frozen event table.

Reads coding_work/rows/*.csv (one per document, written by blind coding agents) and coding_work/docs_index.tsv,
validates every field, assigns event_ids, computes the `pivot` flag mechanically, and writes
events/events_v1.csv, events/documents_v1.csv, events/merge_report.md and events/FROZEN.sha256.
Never reads price data.

pivot rule (prereg/extraction_protocol_v1.md): per SW code (union of sw_l1 and sw_l2 codes), in chronological order,
direction = +1 for S+, -1 for R-supply / R-demand, S0 ignored. pivot = 1 when the event's direction is opposite to the
most recent earlier non-S0 event that shares any of its codes; events on the same date do not count as earlier.
"""
import csv, hashlib, re, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/claude/policy_bt')
ROWS = ROOT / 'coding_work' / 'rows'
OUT = ROOT / 'events'
COLS = ['event_id', 'doc_id', 'doc_name', 'doc_type', 'issuer', 'event_date', 'concept_zh', 'concept_en', 'sw_l1', 'sw_l2',
        'stance', 'intensity', 'change_vs_prev', 'pivot', 'quote_zh', 'quote_en', 'prev_quote_zh', 'source_url', 'notes']
STANCES = {'S+', 'S0', 'R-supply', 'R-demand'}
CHANGES = {'new', 'up', 'same', 'down', 'dropped', 'na'}
TYPES = {'FYP_proposal', 'FYP_outline', 'other', 'GWR_first'}


def main(freeze=False):
    tax = {r['code']: r for r in csv.DictReader(open(ROOT / 'prereg' / 'sw_taxonomy.csv', encoding='utf-8'))}
    problems, rows = [], []
    for f in sorted(ROWS.glob('*.csv')):
        with open(f, encoding='utf-8') as fh:
            for i, r in enumerate(csv.DictReader(fh)):
                r = {k: (v or '').strip() for k, v in r.items() if k}
                where = f'{f.name}:{i + 2}'
                if r.get('stance') not in STANCES:
                    problems.append(f'{where} bad stance {r.get("stance")!r}')
                if r.get('intensity') not in {'1', '2', '3'}:
                    problems.append(f'{where} bad intensity {r.get("intensity")!r}')
                if r.get('change_vs_prev') not in CHANGES:
                    problems.append(f'{where} bad change {r.get("change_vs_prev")!r}')
                if r.get('doc_type') not in TYPES:
                    problems.append(f'{where} bad doc_type {r.get("doc_type")!r}')
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', r.get('event_date', '')):
                    problems.append(f'{where} bad date {r.get("event_date")!r}')
                for col, lvl in (('sw_l1', 'L1'), ('sw_l2', 'L2')):
                    for c in [x for x in r.get(col, '').split(';') if x]:
                        if c != 'none' and (c not in tax or tax[c]['level'] != lvl):
                            problems.append(f'{where} {col} code {c} not a valid {lvl} code')
                if len(r.get('quote_zh', '')) > 60:
                    problems.append(f'{where} quote_zh longer than 60 chars ({len(r["quote_zh"])})')
                r['_src'] = where
                rows.append(r)
    rows.sort(key=lambda r: (r['event_date'], r['doc_id'], r.get('concept_zh', '')))
    direction = {'S+': 1, 'R-supply': -1, 'R-demand': -1, 'S0': 0}
    last = {}  # code -> (date, direction)
    pending = []
    for n, r in enumerate(rows, 1):
        r['event_id'] = f'E{n:04d}'
    i = 0
    while i < len(rows):  # process one date at a time so same-date events do not count as earlier
        j = i
        while j < len(rows) and rows[j]['event_date'] == rows[i]['event_date']:
            j += 1
        batch = rows[i:j]
        for r in batch:
            codes = {c for c in (r.get('sw_l1', '') + ';' + r.get('sw_l2', '')).split(';') if c and c != 'none'}
            d = direction.get(r['stance'], 0)
            prev = [last[c] for c in codes if c in last]
            latest = max((p[0] for p in prev), default=None)
            r['pivot'] = '1' if d != 0 and latest and any(p[1] == -d for p in prev if p[0] == latest) else '0'
            r['_codes'] = codes
        for r in batch:
            d = direction.get(r['stance'], 0)
            if d:
                for c in r['_codes']:
                    last[c] = (r['event_date'], d)
        i = j
    docs = list(csv.DictReader(open(ROOT / 'coding_work' / 'docs_index.tsv', encoding='utf-8'), delimiter='\t'))
    used = {r['doc_id'] for r in rows}
    OUT.mkdir(exist_ok=True)
    report = [f'# Merge report ({datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")})', '',
              f'- rows: {len(rows)} from {len(list(ROWS.glob("*.csv")))} files; documents coded: {len(used)}',
              f'- validation problems: {len(problems)}', '']
    report += [f'  - {p}' for p in problems[:200]]
    counts = {}
    for r in rows:
        counts[(r['doc_type'], r['stance'])] = counts.get((r['doc_type'], r['stance']), 0) + 1
    report += ['', '| doc_type | stance | rows |', '|---|---|---|'] + [f'| {k[0]} | {k[1]} | {v} |' for k, v in sorted(counts.items())]
    report += ['', f'- pivot = 1: {sum(r["pivot"] == "1" for r in rows)}']
    (OUT / 'merge_report.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print('\n'.join(report[:12]))
    if problems and freeze:
        print('NOT FROZEN: fix validation problems first')
        return 1
    if not freeze:
        return 0
    with open(OUT / 'events_v1.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in COLS})
    dcols = ['doc_id', 'doc_name', 'doc_type', 'issuer', 'event_date', 'source_url', 'date_source', 'verified']
    with open(OUT / 'documents_v1.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=dcols)
        w.writeheader()
        types = {r['doc_id']: r['doc_type'] for r in rows}
        for d in docs:
            if d['doc_id'] not in used:
                continue
            w.writerow(dict(doc_id=d['doc_id'], doc_name=d['title'], doc_type=types.get(d['doc_id'], ''), issuer=d['issuer'],
                            event_date=d['publication_date'], source_url=d['fulltext_url'], date_source=d['date_source'],
                            verified='yes' if d.get('coverage', '').startswith('complete') else d.get('coverage', '')))
    h = {p: hashlib.sha256((OUT / p).read_bytes()).hexdigest() for p in ['events_v1.csv', 'documents_v1.csv']}
    (OUT / 'FROZEN.sha256').write_text(''.join(f'{v}  {k}\n' for k, v in h.items()) +
                                       f'frozen_at_utc {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}\n', encoding='utf-8')
    print('FROZEN', h)
    return 0


if __name__ == '__main__':
    sys.exit(main('--freeze' in sys.argv))
