#!/usr/bin/env python3
"""
Independent backtest for the pre-registered study "If you buy what the policy wording favours, how often do you win?"

Executes analysis_plan_v1.md + clarifications C1-C14 mechanically on the frozen event table.
Outputs (to /home/claude/policy_bt/backtest/): event_level.csv, results.json, portfolio_monthly.csv,
placebo_draws.json, report.md.

Interpretive decisions taken before any outcome was computed are listed in DEVIATIONS below and copied to report.md.
"""
import bisect
import csv
import hashlib
import json
import math
import os
import re
import sys
import time

import numpy as np
import pandas as pd

T_START = time.time()
BASE = '/home/claude/policy_bt'
OUT = os.path.join(BASE, 'backtest')
EV_DIR = os.path.join(BASE, 'events')
DATA = os.path.join(BASE, 'data')
PREREG = os.path.join(BASE, 'prereg')

SEEDS = {
    'bootstrap': 20261027,          # doc-clustered bootstrap (C10), all CIs
    'placebo_perm': 11,             # placebo 1, industry permutation (C8)
    'placebo_shift': 22,            # placebo 2, date shift (C9)
    'perm_relabel_exploratory': 33, # exploratory sensitivity for placebo 1 (labelled exploratory)
    'self_check': 44,               # choice of events for the hand recomputation check
}
N_BOOT = 10000
N_PLAC = 2000
HS = [1, 3, 6, 12, 24, 36]
BENCH = '801003'
SUBSETS = ['FYP_proposal', 'FYP', 'other', 'GWR_first', 'all']
RULES = ['S+', 'R-demand', 'R-supply H-a', 'R-supply H-b']
RULE_STANCE = {'S+': 'S+', 'R-demand': 'R-demand', 'R-supply H-a': 'R-supply', 'R-supply H-b': 'R-supply'}
RULE_SIGN = {'S+': 1, 'R-demand': -1, 'R-supply H-a': -1, 'R-supply H-b': 1}  # +1: win if BHAR>0; -1: win if BHAR<0
PLAN_LABEL = {'P10': '十五', 'P11': '十一五', 'P12': '十二五', 'P13': '十三五', 'P14': '十四五', 'P15': '十五五'}
PLAN_LAST_YEAR = {'P10': 2005, 'P11': 2010, 'P12': 2015, 'P13': 2020, 'P14': 2025, 'P15': 2030}
GROUPS = ['S+ FYP_proposal', 'S+ all', 'R-demand all', 'R-supply all', 'S0 all', 'pivot all']

DEVIATIONS = [
    ("Plan dimension for subgroups",
     "The events table has no plan column. Plan is derived mechanically from the doc_id prefix: P10->十五, "
     "P11->十一五, P12->十二五, P13->十三五, P14->十四五, P15->十五五; every other document (B..) gets plan = 'other'. "
     "Applied as instructed by the caller."),
    ("Placebo 1: draw without replacement within a document is infeasible for some document-level groups",
     "C8 asks each document's replacement industries to be drawn without replacement. In {N_OVER} (document, level) "
     "groups ({OVER_LIST}; codes needed / eligible pool) the document needs more replacement codes than the pool "
     "holds. Resolution, applied to every group: "
     "codes are drawn by walking through a random permutation of the pool; when the pool is exhausted a fresh "
     "independent permutation is started (no repeats until every eligible series has been used once). Within one "
     "event, codes are always distinct (a duplicate at a permutation boundary is redrawn from the rest of the pool). "
     "Groups where the pool is large enough are unaffected (pure draw without replacement)."),
    ("Placebo 1: eligibility of replacement series",
     "Replacement series must satisfy the same eligibility as the actual selection: a close at the entry month (C8) "
     "and no missing month between t0 and min(t0+36, last bar) (C14). Only 801193 and 801951 are affected."),
    ("Placebo 2: which series a shifted event uses",
     "'Same industries' is implemented as the event's actual series_used (same codes, same level). At the shifted "
     "entry month the C2/C14 filters are applied within series_used (keep codes with a close at the shifted t0 and no "
     "missing month to min(t0+36, last bar)); if none remain the event has lost data and is dropped from that draw. "
     "No level fallback is done for shifted events. A shifted date whose entry month falls before 2000-01 (no monthly "
     "data) or after the last bar is dropped."),
    ("Month-end calendar",
     "Entry months (C3) use the benchmark 801003's bar dates as the month-end calendar. In 14 months a few series "
     "carry a bar dated a few days earlier (801193, 801951) or one day later (801952 in 2022-03) than 801003; no event "
     "date falls inside such a gap, so no entry month depends on this. Monthly closes are used exactly as they appear "
     "in sw_monthly.csv (a present bar is data; C14 treats only absent months as missing). None of these early-dated "
     "bars lies inside any tested event's [t0, t0+36] window (checked in the run)."),
    ("Daily trading calendar",
     "For C7/C14 the trading-day calendar is the set of dates on which 801003 has a close. The source has 18 dates on "
     "which some series have a close but 801003 does not (2015-11-27 is held by 95 series; the other 17 only by "
     "801950 and/or 801952). On those dates no abnormal return can be formed, so they are not trading days of the "
     "calendar; returns are close-to-close between consecutive calendar days for index and benchmark alike. A code "
     "is used in a CAR only if it has a close on every calendar day from day -1 to day k (day -1 is needed for the "
     "day-0 return). Codes are the event's series_used."),
    ("Multi-code events: pre-event, turnover and path windows",
     "C5/C6/C14 windows for multi-code events are computed only when every code in series_used has data in every "
     "month of the window; otherwise missing. Turnover sums the codes' turnover (C6) and divides by 801003's."),
    ("Event-time paths (section 8)",
     "path(k) = I(t0+k)/I(t0) - B(t0+k)/B(t0), where I is the event's equal-weight monthly-rebalanced industry index "
     "and B is 801003. For k > 0 this is BHAR(k); for k < 0 it is the relative-wealth gap normalised at entry "
     "(a pre-entry outperformance shows as a negative value rising to 0 at k = 0)."),
    ("Exclusion reason names",
     "Both sw_l1 and sw_l2 equal to none (or empty) -> 'no_sw_code' (plan section 2.2). C2 -> 'no_series_at_entry'. "
     "C14 -> 'data_gap' (used when at least one coded series had a close at entry but every candidate was removed by "
     "the gap rule). An empty sw_l2 cell is treated like 'none'."),
    ("Horizons and placebos reported",
     "win_rates rows are produced for h = 1, 3, 6, 12, 24, 36 (all section 3 horizons); placebos are run for all of "
     "them. Primary is h = 36 (C1); h = 12 is secondary; other horizons are descriptive."),
    ("p-values",
     "One-sided share of placebo draws at least as favourable as the actual statistic (spec): win rate - draws with "
     "placebo win rate >= actual; mean BHAR - draws with placebo mean >= actual for S+ and R-supply H-b, <= actual for "
     "R-demand and R-supply H-a. No +1 correction. Date-shift draws in which no event of a row survives are dropped "
     "from that row's distribution (count reported)."),
    ("Portfolio statistics",
     "ann_return/ann_bench are geometric annualised returns over the portfolio's months (start = first month with a "
     "holding, end = last bar 2026-10 which is a partial month). ann_excess = 12 x mean monthly excess return, "
     "vol_excess = sqrt(12) x st.dev. of monthly excess return, info_ratio = ann_excess / vol_excess, max drawdown on "
     "the compounded excess-return series, hit_rate = share of months with excess > 0. For P3 the 'excess' series is "
     "the long-short return itself (C12). A month in which a leg holds no series with valid data has P3 return 0 (C12); "
     "for P1/P2 such a month (if any) would be held in cash at 0. The rolling 36-month excess return (section 7) is "
     "compounded portfolio minus compounded benchmark over the trailing 36 months (P3: compounded long-short return), "
     "stored in results.json under portfolios.<P>.rolling36_excess. P1 plan end = December of the plan's last year "
     "(C12), plan from doc_id prefix."),
    ("Bootstrap of medians and subgroup CIs",
     "Section 5 also asks for CIs of the median BHAR; win_rates rows carry extra fields median_ci_lo/median_ci_hi "
     "(doc-clustered, same draws). Subgroup ci_lo/ci_hi are win-rate CIs; subgroup rows also carry mean_ci_lo/hi. "
     "S0 rows are descriptive: win_rate is null, pos_rate (share BHAR > 0) is given."),
]

# ----------------------------------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------------------------------


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def fnum(x):
    """JSON-safe float."""
    if x is None:
        return None
    try:
        xf = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(xf) or math.isinf(xf):
        return None
    return xf


def jclean(o):
    if isinstance(o, dict):
        return {str(k): jclean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jclean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return fnum(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def pct(a, q):
    a = np.asarray(a, float)
    a = a[~np.isnan(a)]
    if a.size == 0:
        return float('nan')
    return float(np.percentile(a, q))


# ----------------------------------------------------------------------------------------------------------------
# 0. hash check
# ----------------------------------------------------------------------------------------------------------------
HEX = re.compile(r'^([0-9a-f]{64})\s+(\S+)\s*$')
hash_details = {'events': {}, 'prereg': {}, 'not_checked': []}
with open(os.path.join(EV_DIR, 'FROZEN.sha256')) as f:
    for line in f:
        mm = HEX.match(line.strip())
        if mm:
            p = os.path.join(EV_DIR, mm.group(2))
            hash_details['events'][mm.group(2)] = (os.path.exists(p) and sha256(p) == mm.group(1))
with open(os.path.join(PREREG, 'PREREG.sha256')) as f:
    for line in f:
        mm = HEX.match(line.strip())
        if not mm:
            continue
        rel = mm.group(2)
        if not (rel.startswith('prereg/') or rel.startswith('data/')):
            # scripts/ is outside the inputs this agent may look at
            hash_details['not_checked'].append(rel)
            continue
        p = os.path.join(BASE, rel)
        hash_details['prereg'][rel] = (os.path.exists(p) and sha256(p) == mm.group(1))
hash_ok_events = len(hash_details['events']) == 2 and all(hash_details['events'].values())
hash_ok_prereg = len(hash_details['prereg']) > 0 and all(hash_details['prereg'].values())
hash_check = {'events': hash_ok_events, 'prereg': hash_ok_prereg, 'details': hash_details}
if not (hash_ok_events and hash_ok_prereg):
    with open(os.path.join(OUT, 'results.json'), 'w') as f:
        json.dump(jclean({'meta': {'hash_check': hash_check, 'runtime_note': 'stopped: hash mismatch'}}), f, indent=1,
                  ensure_ascii=False)
    print('HASH CHECK FAILED', hash_details)
    sys.exit(1)
print('hash check ok', time.time() - T_START)

# ----------------------------------------------------------------------------------------------------------------
# 1. data
# ----------------------------------------------------------------------------------------------------------------
mon = pd.read_csv(os.path.join(DATA, 'sw_monthly.csv'), dtype={'code': str, 'parent_l1': str})
lineage = pd.read_csv(os.path.join(DATA, 'sw_lineage.csv'), dtype=str)
bm = mon[mon.code == BENCH].sort_values('month')
MONTHS = list(bm.month)
BARD = list(bm.bar_date)
T = len(MONTHS)
LAST = T - 1
MI = {m: i for i, m in enumerate(MONTHS)}
CODES = sorted(mon.code.unique())
S = len(CODES)
CI = {c: i for i, c in enumerate(CODES)}
LEVEL = mon.drop_duplicates('code').set_index('code').level.to_dict()
NAME = mon.drop_duplicates('code').set_index('code').name.to_dict()
BI = CI[BENCH]

C = np.full((T, S), np.nan)
TO = np.full((T, S), np.nan)
BAR_CODE = {}
for c, mo, cl, to, bd_ in zip(mon.code, mon.month, mon.close, mon.turnover_100m_cny, mon.bar_date):
    C[MI[mo], CI[c]] = cl
    TO[MI[mo], CI[c]] = to
    BAR_CODE[(c, mo)] = bd_
HAVE = ~np.isnan(C)
R = np.full((T, S), np.nan)
R[1:] = C[1:] / C[:-1] - 1.0          # NaN whenever either close is absent (C14: never a zero return)
RB = R[:, BI]
# stale bars (bar date differs from 801003's bar date that month)
STALE = {(c, mo): bd_ for (c, mo), bd_ in BAR_CODE.items() if bd_ != BARD[MI[mo]]}

day = pd.read_csv(os.path.join(DATA, 'sw_daily.csv'), dtype={'code': str})
DDATES = sorted(day[day.code == BENCH].date.unique())
ND = len(DDATES)
DI = {d: i for i, d in enumerate(DDATES)}
ALL_DAYS = set(day.date.unique())
day = day[day.date.isin(DI)]
DC = np.full((ND, S), np.nan)
DC[day.date.map(DI).values, day.code.map(CI).values] = day.close.values
DR = np.full((ND, S), np.nan)
DR[1:] = DC[1:] / DC[:-1] - 1.0
print('data loaded', time.time() - T_START)

# ----------------------------------------------------------------------------------------------------------------
# 2. events, entry month, series selection (C2, C3, C14)
# ----------------------------------------------------------------------------------------------------------------
ev = pd.read_csv(os.path.join(EV_DIR, 'events_v1.csv'), dtype=str, keep_default_na=False)
docs = pd.read_csv(os.path.join(EV_DIR, 'documents_v1.csv'), dtype=str, keep_default_na=False)
NE = len(ev)


def parse_codes(s):
    return [c for c in str(s).split(';') if c.strip() not in ('', 'none')]


def entry_index(date_str):
    """first month whose (801003) bar date is strictly after date_str; returns T if none."""
    return bisect.bisect_right(BARD, date_str)


def gap_free(j, t):
    """series j has a close at t and no missing month in [t, min(t+36, LAST)] (C2 + C14)."""
    return bool(HAVE[t, j] and HAVE[t:min(t + 36, LAST) + 1, j].all())


def plan_of(doc_id):
    p = doc_id[:3]
    return PLAN_LABEL[p] if p in PLAN_LABEL else 'other'


ev['plan'] = ev.doc_id.map(plan_of)
ev['l1c'] = ev.sw_l1.map(parse_codes)
ev['l2c'] = ev.sw_l2.map(parse_codes)
ev['t0'] = ev.event_date.map(entry_index)
assert (ev.t0 < T).all()
ev['entry_month'] = ev.t0.map(lambda t: MONTHS[t])

sel_used, sel_level, sel_reason = [], [], []
for r in ev.itertuples():
    t = r.t0
    if not r.l1c and not r.l2c:
        sel_used.append([]); sel_level.append(''); sel_reason.append('no_sw_code'); continue
    a2 = [c for c in r.l2c if HAVE[t, CI[c]]]
    b2 = [c for c in a2 if gap_free(CI[c], t)]
    a1 = [c for c in r.l1c if HAVE[t, CI[c]]]
    b1 = [c for c in a1 if gap_free(CI[c], t)]
    if b2:
        sel_used.append(b2); sel_level.append('L2'); sel_reason.append('')
    elif b1:
        sel_used.append(b1); sel_level.append('L1'); sel_reason.append('')
    elif a2 or a1:
        sel_used.append([]); sel_level.append(''); sel_reason.append('data_gap')
    else:
        sel_used.append([]); sel_level.append(''); sel_reason.append('no_series_at_entry')
ev['used'] = sel_used
ev['level_used'] = sel_level
ev['excluded_reason'] = sel_reason
ev['tested'] = ev.excluded_reason == ''
TE = ev[ev.tested].reset_index(drop=True)          # tested events
NT = len(TE)
KMAX = int(TE.used.map(len).max())
T0 = TE.t0.values.astype(int)
CODEMAT = np.full((NT, KMAX), -1, int)
for i, u in enumerate(TE.used):
    CODEMAT[i, :len(u)] = [CI[c] for c in u]
DOCS_T = sorted(TE.doc_id.unique())
DOCIX = {d: i for i, d in enumerate(DOCS_T)}
TE_DOC = TE.doc_id.map(DOCIX).values
print('selection done: tested', NT, ev.excluded_reason.value_counts().to_dict(), time.time() - T_START)

# ----------------------------------------------------------------------------------------------------------------
# 3. return machinery
# ----------------------------------------------------------------------------------------------------------------
TT = np.minimum(T0[:, None] + np.arange(1, 37)[None, :], LAST)     # (NT, 36) forward month indices (clipped)
FWD_VALID = (T0[:, None] + np.arange(1, 37)[None, :]) <= LAST       # horizon month inside data
HIX = np.array(HS) - 1
# benchmark compounded growth per event and horizon
WB_F = np.cumprod(1.0 + RB[TT], axis=1)                              # (NT, 36)


def bhar_from_codes(codemat, t_idx=TT):
    """codemat: (..., NT, KMAX) with -1 padding -> BHAR (..., NT, 6); NaN for incomplete horizons."""
    valid = codemat >= 0
    k = valid.sum(-1, keepdims=True)
    cm = np.where(valid, codemat, 0)
    g = R[t_idx[..., :, None], cm[..., None, :]]                     # (..., NT, 36, KMAX)
    g = np.where(valid[..., None, :], g, 0.0)
    p = g.sum(-1) / k                                                # equal weight, rebalanced monthly (C2)
    wi = np.cumprod(1.0 + p, axis=-1)[..., HIX]
    out = wi - WB_F[:, HIX]
    return np.where(FWD_VALID[:, HIX], out, np.nan)


def growth(codes_idx, a, b):
    """Compounded equal-weight rebalanced growth from close a to close b (a<=b); NaN if any month missing."""
    if a < 0 or b > LAST:
        return float('nan')
    if a == b:
        return 1.0
    blk = HAVE[a:b + 1][:, codes_idx]
    if not blk.all():
        return float('nan')
    p = R[a + 1:b + 1][:, codes_idx].mean(axis=1)
    return float(np.prod(1.0 + p))


def bgrowth(a, b):
    if a < 0 or b > LAST:
        return float('nan')
    return float(C[b, BI] / C[a, BI])


BH = bhar_from_codes(CODEMAT)                                        # (NT, 6) actual BHARs
assert not np.isnan(BH[FWD_VALID[:, HIX]]).any(), 'missing BHAR inside data for a tested event'

# pre-event drift (C5), turnover (C6), daily CAR (C7), paths
pre12 = np.full(NT, np.nan); pre3 = np.full(NT, np.nan)
tsh_pre = np.full(NT, np.nan); tsh_p1 = np.full(NT, np.nan); tsh_p25 = np.full(NT, np.nan)
car = {k: np.full(NT, np.nan) for k in (1, 5, 20)}
KS = list(range(-12, 37))
PATH = np.full((NT, len(KS)), np.nan)
ev_day0 = [None] * NT


def tshare(cix, a, b):
    if a < 0 or b > LAST:
        return float('nan')
    blk = TO[a:b + 1][:, cix]
    if np.isnan(blk).any() or np.isnan(TO[a:b + 1, BI]).any():
        return float('nan')
    return float(np.mean(blk.sum(axis=1) / TO[a:b + 1, BI]))


for i in range(NT):
    cix = [CI[c] for c in TE.used[i]]
    t = T0[i]
    for w, arr in ((12, pre12), (3, pre3)):
        gi = growth(cix, t - w, t)
        arr[i] = gi - bgrowth(t - w, t) if not math.isnan(gi) else np.nan
    tsh_pre[i] = tshare(cix, t - 12, t - 1)
    tsh_p1[i] = tshare(cix, t + 1, t + 12)
    tsh_p25[i] = tshare(cix, t + 25, t + 36)
    # paths
    for kk, k in enumerate(KS):
        if k == 0:
            PATH[i, kk] = 0.0
        elif k < 0:
            gi = growth(cix, t + k, t)
            if not math.isnan(gi) and t + k >= 0:
                PATH[i, kk] = 1.0 / gi - 1.0 / bgrowth(t + k, t)
        else:
            if t + k <= LAST:
                gi = growth(cix, t, t + k)
                PATH[i, kk] = gi - bgrowth(t, t + k)
    # daily
    d0 = bisect.bisect_left(DDATES, TE.event_date[i])
    ev_day0[i] = DDATES[d0] if d0 < ND else None
    for k in (1, 5, 20):
        if d0 - 1 < 0 or d0 + k > ND - 1:
            continue
        ok = [j for j in cix if not np.isnan(DC[d0 - 1:d0 + k + 1, j]).any()]
        if not ok:
            continue
        p = DR[d0:d0 + k + 1][:, ok].mean(axis=1)
        car[k][i] = float(np.sum(p - DR[d0:d0 + k + 1, BI]))
# consistency: path at k>0 equals BHAR
for h in HS:
    a = PATH[:, KS.index(h)]; b = BH[:, HS.index(h)]
    m_ = ~np.isnan(b)
    assert np.allclose(a[m_], b[m_], atol=1e-10), 'path/BHAR mismatch'
print('event measures done', time.time() - T_START)

# win indicators per rule (C11: ties lose)
STANCE = TE.stance.values


def wins_for(rule, bh):
    return (bh > 0) if RULE_SIGN[rule] > 0 else (bh < 0)


# ----------------------------------------------------------------------------------------------------------------
# 4. event_level.csv
# ----------------------------------------------------------------------------------------------------------------
tix = {eid: i for i, eid in enumerate(TE.event_id)}
rows = []
partial_by_h = {h: 0 for h in HS}
for r in ev.itertuples():
    row = {'event_id': r.event_id, 'doc_id': r.doc_id, 'doc_type': r.doc_type, 'stance': r.stance,
           'event_date': r.event_date, 'entry_month': r.entry_month, 'series_used': ';'.join(r.used),
           'level_used': r.level_used, 'excluded_reason': r.excluded_reason}
    i = tix.get(r.event_id)
    for h in HS:
        row[f'bhar_{h}'] = '' if i is None or np.isnan(BH[i, HS.index(h)]) else repr(float(BH[i, HS.index(h)]))
    vals = {'pre_12': pre12, 'pre_3': pre3, 'car_d1': car[1], 'car_d5': car[5], 'car_d20': car[20],
            'tshare_pre': tsh_pre, 'tshare_post_1_12': tsh_p1, 'tshare_post_25_36': tsh_p25}
    for k_, arr in vals.items():
        row[k_] = '' if i is None or np.isnan(arr[i]) else repr(float(arr[i]))
    for h in (12, 36):
        v = '' if i is None else BH[i, HS.index(h)]
        if i is None or np.isnan(v) or r.stance == 'S0':
            row[f'win_{h}'] = ''
        else:
            rule = {'S+': 'S+', 'R-demand': 'R-demand', 'R-supply': 'R-supply H-a'}[r.stance]
            row[f'win_{h}'] = int(wins_for(rule, v))
    flag = 0
    if i is not None:
        for h in HS:
            if T0[i] + h == LAST:
                flag = 1; partial_by_h[h] += 1
    row['ends_on_partial_month'] = flag if i is not None else ''
    rows.append(row)
EL_COLS = ['event_id', 'doc_id', 'doc_type', 'stance', 'event_date', 'entry_month', 'series_used', 'level_used',
           'excluded_reason', 'bhar_1', 'bhar_3', 'bhar_6', 'bhar_12', 'bhar_24', 'bhar_36', 'pre_12', 'pre_3',
           'car_d1', 'car_d5', 'car_d20', 'tshare_pre', 'tshare_post_1_12', 'tshare_post_25_36', 'win_12', 'win_36',
           'ends_on_partial_month']
pd.DataFrame(rows)[EL_COLS].to_csv(os.path.join(OUT, 'event_level.csv'), index=False)
print('event_level written', time.time() - T_START)

# ----------------------------------------------------------------------------------------------------------------
# 5. bootstrap machinery (C10: cluster = doc_id, 10,000 draws, percentile 95%)
# ----------------------------------------------------------------------------------------------------------------
rng_boot = np.random.default_rng(SEEDS['bootstrap'])


def boot_counts(n_groups):
    return rng_boot.multinomial(n_groups, np.full(n_groups, 1.0 / n_groups), size=N_BOOT)


def boot_stats(doc_ids, values, win=None, want_median=False):
    """doc_ids: array of doc labels; values: float array (no NaN); win: optional 0/1 array.
    Returns dict with CIs of mean (and win rate, median)."""
    u, g = np.unique(doc_ids, return_inverse=True)
    G = len(u)
    cnt = boot_counts(G)                                     # (B, G)
    n_g = np.bincount(g, minlength=G).astype(float)
    tot = cnt @ n_g
    out = {}
    s_g = np.bincount(g, weights=values, minlength=G)
    mb = (cnt @ s_g) / tot
    out['mean_ci'] = (pct(mb, 2.5), pct(mb, 97.5))
    if win is not None:
        w_g = np.bincount(g, weights=win.astype(float), minlength=G)
        wb = (cnt @ w_g) / tot
        out['win_ci'] = (pct(wb, 2.5), pct(wb, 97.5))
    if want_median:
        order = np.argsort(values, kind='stable')
        v_sorted = values[order]
        wts = cnt[:, g[order]]                               # (B, n)
        cs = np.cumsum(wts, axis=1)
        totl = cs[:, -1]
        k1 = (totl + 1) // 2
        k2 = totl // 2 + 1
        i1 = (cs >= k1[:, None]).argmax(axis=1)
        i2 = (cs >= k2[:, None]).argmax(axis=1)
        med = 0.5 * (v_sorted[i1] + v_sorted[i2])
        out['median_ci'] = (pct(med, 2.5), pct(med, 97.5))
    return out


def boot_mean_matrix(doc_ids, M):
    """M: (n, K) with NaN allowed -> bootstrap mean per column (B, K)."""
    u, g = np.unique(doc_ids, return_inverse=True)
    G = len(u)
    cnt = boot_counts(G)
    ok = ~np.isnan(M)
    s_g = np.zeros((G, M.shape[1])); n_g = np.zeros((G, M.shape[1]))
    np.add.at(s_g, g, np.where(ok, M, 0.0))
    np.add.at(n_g, g, ok.astype(float))
    with np.errstate(invalid='ignore', divide='ignore'):
        return (cnt @ s_g) / (cnt @ n_g)


# ----------------------------------------------------------------------------------------------------------------
# 6. subsets
# ----------------------------------------------------------------------------------------------------------------
DT = TE.doc_type.values


def subset_mask(name):
    if name == 'FYP_proposal':
        return DT == 'FYP_proposal'
    if name == 'FYP':
        return np.isin(DT, ['FYP_proposal', 'FYP_outline'])
    if name == 'other':
        return DT == 'other'
    if name == 'GWR_first':
        return DT == 'GWR_first'
    if name == 'all':
        return np.ones(NT, bool)
    raise ValueError(name)


def row_mask(subset, rule, h):
    hi = HS.index(h)
    return subset_mask(subset) & (STANCE == RULE_STANCE[rule]) & ~np.isnan(BH[:, hi])


# ----------------------------------------------------------------------------------------------------------------
# 7. placebo 1 (industry permutation, C8)
# ----------------------------------------------------------------------------------------------------------------
def eligible_pool(level, t):
    return np.array([CI[c] for c in CODES if LEVEL[c] == level and gap_free(CI[c], t)], int)


GROUPS_DL = {}
for i in range(NT):
    GROUPS_DL.setdefault((TE.doc_id[i], TE.level_used[i]), []).append(i)
pool_info = []


def fix_within_event_dups(rng, sl, pool):
    """sl: (N, k) codes; redraw duplicates within a row from the rest of the pool."""
    k = sl.shape[1]
    if k < 2:
        return sl
    srt = np.sort(sl, axis=1)
    bad = np.where((srt[:, 1:] == srt[:, :-1]).any(axis=1))[0]
    for rI in bad:
        seen = []
        for j in range(k):
            if sl[rI, j] in seen:
                rest = np.setdiff1d(pool, seen + list(sl[rI, j + 1:]))
                sl[rI, j] = rng.choice(rest)
            seen.append(sl[rI, j])
    return sl


def draw_perm_codes(rng, n_draws, relabel=False):
    """Returns (n_draws, NT, KMAX) replacement code matrix."""
    out = np.full((n_draws, NT, KMAX), -1, int)
    for (doc, lev), idxs in GROUPS_DL.items():
        t = T0[idxs[0]]
        pool = eligible_pool(lev, t)
        P = len(pool)
        ks = [int((CODEMAT[i] >= 0).sum()) for i in idxs]
        if not relabel:
            L = sum(ks)
            nperm = -(-L // P)
            seq = np.concatenate([rng.permuted(np.tile(pool, (n_draws, 1)), axis=1) for _ in range(nperm)], axis=1)
            pos = 0
            for i, k in zip(idxs, ks):
                sl = seq[:, pos:pos + k].copy(); pos += k
                if pos > P and k > 1:          # only possible across a permutation boundary
                    sl = fix_within_event_dups(rng, sl, pool)
                out[:, i, :k] = sl
        else:
            distinct = sorted(set(int(c) for i in idxs for c in CODEMAT[i] if c >= 0))
            u = len(distinct)
            perm = rng.permuted(np.tile(pool, (n_draws, 1)), axis=1)[:, :u]
            pos_of = {c: j for j, c in enumerate(distinct)}
            for i, k in zip(idxs, ks):
                cols = [pos_of[int(c)] for c in CODEMAT[i, :k]]
                out[:, i, :k] = perm[:, cols]
    return out


for (doc, lev), idxs in GROUPS_DL.items():
    t = T0[idxs[0]]
    P = len(eligible_pool(lev, t))
    need = int(sum((CODEMAT[i] >= 0).sum() for i in idxs))
    distinct = len(set(int(c) for i in idxs for c in CODEMAT[i] if c >= 0))
    pool_info.append({'doc_id': doc, 'level': lev, 'entry_month': MONTHS[t], 'n_events': len(idxs),
                      'codes_needed': need, 'distinct_actual': distinct, 'pool': P, 'over_capacity': need > P})


def placebo_bhars(codes_all, chunk=40):
    n = codes_all.shape[0]
    res = np.empty((n, NT, len(HS)), np.float32)
    for s in range(0, n, chunk):
        res[s:s + chunk] = bhar_from_codes(codes_all[s:s + chunk], TT[None, :, :])
    return res


rng_perm = np.random.default_rng(SEEDS['placebo_perm'])
PERM_CODES = draw_perm_codes(rng_perm, N_PLAC)
# sanity: distinctness within event; same level; eligible
for i in range(NT):
    k = int((CODEMAT[i] >= 0).sum())
    blk = PERM_CODES[:, i, :k]
    if k > 1:
        srt = np.sort(blk, axis=1)
        assert not (srt[:, 1:] == srt[:, :-1]).any(), 'duplicate code within event in placebo 1'
    assert set(np.unique(blk)) <= set(eligible_pool(TE.level_used[i], T0[i]))
BH_PERM = placebo_bhars(PERM_CODES)
# machinery check: recompute 200 random (draw, event) placebo-1 BHARs with the slow growth() path
_rng_c = np.random.default_rng(SEEDS['self_check'] + 1)
_pd, _pe = _rng_c.integers(0, N_PLAC, 200), _rng_c.integers(0, NT, 200)
_mx = 0.0
for _d, _e in zip(_pd, _pe):
    _codes = [int(c) for c in PERM_CODES[_d, _e] if c >= 0]
    for _hj, _h in enumerate(HS):
        if T0[_e] + _h <= LAST:
            _v = growth(_codes, T0[_e], T0[_e] + _h) - bgrowth(T0[_e], T0[_e] + _h)
            _mx = max(_mx, abs(_v - float(BH_PERM[_d, _e, _hj])) / max(1.0, abs(_v)))
PLACEBO1_CHECK_MAXRELDIFF = _mx
assert _mx < 1e-5, f'placebo 1 machinery mismatch {_mx}'
del PERM_CODES
print('placebo 1 done', time.time() - T_START)

rng_rel = np.random.default_rng(SEEDS['perm_relabel_exploratory'])
REL_CODES = draw_perm_codes(rng_rel, N_PLAC, relabel=True)
BH_REL = placebo_bhars(REL_CODES)
del REL_CODES
print('exploratory relabel placebo done', time.time() - T_START)

# ----------------------------------------------------------------------------------------------------------------
# 8. placebo 2 (date shift, C9)
# ----------------------------------------------------------------------------------------------------------------
SHIFTS = [s for s in range(-24, 25) if 6 <= abs(s) <= 24]           # 38 values
SHI = {s: j for j, s in enumerate(SHIFTS)}
SH_TABLE = np.full((NT, len(SHIFTS), len(HS)), np.nan)
doc_date = TE.groupby('doc_id').event_date.first().to_dict()
shift_entry = {}
for d in DOCS_T:
    for s in SHIFTS:
        nd = (pd.Timestamp(doc_date[d]) + pd.DateOffset(months=s)).strftime('%Y-%m-%d')
        if nd < '1999-12-30':
            t = None                     # entry month would precede the first monthly bar
        else:
            t = entry_index(nd)
            if t >= T:
                t = None
        shift_entry[(d, s)] = t
for i in range(NT):
    d = TE.doc_id[i]
    cix_all = [CI[c] for c in TE.used[i]]
    for s in SHIFTS:
        t = shift_entry[(d, s)]
        if t is None:
            continue
        cix = [j for j in cix_all if gap_free(j, t)]
        if not cix:
            continue
        for hj, h in enumerate(HS):
            if t + h > LAST:
                continue
            gi = growth(cix, t, t + h)
            SH_TABLE[i, SHI[s], hj] = gi - bgrowth(t, t + h)
# machinery check: the shift code path with a zero shift must reproduce the actual BHARs exactly
_sh0 = np.full((NT, len(HS)), np.nan)
for i in range(NT):
    _t = entry_index((pd.Timestamp(doc_date[TE.doc_id[i]]) + pd.DateOffset(months=0)).strftime('%Y-%m-%d'))
    _cix = [j for j in (CI[c] for c in TE.used[i]) if gap_free(j, _t)]
    for hj, h in enumerate(HS):
        if _t + h <= LAST:
            _sh0[i, hj] = growth(_cix, _t, _t + h) - bgrowth(_t, _t + h)
SHIFT0_SAME_NAN = bool((np.isnan(_sh0) == np.isnan(BH)).all())
SHIFT0_MAXDIFF = float(np.nanmax(np.abs(_sh0 - BH)))
assert SHIFT0_SAME_NAN and SHIFT0_MAXDIFF < 1e-10, 'shift machinery does not reproduce actual BHARs at shift 0'
_ok = [(TE.doc_id[i], s_) for i in range(NT) for s_ in SHIFTS if shift_entry[(TE.doc_id[i], s_)] is not None]
SHIFT_ENTRY_EQ_T0_PLUS_S = float(np.mean([shift_entry[(d_, s_)] == T0[TE.doc_id.values.tolist().index(d_)] + s_
                                          for d_, s_ in set(_ok)]))
rng_shift = np.random.default_rng(SEEDS['placebo_shift'])
G_ALL = len(DOCS_T)
mag = rng_shift.integers(6, 25, size=(N_PLAC, G_ALL))
sgn = rng_shift.choice(np.array([-1, 1]), size=(N_PLAC, G_ALL))
shift_draw = mag * sgn                                                 # (N, G)
shift_idx = np.vectorize(SHI.get)(shift_draw)
BH_SHIFT = SH_TABLE[np.arange(NT)[None, :], shift_idx[:, TE_DOC], :].astype(np.float32)  # (N, NT, 6)
print('placebo 2 done', time.time() - T_START)


def placebo_row_stats(BHP, mask, h, rule):
    hi = HS.index(h)
    x = BHP[:, mask, hi].astype(float)                      # (N, n)
    ok = ~np.isnan(x)
    nok = ok.sum(1)
    w = wins_for(rule, x) & ok
    with np.errstate(invalid='ignore', divide='ignore'):
        wr = w.sum(1) / nok
        mn = np.where(ok, x, 0).sum(1) / nok
    wr[nok == 0] = np.nan; mn[nok == 0] = np.nan
    return wr, mn, nok


def pval(dist, actual, sign):
    d = dist[~np.isnan(dist)]
    if d.size == 0 or actual is None or (isinstance(actual, float) and math.isnan(actual)):
        return float('nan')
    return float(np.mean(d >= actual)) if sign > 0 else float(np.mean(d <= actual))


# ----------------------------------------------------------------------------------------------------------------
# 9. win_rates
# ----------------------------------------------------------------------------------------------------------------
win_rows = []
placebo_dump = {}
exploratory_relabel = []
n_used = {}
for subset in SUBSETS:
    for rule in RULES:
        for h in HS:
            mask = row_mask(subset, rule, h)
            n = int(mask.sum())
            row = {'subset': subset, 'rule': rule, 'h': h, 'n': n, 'n_docs': int(len(set(TE.doc_id[mask])))}
            keys = ['win_rate', 'ci_lo', 'ci_hi', 'mean_bhar', 'mean_ci_lo', 'mean_ci_hi', 'median_bhar',
                    'perm_win_median', 'perm_win_p05', 'perm_win_p95', 'p_perm_win', 'perm_mean_median',
                    'perm_mean_p05', 'perm_mean_p95', 'p_perm_mean', 'shift_win_median', 'shift_win_p05',
                    'shift_win_p95', 'p_shift_win', 'shift_mean_median', 'shift_mean_p05', 'shift_mean_p95',
                    'p_shift_mean', 'median_ci_lo', 'median_ci_hi', 'shift_n_median', 'shift_draws_empty']
            if n == 0:
                row.update({k: None for k in keys})
                win_rows.append(row)
                continue
            hi = HS.index(h)
            x = BH[mask, hi]
            w = wins_for(rule, x)
            bs = boot_stats(TE.doc_id.values[mask], x, w, want_median=True)
            row.update({'win_rate': float(w.mean()), 'ci_lo': bs['win_ci'][0], 'ci_hi': bs['win_ci'][1],
                        'mean_bhar': float(x.mean()), 'mean_ci_lo': bs['mean_ci'][0], 'mean_ci_hi': bs['mean_ci'][1],
                        'median_bhar': float(np.median(x)),
                        'median_ci_lo': bs['median_ci'][0], 'median_ci_hi': bs['median_ci'][1]})
            sg = RULE_SIGN[rule]
            pw, pm, _ = placebo_row_stats(BH_PERM, mask, h, rule)
            sw, sm, snok = placebo_row_stats(BH_SHIFT, mask, h, rule)
            row.update({'perm_win_median': pct(pw, 50), 'perm_win_p05': pct(pw, 5), 'perm_win_p95': pct(pw, 95),
                        'p_perm_win': pval(pw, row['win_rate'], 1),
                        'perm_mean_median': pct(pm, 50), 'perm_mean_p05': pct(pm, 5), 'perm_mean_p95': pct(pm, 95),
                        'p_perm_mean': pval(pm, row['mean_bhar'], sg),
                        'shift_win_median': pct(sw, 50), 'shift_win_p05': pct(sw, 5), 'shift_win_p95': pct(sw, 95),
                        'p_shift_win': pval(sw, row['win_rate'], 1),
                        'shift_mean_median': pct(sm, 50), 'shift_mean_p05': pct(sm, 5), 'shift_mean_p95': pct(sm, 95),
                        'p_shift_mean': pval(sm, row['mean_bhar'], sg),
                        'shift_n_median': float(np.median(snok)), 'shift_draws_empty': int((snok == 0).sum())})
            win_rows.append(row)
            if subset in ('FYP_proposal', 'all') and rule in ('S+', 'R-demand') and h in (12, 36):
                placebo_dump[f'{subset}|{rule}|{h}'] = {'perm_win': [fnum(v) for v in pw],
                                                        'shift_win': [fnum(v) for v in sw],
                                                        'actual_win': row['win_rate'],
                                                        'perm_mean': [fnum(v) for v in pm],
                                                        'shift_mean': [fnum(v) for v in sm],
                                                        'actual_mean': row['mean_bhar']}
            if subset in ('FYP_proposal', 'FYP', 'all') and h in (12, 36):
                rw, rm, _ = placebo_row_stats(BH_REL, mask, h, rule)
                exploratory_relabel.append({'subset': subset, 'rule': rule, 'h': h, 'n': n,
                                            'win_rate': row['win_rate'], 'relabel_win_median': pct(rw, 50),
                                            'relabel_win_p05': pct(rw, 5), 'relabel_win_p95': pct(rw, 95),
                                            'p_relabel_win': pval(rw, row['win_rate'], 1),
                                            'mean_bhar': row['mean_bhar'], 'relabel_mean_median': pct(rm, 50),
                                            'relabel_mean_p05': pct(rm, 5), 'relabel_mean_p95': pct(rm, 95),
                                            'p_relabel_mean': pval(rm, row['mean_bhar'], sg)})
print('win_rates done', time.time() - T_START)

# ----------------------------------------------------------------------------------------------------------------
# 10. subgroups
# ----------------------------------------------------------------------------------------------------------------
DECADE = TE.event_date.str[:3].map({'200': '2000s', '201': '2010s', '202': '2020s'}).values
DIMS = {'plan': TE.plan.values, 'doc_type': TE.doc_type.values, 'stance': TE.stance.values,
        'intensity': TE.intensity.values, 'change_vs_prev': TE.change_vs_prev.values, 'pivot': TE['pivot'].values,
        'decade': DECADE}
DIM_ORDER = {'plan': ['十五', '十一五', '十二五', '十三五', '十四五', '十五五', 'other'],
             'doc_type': ['FYP_proposal', 'FYP_outline', 'other', 'GWR_first'],
             'stance': ['S+', 'R-demand', 'R-supply', 'S0'], 'intensity': ['1', '2', '3'],
             'change_vs_prev': ['new', 'up', 'same', 'down', 'dropped', 'na'], 'pivot': ['1', '0'],
             'decade': ['2000s', '2010s', '2020s']}
sub_rows = []
for dim, vals in DIMS.items():
    extra = sorted(set(vals) - set(DIM_ORDER[dim]))
    for val in DIM_ORDER[dim] + extra:
        for rule in RULES + ['S0']:
            if dim == 'stance' and RULE_STANCE.get(rule, 'S0') != val:
                continue
            for h in (12, 36):
                hi = HS.index(h)
                st = RULE_STANCE.get(rule, 'S0')
                mask = (vals == val) & (STANCE == st) & ~np.isnan(BH[:, hi])
                n = int(mask.sum())
                if n == 0:
                    continue
                x = BH[mask, hi]
                row = {'dim': dim, 'value': val, 'rule': rule, 'h': h, 'n': n,
                       'n_docs': int(len(set(TE.doc_id[mask]))), 'mean_bhar': float(x.mean()),
                       'median_bhar': float(np.median(x)), 'pos_rate': float((x > 0).mean())}
                if rule == 'S0':
                    bs = boot_stats(TE.doc_id.values[mask], x)
                    row.update({'win_rate': None, 'ci_lo': None, 'ci_hi': None,
                                'mean_ci_lo': bs['mean_ci'][0], 'mean_ci_hi': bs['mean_ci'][1]})
                else:
                    w = wins_for(rule, x)
                    bs = boot_stats(TE.doc_id.values[mask], x, w)
                    row.update({'win_rate': float(w.mean()), 'ci_lo': bs['win_ci'][0], 'ci_hi': bs['win_ci'][1],
                                'mean_ci_lo': bs['mean_ci'][0], 'mean_ci_hi': bs['mean_ci'][1]})
                sub_rows.append(row)
print('subgroups done', time.time() - T_START)


# ----------------------------------------------------------------------------------------------------------------
# 11. car_paths, short_window, turnover
# ----------------------------------------------------------------------------------------------------------------
def group_mask(gname):
    return {'S+ FYP_proposal': (STANCE == 'S+') & (DT == 'FYP_proposal'),
            'S+ all': STANCE == 'S+', 'R-demand all': STANCE == 'R-demand',
            'R-supply all': STANCE == 'R-supply', 'S0 all': STANCE == 'S0',
            'pivot all': TE['pivot'].values == '1'}[gname]


car_paths = {}
for gname in GROUPS:
    m_ = group_mask(gname)
    M = PATH[m_]
    bm_ = boot_mean_matrix(TE.doc_id.values[m_], M)
    car_paths[gname] = {'k': KS, 'mean': [fnum(np.nanmean(M[:, j])) if (~np.isnan(M[:, j])).any() else None
                                          for j in range(len(KS))],
                        'lo': [fnum(pct(bm_[:, j], 2.5)) for j in range(len(KS))],
                        'hi': [fnum(pct(bm_[:, j], 97.5)) for j in range(len(KS))],
                        'n': [int((~np.isnan(M[:, j])).sum()) for j in range(len(KS))]}

short_window = []
for gname in GROUPS:
    for k in (1, 5, 20):
        m_ = group_mask(gname) & ~np.isnan(car[k])
        n = int(m_.sum())
        if n == 0:
            short_window.append({'group': gname, 'k': k, 'n': 0, 'mean_car': None, 'ci_lo': None, 'ci_hi': None,
                                 'pos_rate': None}); continue
        x = car[k][m_]
        bs = boot_stats(TE.doc_id.values[m_], x)
        short_window.append({'group': gname, 'k': k, 'n': n, 'n_docs': int(len(set(TE.doc_id[m_]))),
                             'mean_car': float(x.mean()), 'ci_lo': bs['mean_ci'][0], 'ci_hi': bs['mean_ci'][1],
                             'pos_rate': float((x > 0).mean()), 'median_car': float(np.median(x))})

turnover = []
for gname in GROUPS:
    gm = group_mask(gname)
    m_ = gm & ~np.isnan(tsh_pre) & ~np.isnan(tsh_p1)
    m25 = gm & ~np.isnan(tsh_pre) & ~np.isnan(tsh_p25)
    n = int(m_.sum())
    row = {'group': gname, 'n': n}
    if n:
        ch = tsh_p1[m_] - tsh_pre[m_]
        bs = boot_stats(TE.doc_id.values[m_], ch)
        ratio = tsh_p1[m_] / tsh_pre[m_]
        row.update({'share_pre': float(tsh_pre[m_].mean()), 'share_post_1_12': float(tsh_p1[m_].mean()),
                    'change_pp_1_12': float(ch.mean()), 'ci_lo': bs['mean_ci'][0], 'ci_hi': bs['mean_ci'][1],
                    'ratio_post_pre_1_12_mean': float(ratio.mean()),
                    'ratio_post_pre_1_12_median': float(np.median(ratio))})
    else:
        row.update({'share_pre': None, 'share_post_1_12': None, 'change_pp_1_12': None, 'ci_lo': None, 'ci_hi': None})
    n25 = int(m25.sum())
    row['n_25_36'] = n25
    if n25:
        ch25 = tsh_p25[m25] - tsh_pre[m25]
        bs25 = boot_stats(TE.doc_id.values[m25], ch25)
        row.update({'share_post_25_36': float(tsh_p25[m25].mean()), 'share_pre_on_25_36_set': float(tsh_pre[m25].mean()),
                    'change_pp_25_36': float(ch25.mean()), 'ci_lo_25_36': bs25['mean_ci'][0],
                    'ci_hi_25_36': bs25['mean_ci'][1],
                    'ratio_post_pre_25_36_median': float(np.median(tsh_p25[m25] / tsh_pre[m25]))})
    else:
        row['share_post_25_36'] = None
    turnover.append(row)
print('paths/short/turnover done', time.time() - T_START)

# ----------------------------------------------------------------------------------------------------------------
# 12. portfolios (C12)
# ----------------------------------------------------------------------------------------------------------------
H_P1 = np.zeros((T, S), bool); H_P2 = np.zeros((T, S), bool); H_SH = np.zeros((T, S), bool)
for i in range(NT):
    t = T0[i]
    cix = [CI[c] for c in TE.used[i]]
    if STANCE[i] == 'S+':
        e2 = min(t + 36, LAST)
        if t + 1 <= e2:
            H_P2[t + 1:e2 + 1][:, cix] = True
        if DT[i] in ('FYP_proposal', 'FYP_outline'):
            yr = PLAN_LAST_YEAR[TE.doc_id[i][:3]]
            e1 = MI.get(f'{yr}-12', LAST)
            e1 = min(e1, LAST)
            if t + 1 <= e1:
                H_P1[t + 1:e1 + 1][:, cix] = True
    elif STANCE[i] == 'R-demand':
        e3 = min(t + 36, LAST)
        if t + 1 <= e3:
            H_SH[t + 1:e3 + 1][:, cix] = True


def leg(H):
    ret = np.full(T, np.nan); n = np.zeros(T, int); n_hold = np.zeros(T, int)
    for m in range(1, T):
        held = H[m]
        n_hold[m] = held.sum()
        valid = held & HAVE[m] & HAVE[m - 1]        # C14: skip series lacking close of m or m-1
        n[m] = valid.sum()
        if n[m]:
            ret[m] = R[m, valid].mean()
    return ret, n, n_hold


p1, p1n, p1h = leg(H_P1)
p2, p2n, p2h = leg(H_P2)
psh, pshn, pshh = leg(H_SH)
p3 = np.where((p2n > 0) & (pshn > 0), p2 - psh, 0.0)


def port_stats(ret, n, start, is_ls=False, n_short=None):
    idx = np.arange(start, T)
    r = ret[idx].copy()
    empty = int(np.isnan(r).sum())
    r = np.where(np.isnan(r), 0.0, r)          # cash at 0 in an empty month (none expected for P1/P2)
    b = RB[idx]
    ex = r if is_ls else r - b
    M_ = len(idx)
    ann_r = float(np.prod(1 + r) ** (12.0 / M_) - 1)
    ann_b = float(np.prod(1 + b) ** (12.0 / M_) - 1)
    ann_ex = float(12 * ex.mean())
    vol = float(np.std(ex, ddof=1) * math.sqrt(12))
    w = np.cumprod(1 + ex)
    dd = float(np.min(w / np.maximum.accumulate(w) - 1))
    roll = []
    for j in range(35, M_):
        seg = slice(j - 35, j + 1)
        val = np.prod(1 + r[seg]) - 1 if is_ls else np.prod(1 + r[seg]) - np.prod(1 + b[seg])
        roll.append((MONTHS[idx[j]], float(val)))
    rv = np.array([v for _, v in roll])
    out = {'start': MONTHS[start], 'end': MONTHS[LAST], 'months': M_, 'ann_return': ann_r, 'ann_bench': ann_b,
           'ann_excess': ann_ex, 'vol_excess': vol, 'info_ratio': ann_ex / vol if vol > 0 else None,
           'max_drawdown_excess': dd, 'hit_rate': float((ex > 0).mean()),
           'avg_holdings': float(n[idx].mean()) if n_short is None else float((n[idx] + n_short[idx]).mean()),
           'ann_return_minus_bench': ann_r - ann_b, 'months_empty': empty,
           'cum_return': float(np.prod(1 + r) - 1), 'cum_bench': float(np.prod(1 + b) - 1),
           'rolling36_excess': {'month': [m for m, _ in roll], 'value': [v for _, v in roll]},
           'rolling36_summary': {'n': int(rv.size), 'min': fnum(rv.min()) if rv.size else None,
                                 'max': fnum(rv.max()) if rv.size else None,
                                 'median': fnum(np.median(rv)) if rv.size else None,
                                 'share_positive': fnum((rv > 0).mean()) if rv.size else None}}
    return out


st1 = int(np.argmax(p1n > 0)); st2 = int(np.argmax(p2n > 0))
st3 = int(np.argmax((p2n > 0) | (pshn > 0)))
portfolios = {'P1': port_stats(p1, p1n, st1), 'P2': port_stats(p2, p2n, st2),
              'P3': port_stats(p3, p2n, st3, is_ls=True, n_short=pshn)}
portfolios['P3']['avg_long'] = float(p2n[st3:].mean())
portfolios['P3']['avg_short'] = float(pshn[st3:].mean())
portfolios['P3']['months_empty_leg'] = int(((p2n[st3:] == 0) | (pshn[st3:] == 0)).sum())
idx3 = np.arange(st3, T); both = (p2n[idx3] > 0) & (pshn[idx3] > 0)
portfolios['P3']['months_both_legs'] = int(both.sum())
portfolios['P3']['first_month_both_legs'] = MONTHS[idx3[np.argmax(both)]] if both.any() else None
for P, (nn, hh) in {'P1': (p1n, p1h), 'P2': (p2n, p2h)}.items():
    st = {'P1': st1, 'P2': st2}[P]
    portfolios[P]['months_series_skipped_for_data'] = int((hh[st:] > nn[st:]).sum())
portfolios['P3']['months_short_series_skipped_for_data'] = int((pshh[st3:] > pshn[st3:]).sum())

first_pm = min(st1, st2, st3)
with open(os.path.join(OUT, 'portfolio_monthly.csv'), 'w', newline='') as f:
    wr = csv.writer(f)
    wr.writerow(['month', 'bench_ret', 'P1_ret', 'P1_n', 'P2_ret', 'P2_n', 'P3_ret', 'P3_long_n', 'P3_short_n'])
    for m in range(first_pm, T):
        def fv(v, st):
            return '' if (m < st or np.isnan(v)) else repr(float(v))
        p1v = (0.0 if np.isnan(p1[m]) else p1[m]) if m >= st1 else np.nan
        p2v = (0.0 if np.isnan(p2[m]) else p2[m]) if m >= st2 else np.nan
        wr.writerow([MONTHS[m], repr(float(RB[m])), fv(p1v, st1), int(p1n[m]), fv(p2v, st2), int(p2n[m]),
                     fv(p3[m], st3), int(p2n[m]), int(pshn[m])])
print('portfolios done', time.time() - T_START)

# ----------------------------------------------------------------------------------------------------------------
# 13. results.json, placebo_draws.json
# ----------------------------------------------------------------------------------------------------------------
excl = ev.excluded_reason[ev.excluded_reason != ''].value_counts().to_dict()
incomplete_by_h = {str(h): int(np.isnan(BH[:, HS.index(h)]).sum()) for h in HS}
n_by_subset_h = {s: {str(h): int((subset_mask(s) & ~np.isnan(BH[:, HS.index(h)])).sum()) for h in HS} for s in SUBSETS}
n_by_subset_stance_h = {s: {st: {str(h): int((subset_mask(s) & (STANCE == st) & ~np.isnan(BH[:, HS.index(h)])).sum())
                                 for h in HS} for st in ['S+', 'R-demand', 'R-supply', 'S0']} for s in SUBSETS}
stale_used = []
for i in range(NT):
    t = T0[i]
    for c in TE.used[i]:
        for tm in range(t, min(t + 36, LAST) + 1):
            if (c, MONTHS[tm]) in STALE:
                stale_used.append((TE.event_id[i], c, MONTHS[tm]))
meta = {'n_events': NE, 'n_tested': NT, 'excluded': excl, 'first_entry': MONTHS[int(T0.min())],
        'last_bar': BARD[LAST], 'hash_check': hash_check, 'seeds': SEEDS,
        'n_bootstrap': N_BOOT, 'n_placebo': N_PLAC, 'incomplete_by_h': incomplete_by_h,
        'ends_on_partial_month_by_h': {str(h): v for h, v in partial_by_h.items()},
        'n_by_subset_h': n_by_subset_h, 'n_by_subset_stance_h': n_by_subset_stance_h,
        'level_used': TE.level_used.value_counts().to_dict(),
        'n_docs_tested': len(DOCS_T), 'lineage_rows': int(len(lineage)),
        'placebo1_groups_over_capacity': [p for p in pool_info if p['over_capacity']],
        'stale_bars_in_event_windows': len(stale_used),
        'benchmark_days_missing_vs_other_series': sorted(ALL_DAYS - set(DDATES))}
# pre-event drift (section 3 / C5), aggregated by the same groups as the paths
pre_drift = []
for gname in GROUPS:
    for w_, arr in ((12, pre12), (3, pre3)):
        m_ = group_mask(gname) & ~np.isnan(arr)
        n = int(m_.sum())
        row = {'group': gname, 'window': w_, 'n': n}
        if n:
            x = arr[m_]
            bs = boot_stats(TE.doc_id.values[m_], x)
            row.update({'n_docs': int(len(set(TE.doc_id[m_]))), 'mean_pre': float(x.mean()),
                        'ci_lo': bs['mean_ci'][0], 'ci_hi': bs['mean_ci'][1], 'median_pre': float(np.median(x)),
                        'pos_rate': float((x > 0).mean())})
        pre_drift.append(row)
results = {'meta': meta, 'win_rates': win_rows, 'subgroups': sub_rows, 'car_paths': car_paths,
           'short_window': short_window, 'turnover': turnover, 'portfolios': portfolios, 'pre_drift': pre_drift,
           'exploratory': {'note': 'EXPLORATORY, not in the plan: placebo 1 variant that relabels each document\'s '
                                   'distinct actual series to distinct random series of the same level (preserves '
                                   'within-document repetition of industries). Seed perm_relabel_exploratory.',
                           'placebo1_relabel': exploratory_relabel}}
with open(os.path.join(OUT, 'placebo_draws.json'), 'w') as f:
    json.dump(jclean(placebo_dump), f, ensure_ascii=False)

# ----------------------------------------------------------------------------------------------------------------
# 14. self-checks
# ----------------------------------------------------------------------------------------------------------------
checks = {}
# (1) hand recomputation from sw_monthly.csv with the csv module (independent path)
closes = {}
with open(os.path.join(DATA, 'sw_monthly.csv'), newline='') as f:
    for rr in csv.DictReader(f):
        closes[(rr['code'], rr['month'])] = float(rr['close'])
el = pd.read_csv(os.path.join(OUT, 'event_level.csv'), dtype=str, keep_default_na=False)
cand = el[(el.bhar_36 != '') & (el.excluded_reason == '')]
rng_chk = np.random.default_rng(SEEDS['self_check'])
pick = list(rng_chk.choice(cand.index.values, size=5, replace=False))
multi = cand[cand.series_used.str.contains(';')]
if not any(';' in cand.series_used[p] for p in pick) and len(multi):
    pick[-1] = int(rng_chk.choice(np.setdiff1d(multi.index.values, pick)))  # make sure one multi-code event is checked


def add_months(ym, k):
    y, m = int(ym[:4]), int(ym[5:])
    z = y * 12 + (m - 1) + k
    return f'{z // 12:04d}-{z % 12 + 1:02d}'


hand = []
for p in pick:
    r_ = el.loc[p]
    codes_ = r_.series_used.split(';')
    for h in (12, 36):
        g = 1.0
        for k in range(1, h + 1):
            mo, mprev = add_months(r_.entry_month, k), add_months(r_.entry_month, k - 1)
            g *= 1 + sum(closes[(c, mo)] / closes[(c, mprev)] - 1 for c in codes_) / len(codes_)
        b = closes[(BENCH, add_months(r_.entry_month, h))] / closes[(BENCH, r_.entry_month)]
        val = g - b
        csv_val = float(r_[f'bhar_{h}'])
        hand.append({'event_id': r_.event_id, 'series_used': r_.series_used, 'entry_month': r_.entry_month, 'h': h,
                     'hand': val, 'csv': csv_val, 'abs_diff': abs(val - csv_val)})
checks['hand_recompute'] = {'rows': hand, 'max_abs_diff': max(x['abs_diff'] for x in hand),
                            'pass': max(x['abs_diff'] for x in hand) < 1e-9}
# (2) primary win rate from event_level.csv
pr = el[(el.doc_type == 'FYP_proposal') & (el.stance == 'S+') & (el.bhar_36 != '')]
w_csv = pr.win_36.astype(int).mean()
m_csv = pr.bhar_36.astype(float).mean()
prow = [r_ for r_ in win_rows if r_['subset'] == 'FYP_proposal' and r_['rule'] == 'S+' and r_['h'] == 36][0]
w12 = el[(el.doc_type == 'FYP_proposal') & (el.stance == 'S+') & (el.bhar_12 != '')]
prow12 = [r_ for r_ in win_rows if r_['subset'] == 'FYP_proposal' and r_['rule'] == 'S+' and r_['h'] == 12][0]
allrows_ok = True
for r_ in win_rows:
    if r_['n'] == 0 or r_['rule'] not in ('S+', 'R-demand', 'R-supply H-a') or r_['h'] not in (12, 36):
        continue
    st = RULE_STANCE[r_['rule']]
    sub = el[(el.stance == st) & (el[f'win_{r_["h"]}'] != '')]
    if r_['subset'] == 'FYP_proposal':
        sub = sub[sub.doc_type == 'FYP_proposal']
    elif r_['subset'] == 'FYP':
        sub = sub[sub.doc_type.isin(['FYP_proposal', 'FYP_outline'])]
    elif r_['subset'] in ('other', 'GWR_first'):
        sub = sub[sub.doc_type == r_['subset']]
    if len(sub) != r_['n'] or abs(sub[f'win_{r_["h"]}'].astype(int).mean() - r_['win_rate']) > 1e-12:
        allrows_ok = False
checks['win_rate_consistency'] = {'primary_n_csv': int(len(pr)), 'primary_n_json': prow['n'],
                                  'primary_win_csv': float(w_csv), 'primary_win_json': prow['win_rate'],
                                  'primary_mean_csv': float(m_csv), 'primary_mean_json': prow['mean_bhar'],
                                  'h12_n_csv': int(len(w12)), 'h12_win_csv': float(w12.win_12.astype(int).mean()),
                                  'h12_win_json': prow12['win_rate'],
                                  'all_h12_h36_rows_match': allrows_ok,
                                  'pass': bool(len(pr) == prow['n'] and abs(w_csv - prow['win_rate']) < 1e-12
                                               and abs(m_csv - prow['mean_bhar']) < 1e-12 and allrows_ok
                                               and abs(w12.win_12.astype(int).mean() - prow12['win_rate']) < 1e-12)}
# (3) timing
bad_entry = el[el.entry_month < el.event_date.str[:7]]
bar_after = all(BARD[MI[m_]] > d_ for m_, d_ in zip(el.entry_month, el.event_date))
beyond = 0
for _, r_ in el[el.excluded_reason == ''].iterrows():
    for h in HS:
        if r_[f'bhar_{h}'] != '' and MI[r_.entry_month] + h > LAST:
            beyond += 1
day_beyond = 0
for i in range(NT):
    d0 = bisect.bisect_left(DDATES, TE.event_date[i])
    for k in (1, 5, 20):
        if not np.isnan(car[k][i]) and (d0 + k > ND - 1 or DDATES[d0] < TE.event_date[i]):
            day_beyond += 1
port_lookahead = 0
# a series can be held in month m only if some event pointing to it has t0 <= m-1
first_hold = {}
for i in range(NT):
    for c in TE.used[i]:
        first_hold.setdefault(c, []).append(T0[i])
for H_ in (H_P1, H_P2, H_SH):
    for c, ts in first_hold.items():
        hm = np.where(H_[:, CI[c]])[0]
        if hm.size and hm.min() < min(ts) + 1:
            port_lookahead += 1
checks['timing'] = {'entry_before_event_month': int(len(bad_entry)), 'entry_bar_strictly_after_event_date': bar_after,
                    'bhar_beyond_last_bar': beyond, 'car_beyond_last_day_or_day0_before_event': day_beyond,
                    'portfolio_hold_before_t0_plus_1': port_lookahead,
                    'pass': bool(len(bad_entry) == 0 and bar_after and beyond == 0 and day_beyond == 0
                                 and port_lookahead == 0)}
checks['placebo_machinery'] = {'placebo1_recompute_200_max_rel_diff': PLACEBO1_CHECK_MAXRELDIFF,
                               'shift0_reproduces_actual_max_abs_diff': SHIFT0_MAXDIFF,
                               'shift0_same_missing_pattern': SHIFT0_SAME_NAN,
                               'share_doc_shifts_with_entry_eq_t0_plus_shift': SHIFT_ENTRY_EQ_T0_PLUS_S,
                               'pass': bool(PLACEBO1_CHECK_MAXRELDIFF < 1e-5 and SHIFT0_SAME_NAN
                                            and SHIFT0_MAXDIFF < 1e-10)}
checks['counts'] = {'n_events': NE, 'n_tested': NT, 'excluded': excl, 'incomplete_by_h': incomplete_by_h,
                    'n_by_subset_h': n_by_subset_h}
results['meta']['checks'] = {k: v for k, v in checks.items()}
runtime = time.time() - T_START
results['meta']['runtime_note'] = (f'full run {runtime:.0f} s on 2 CPUs; placebo BHARs vectorised by gathering monthly '
                                   f'returns for replacement codes; date-shift outcomes precomputed for all 38 shifts')
with open(os.path.join(OUT, 'results.json'), 'w') as f:
    json.dump(jclean(results), f, ensure_ascii=False, indent=1)
print('results written', runtime)

# ----------------------------------------------------------------------------------------------------------------
# 15. report.md (generated from the computed numbers)
# ----------------------------------------------------------------------------------------------------------------
RJ = jclean(results)


def f(x, d=3):
    return '–' if x is None or (isinstance(x, float) and math.isnan(x)) else f'{x:.{d}f}'


def pc(x, d=1):
    return '–' if x is None or (isinstance(x, float) and math.isnan(x)) else f'{100 * x:.{d}f}%'


def ci(lo, hi, d=3):
    return f'[{f(lo, d)}, {f(hi, d)}]'


W = {(r_['subset'], r_['rule'], r_['h']): r_ for r_ in RJ['win_rates']}
prim, sec = W[('FYP_proposal', 'S+', 36)], W[('FYP_proposal', 'S+', 12)]
prim_docs = sorted(set(TE.doc_id[row_mask('FYP_proposal', 'S+', 36)]))
PF = RJ['portfolios']
_p2_empty = [MONTHS[m] for m in range(st2, T) if p2n[m] == 0]
_p2_empty_txt = (f'{_p2_empty[0]}…{_p2_empty[-1]}' if _p2_empty and
                 MI[_p2_empty[-1]] - MI[_p2_empty[0]] + 1 == len(_p2_empty) else ', '.join(_p2_empty))
_partial_docs = sorted(set(TE.doc_id[i] for i in range(NT) if T0[i] + 12 == LAST))
_n_doc_partial = {d: int((TE.doc_id == d).sum()) for d in _partial_docs}
_partial_txt = ', '.join(f'{d} ({sum(1 for i in range(NT) if TE.doc_id[i] == d and T0[i] + 12 == LAST)} of '
                         f'{_n_doc_partial[d]} tested events)' for d in _partial_docs)
_n_gapdrop, _gap_fallback = 0, []
for r_ in ev[ev.tested].itertuples():
    _t = r_.t0
    _cands = r_.l2c if r_.level_used == 'L2' else r_.l1c
    _n_gapdrop += int(len([c for c in _cands if HAVE[_t, CI[c]]]) > len(r_.used))
    if r_.level_used == 'L1' and any(HAVE[_t, CI[c]] for c in r_.l2c):
        _gap_fallback.append((r_.event_id, ';'.join(r_.l2c), r_.entry_month))
_small = [r_ for r_ in RJ['win_rates'] if r_['n'] and not (r_['subset'] == 'FYP_proposal' and r_['rule'] == 'S+'
          and r_['h'] == 36) and min(r_[k] for k in ('p_perm_win', 'p_perm_mean', 'p_shift_win', 'p_shift_mean')) <= 0.05]
L = []
A = L.append
A('# Backtest report — policy wording vs. SW industry index returns (analysis plan v1)')
A('')
A(f'Executed by the independent backtest agent with `backtest/backtest.py` (Python {sys.version.split()[0]}, numpy '
  f'{np.__version__}, pandas {pd.__version__}). Numbers are decimals (0.123 = 12.3%) unless shown with a % sign. '
  f'Every figure here is also in `results.json`; per-event values are in `event_level.csv`.')
A('')
A('## 1. Inputs and what was tested')
A('')
A(f'- **Hash check:** events files {"match" if hash_ok_events else "DO NOT match"} `events/FROZEN.sha256`; all '
  f'{len(hash_details["prereg"])} prereg and data files listed in `prereg/PREREG.sha256` '
  f'{"match" if hash_ok_prereg else "DO NOT all match"}. Not checked: '
  f'{", ".join(hash_details["not_checked"])} (outside the inputs this agent may open).')
A(f'- **Events:** {NE} events from {ev.doc_id.nunique()} documents. Tested: {NT} events from {len(DOCS_T)} documents '
  f'({RJ["meta"]["level_used"].get("L2", 0)} on L2 series, {RJ["meta"]["level_used"].get("L1", 0)} on L1). '
  f'Excluded: ' + ', '.join(f'{k} = {v}' for k, v in excl.items()) + '. No event was edited, added, dropped or '
  're-dated; ' + (f'data_gap (C14) removed no event ' if 'data_gap' not in excl else f'data_gap removed {excl["data_gap"]} events ')
  + f'({_n_gapdrop} events lost one of several series to the gap rule and kept the rest at the same level; '
  f'{len(_gap_fallback)} events had L2 series at entry that all failed the gap rule and fell back to L1 under C14: '
  + ', '.join(f'{e_} [L2 {c_}, entry {m_}]' for e_, c_, m_ in _gap_fallback) + ').')
A(f'- **Timing:** entry = close of the first month-end (801003 bar date) strictly after the event date; first entry '
  f'{RJ["meta"]["first_entry"]}; last bar {RJ["meta"]["last_bar"]} (2026-10 is a partial month). Incomplete horizons '
  f'(excluded from that horizon): ' + ', '.join(f'h={h}: {v}' for h, v in incomplete_by_h.items()) + '. '
  f'{partial_by_h[12]} events have their 12-month horizon ending on the partial month ({_partial_txt}); other '
  'horizons ending there: ' + ', '.join(f'h={h}: {v}' for h, v in partial_by_h.items() if h != 12) + '.')
A('- **Measure:** BHAR(h) = compounded industry return minus compounded 申万A指 (801003) return from the entry close '
  'to the close h months later; multi-code events use an equal-weight, monthly-rebalanced average. Price indices on '
  'both sides.')
A('- **Win rules (plan section 4, C11):** S+ wins if BHAR > 0; R-demand wins if BHAR < 0; R-supply is shown under '
  'H-a (win if BHAR < 0) and H-b (win if BHAR > 0); ties lose; S0 is descriptive.')
A(f'- **Inference:** doc-clustered bootstrap (C10, {N_BOOT:,} draws, percentile 95% CI); placebo 1 = random industries '
  f'at the same dates (C8, {N_PLAC:,} draws); placebo 2 = each document shifted by ±6–24 months (C9, {N_PLAC:,} '
  'draws). p-values are one-sided in the direction of the rule (share of placebo draws at least as favourable as '
  'the actual result).')
A('- **Primary test (C1):** doc_type = FYP_proposal, stance = S+, h = 36. Everything else is secondary; results on '
  'doc_type = other are **exploratory** (C1).')
A('')
A('## 2. Plain-language findings')
A('')
p4 = [prim['p_perm_win'], prim['p_perm_mean'], prim['p_shift_win'], prim['p_shift_mean']]
ci_has_half = prim['ci_lo'] <= 0.5 <= prim['ci_hi']
A(f'**Primary test.** {prim["n"]} S+ events from the {len(prim_docs)} five-year-plan proposals with a complete '
  f'36-month window ({", ".join(prim_docs)}; the 十五五 proposal P15-A1 is too recent). Of these, '
  f'{int(round(prim["win_rate"] * prim["n"]))} beat 申万A指 over 36 months: win rate {pc(prim["win_rate"])} '
  f'(95% CI {pc(prim["ci_lo"])}–{pc(prim["ci_hi"])}). Mean BHAR(36) {f(prim["mean_bhar"])} '
  f'(CI {ci(prim["mean_ci_lo"], prim["mean_ci_hi"])}), median {f(prim["median_bhar"])}. Random industries on the '
  f'same dates (placebo 1) give a median win rate of {pc(prim["perm_win_median"])} (5–95%: '
  f'{pc(prim["perm_win_p05"])}–{pc(prim["perm_win_p95"])}); p = {f(prim["p_perm_win"])} for the win rate and '
  f'{f(prim["p_perm_mean"])} for the mean. The same industries at shifted dates (placebo 2) give a median win rate of '
  f'{pc(prim["shift_win_median"])}; p = {f(prim["p_shift_win"])} (win rate) and {f(prim["p_shift_mean"])} (mean). '
  + ('None of the four placebo p-values is below 0.05 and the win-rate CI includes 50%: the primary test does not '
     'show that buying the industries favoured in FYP-proposal wording beat the market over the following three '
     'years.' if (min(p4) > 0.05 and ci_has_half) else
     'At least one placebo p-value is at or below 0.05 or the CI excludes 50%; see the table below.'))
A('')
hi_dir = sec['p_perm_win'] is not None and sec['p_perm_win'] >= 0.95
A(f'**Secondary horizon (12 months).** S+ FYP-proposal events (n = {sec["n"]}, {sec["n_docs"]} documents incl. '
  f'P15-A1) won {pc(sec["win_rate"])} of the time (CI {pc(sec["ci_lo"])}–{pc(sec["ci_hi"])}), mean BHAR(12) '
  f'{f(sec["mean_bhar"])} (CI {ci(sec["mean_ci_lo"], sec["mean_ci_hi"])}). One-sided p-values in the rule\'s '
  f'direction: placebo 1 {f(sec["p_perm_win"])} / {f(sec["p_perm_mean"])}, placebo 2 {f(sec["p_shift_win"])} / '
  f'{f(sec["p_shift_mean"])} (win rate / mean). '
  + (f'The actual win rate lies below the industry-permutation distribution (5–95%: {pc(sec["perm_win_p05"])}–'
     f'{pc(sec["perm_win_p95"])}), i.e. the favoured industries tended to lag the market over the first year. The '
     'plan registers only tests in the direction of the rule, so this underperformance is an **exploratory** '
     'observation, not a registered finding. One-sided p (perm win) for FYP_proposal S+ at h = 1/3/6: '
     + '/'.join(f(W[('FYP_proposal', 'S+', h)]['p_perm_win']) for h in (1, 3, 6))
     + f'; for all S+ events at h = 12: {f(W[("all", "S+", 12)]["p_perm_win"])} (section 4).' if hi_dir else ''))
A('')
for subset in ('all', 'FYP_proposal'):
    rd = W[(subset, 'R-demand', 36)]; rd12 = W[(subset, 'R-demand', 12)]
    A(f'**R-demand ({subset}{", exploratory for the other-document part" if subset == "all" else ""}).** 36 months: '
      f'n = {rd["n"]} ({rd["n_docs"]} docs), win rate (BHAR < 0) {pc(rd["win_rate"])} (CI {pc(rd["ci_lo"])}–'
      f'{pc(rd["ci_hi"])}), mean BHAR {f(rd["mean_bhar"])} (CI {ci(rd["mean_ci_lo"], rd["mean_ci_hi"])}), median '
      f'{f(rd["median_bhar"])}; p (perm win/mean) {f(rd["p_perm_win"])}/{f(rd["p_perm_mean"])}, p (shift win/mean) '
      f'{f(rd["p_shift_win"])}/{f(rd["p_shift_mean"])}. 12 months: n = {rd12["n"]}, win rate {pc(rd12["win_rate"])}, '
      f'mean BHAR {f(rd12["mean_bhar"])}, p (perm win) {f(rd12["p_perm_win"])}, p (shift win) '
      f'{f(rd12["p_shift_win"])}. '
      + ('Restricted-demand industries did not, on average, underperform: the mean BHAR at 36 months is positive.'
         if rd['mean_bhar'] > 0 else 'The mean BHAR at 36 months is negative (in the direction of the rule).'))
    A('')
ha, hb = W[('all', 'R-supply H-a', 36)], W[('all', 'R-supply H-b', 36)]
ha12, hb12 = W[('all', 'R-supply H-a', 12)], W[('all', 'R-supply H-b', 12)]
A(f'**R-supply (all documents; neither hypothesis primary).** 36 months, n = {ha["n"]} ({ha["n_docs"]} docs), mean '
  f'BHAR {f(ha["mean_bhar"])}, median {f(ha["median_bhar"])}. H-a "avoid" win rate {pc(ha["win_rate"])} (CI '
  f'{pc(ha["ci_lo"])}–{pc(ha["ci_hi"])}; p perm/shift {f(ha["p_perm_win"])}/{f(ha["p_shift_win"])}); H-b "incumbents '
  f'gain" win rate {pc(hb["win_rate"])} (CI {pc(hb["ci_lo"])}–{pc(hb["ci_hi"])}; p perm/shift '
  f'{f(hb["p_perm_win"])}/{f(hb["p_shift_win"])}). 12 months: H-a {pc(ha12["win_rate"])}, H-b {pc(hb12["win_rate"])} '
  f'(n = {ha12["n"]}); p (perm mean, H-a) at 12 months = {f(ha12["p_perm_mean"])} (one of many secondary rows; '
  f'exploratory weight). '
  + ('Neither hypothesis has a win-rate CI that excludes 50% at the primary horizon.'
     if (ha['ci_lo'] <= 0.5 <= ha['ci_hi'] and hb['ci_lo'] <= 0.5 <= hb['ci_hi'])
     else 'At least one hypothesis has a win-rate CI excluding 50% at the primary horizon.'))
A('')
A(f'**Other rows with a placebo p ≤ 0.05 (all exploratory/secondary; {len(_small)} of '
  f'{sum(1 for r_ in RJ["win_rates"] if r_["n"]) - 1} non-empty non-primary rows, each with 4 p-values).** '
  + '; '.join(f'{r_["subset"]} {r_["rule"]} h={r_["h"]} (n={r_["n"]}, win {f(r_["win_rate"])}, mean {f(r_["mean_bhar"])}; '
              + ', '.join(f'{k} {f(r_[k])}' for k in ('p_perm_win', 'p_perm_mean', 'p_shift_win', 'p_shift_mean')
                          if r_[k] is not None and r_[k] <= 0.05) + ')' for r_ in _small) + '.')
A('')
A(f'**Portfolios (calendar time, 申万A指 benchmark).** P1 "follow the plan" ({PF["P1"]["start"]}–{PF["P1"]["end"]}, '
  f'{PF["P1"]["months"]} months, avg {f(PF["P1"]["avg_holdings"], 1)} series): annualised return '
  f'{pc(PF["P1"]["ann_return"])} vs benchmark {pc(PF["P1"]["ann_bench"])}; annualised excess (12 x mean monthly) '
  f'{pc(PF["P1"]["ann_excess"])}, tracking volatility {pc(PF["P1"]["vol_excess"])}, information ratio '
  f'{f(PF["P1"]["info_ratio"], 2)}, max drawdown of excess {pc(PF["P1"]["max_drawdown_excess"])}, beats the '
  f'benchmark in {pc(PF["P1"]["hit_rate"])} of months. P2 "all S+" ({PF["P2"]["start"]}–{PF["P2"]["end"]}): '
  f'{pc(PF["P2"]["ann_return"])} vs {pc(PF["P2"]["ann_bench"])}, excess {pc(PF["P2"]["ann_excess"])}, IR '
  f'{f(PF["P2"]["info_ratio"], 2)}, max DD {pc(PF["P2"]["max_drawdown_excess"])}, hit rate {pc(PF["P2"]["hit_rate"])}'
  f' (P2 was empty and held cash at 0 in {PF["P2"]["months_empty"]} months, {_p2_empty_txt}). P3 "long S+ / short '
  f'R-demand" ({PF["P3"]["start"]}–{PF["P3"]["end"]}): long-short annualised {pc(PF["P3"]["ann_return"])}, mean '
  f'{pc(PF["P3"]["ann_excess"])} a year, volatility {pc(PF["P3"]["vol_excess"])}, IR {f(PF["P3"]["info_ratio"], 2)}, '
  f'max DD {pc(PF["P3"]["max_drawdown_excess"])}, positive in {pc(PF["P3"]["hit_rate"])} of months '
  f'({PF["P3"]["months_empty_leg"]} months had an empty leg and count as 0). The portfolio tests have no registered '
  'significance test; the numbers are descriptive.')
A('')
pdict = {(r_['group'], r_['window']): r_ for r_ in RJ['pre_drift']}
swd = {(r_['group'], r_['k']): r_ for r_ in RJ['short_window']}
tod = {r_['group']: r_ for r_ in RJ['turnover']}
A(f'**Before and around the event.** Pre-entry drift (BHAR over the 12 months up to entry) for S+ FYP-proposal '
  f'events: mean {f(pdict[("S+ FYP_proposal", 12)]["mean_pre"])} (CI '
  f'{ci(pdict[("S+ FYP_proposal", 12)]["ci_lo"], pdict[("S+ FYP_proposal", 12)]["ci_hi"])}); all S+: '
  f'{f(pdict[("S+ all", 12)]["mean_pre"])}. Daily reaction CAR[0,+5] for all S+ events: '
  f'{f(swd[("S+ all", 5)]["mean_car"], 4)} (CI {ci(swd[("S+ all", 5)]["ci_lo"], swd[("S+ all", 5)]["ci_hi"], 4)}); '
  f'S+ FYP proposals: {f(swd[("S+ FYP_proposal", 5)]["mean_car"], 4)}. Turnover share after S+ FYP proposals '
  f'changed by {f(tod["S+ FYP_proposal"]["change_pp_1_12"], 4)} (share units; ×100 = percentage points; CI '
  f'{ci(tod["S+ FYP_proposal"]["ci_lo"], tod["S+ FYP_proposal"]["ci_hi"], 4)}) from months −12…−1 to +1…+12'
  + ((', i.e. the favoured industries\' share of market turnover fell slightly rather than rose. '
      if tod['S+ FYP_proposal']['ci_hi'] < 0 else
      (', i.e. it rose. ' if tod['S+ FYP_proposal']['ci_lo'] > 0 else ' (CI includes zero). ')))
  + 'Short-window, drift and turnover results carry no registered test; they are descriptive (doc-clustered CIs).')
A('')
A('## 3. Main win-rate table (C13 subsets; h = 36 primary, h = 12 secondary)')
A('')
A('`other` rows are exploratory (C1). GWR_first: no event in the table has this doc_type, so the subset is empty. '
  'p-values: one-sided, placebo draws at least as favourable as actual.')
A('')
A('| subset | rule | h | n (docs) | win rate [95% CI] | mean BHAR [95% CI] | median | perm win: median [5–95%] | '
  'p perm win | p perm mean | shift win: median [5–95%] | p shift win | p shift mean |')
A('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for h in (36, 12):
    for subset in SUBSETS:
        for rule in RULES:
            r_ = W[(subset, rule, h)]
            if r_['n'] == 0:
                A(f'| {subset} | {rule} | {h} | 0 | – | – | – | – | – | – | – | – | – |')
                continue
            A(f'| {subset}{" (expl.)" if subset == "other" else ""} | {rule} | {h} | {r_["n"]} ({r_["n_docs"]}) | '
              f'{f(r_["win_rate"])} {ci(r_["ci_lo"], r_["ci_hi"])} | {f(r_["mean_bhar"])} '
              f'{ci(r_["mean_ci_lo"], r_["mean_ci_hi"])} | {f(r_["median_bhar"])} | {f(r_["perm_win_median"])} '
              f'{ci(r_["perm_win_p05"], r_["perm_win_p95"])} | {f(r_["p_perm_win"])} | {f(r_["p_perm_mean"])} | '
              f'{f(r_["shift_win_median"])} {ci(r_["shift_win_p05"], r_["shift_win_p95"])} | {f(r_["p_shift_win"])} | '
              f'{f(r_["p_shift_mean"])} |')
A('')
A('## 4. All horizons (descriptive except h = 36 / 12)')
A('')
A('| subset | rule | h | n | win rate [CI] | mean BHAR | median BHAR [CI] | p perm win | p shift win |')
A('|---|---|---|---|---|---|---|---|---|')
for subset, rule in (('FYP_proposal', 'S+'), ('FYP', 'S+'), ('all', 'S+'), ('all', 'R-demand'),
                     ('all', 'R-supply H-a')):
    for h in HS:
        r_ = W[(subset, rule, h)]
        A(f'| {subset} | {rule} | {h} | {r_["n"]} | {f(r_["win_rate"])} {ci(r_["ci_lo"], r_["ci_hi"])} | '
          f'{f(r_["mean_bhar"])} | {f(r_["median_bhar"])} {ci(r_["median_ci_lo"], r_["median_ci_hi"])} | '
          f'{f(r_["p_perm_win"])} | {f(r_["p_shift_win"])} |')
A('')
A('Note: the FYP_proposal S+ mean at h = 24 ({}) is pulled down by P11-A1 (entry 2005-10, window ending at the 2007 '
  'market peak, where BHAR as a difference of gross growth reaches −3.7 for industries that lagged a ~5x benchmark '
  'rise); the median is {}.'.format(f(W[('FYP_proposal', 'S+', 24)]['mean_bhar']),
                                    f(W[('FYP_proposal', 'S+', 24)]['median_bhar'])))
A('')
A('## 5. Subgroups (all reported, no selection; secondary/exploratory)')
A('')
A('CIs are doc-clustered win-rate intervals; with 2–5 documents per cell (every plan and FYP-only cell) they are not '
  'reliable and are shown only for completeness. R-demand h = 12, R-supply and S0 rows (and values with no S+ or '
  'R-demand events, e.g. change_vs_prev = dropped) are in `results.json`.')
A('')
SG = {(r_['dim'], r_['value'], r_['rule'], r_['h']): r_ for r_ in RJ['subgroups']}
A('| dim | value | S+ h=36: n (docs) | win [CI] | mean | median | S+ h=12: n | win | mean | R-demand h=36: n | win | mean |')
A('|---|---|---|---|---|---|---|---|---|---|---|---|')
for dim in DIMS:
    vals_present = [v for v in DIM_ORDER[dim] + sorted(set(DIMS[dim]) - set(DIM_ORDER[dim]))
                    if any(k[0] == dim and k[1] == v for k in SG)]
    for v in vals_present:
        a = SG.get((dim, v, 'S+', 36)); b = SG.get((dim, v, 'S+', 12)); c = SG.get((dim, v, 'R-demand', 36))
        if not (a or b or c):
            continue
        A(f'| {dim} | {v} | ' + (f'{a["n"]} ({a["n_docs"]}) | {f(a["win_rate"])} {ci(a["ci_lo"], a["ci_hi"])} | '
                                 f'{f(a["mean_bhar"])} | {f(a["median_bhar"])}' if a else '– | – | – | –') + ' | '
          + (f'{b["n"]} | {f(b["win_rate"])} | {f(b["mean_bhar"])}' if b else '– | – | –') + ' | '
          + (f'{c["n"]} | {f(c["win_rate"])} | {f(c["mean_bhar"])}' if c else '– | – | –') + ' |')
A('')
A('## 6. Event-time paths (section 8)')
A('')
A('Mean of path(k) = I(t0+k)/I(t0) − B(t0+k)/B(t0) (k > 0: BHAR(k); k < 0: a positive value means the industry '
  'lagged the market before entry). n in parentheses. Bootstrap bands are in `results.json`.')
A('')
KSHOW = [-12, -6, -3, -1, 0, 1, 3, 6, 12, 24, 36]
A('| group | ' + ' | '.join(f'k={k}' for k in KSHOW) + ' |')
A('|---|' + '---|' * len(KSHOW))
for g_, v in RJ['car_paths'].items():
    A(f'| {g_} | ' + ' | '.join(f'{f(v["mean"][KS.index(k)])} ({v["n"][KS.index(k)]})' for k in KSHOW) + ' |')
A('')
A('## 7. Pre-event drift (BHAR from t0−12 / t0−3 to entry)')
A('')
A('| group | window | n (docs) | mean [CI] | median | share > 0 |')
A('|---|---|---|---|---|---|')
for r_ in RJ['pre_drift']:
    if r_['n']:
        A(f'| {r_["group"]} | {r_["window"]} m | {r_["n"]} ({r_["n_docs"]}) | {f(r_["mean_pre"])} '
          f'{ci(r_["ci_lo"], r_["ci_hi"])} | {f(r_["median_pre"])} | {f(r_["pos_rate"])} |')
A('')
A('## 8. Short-window reaction (daily CAR vs 801003)')
A('')
A('| group | window | n (docs) | mean CAR [CI] | median | share > 0 |')
A('|---|---|---|---|---|---|')
for r_ in RJ['short_window']:
    if r_['n']:
        A(f'| {r_["group"]} | [0,+{r_["k"]}] | {r_["n"]} ({r_["n_docs"]}) | {f(r_["mean_car"], 4)} '
          f'{ci(r_["ci_lo"], r_["ci_hi"], 4)} | {f(r_["median_car"], 4)} | {f(r_["pos_rate"])} |')
A('')
A('## 9. Turnover share (industry turnover ÷ 申万A指 turnover)')
A('')
A('| group | n | share −12…−1 | share +1…+12 | change [CI] | median ratio after/before | n (25–36) | share +25…+36 | '
  'change 25–36 [CI] |')
A('|---|---|---|---|---|---|---|---|---|')
for r_ in RJ['turnover']:
    if r_['n']:
        A(f'| {r_["group"]} | {r_["n"]} | {f(r_["share_pre"], 4)} | {f(r_["share_post_1_12"], 4)} | '
          f'{f(r_["change_pp_1_12"], 4)} {ci(r_["ci_lo"], r_["ci_hi"], 4)} | {f(r_["ratio_post_pre_1_12_median"])} | '
          f'{r_["n_25_36"]} | {f(r_.get("share_post_25_36"), 4)} | {f(r_.get("change_pp_25_36"), 4)} '
          f'{ci(r_.get("ci_lo_25_36"), r_.get("ci_hi_25_36"), 4)} |')
A('')
A('## 10. Portfolios (C12)')
A('')
A('| | start–end | months | ann. return | ann. 申万A指 | ann. excess (12×mean) | vol of excess | IR | max DD of excess | '
  'hit rate | avg holdings | rolling 36m excess: median / min / max / share > 0 |')
A('|---|---|---|---|---|---|---|---|---|---|---|---|')
for P in ('P1', 'P2', 'P3'):
    v = PF[P]; rs = v['rolling36_summary']
    A(f'| {P} | {v["start"]}–{v["end"]} | {v["months"]} | {f(v["ann_return"])} | {f(v["ann_bench"])} | '
      f'{f(v["ann_excess"])} | {f(v["vol_excess"])} | {f(v["info_ratio"], 2)} | {f(v["max_drawdown_excess"])} | '
      f'{f(v["hit_rate"])} | {f(v["avg_holdings"], 1)} | {f(rs["median"])} / {f(rs["min"])} / {f(rs["max"])} / '
      f'{f(rs["share_positive"])} |')
A('')
A(f'P3 is a long-short return (no benchmark subtraction): its "ann. return" is the compounded long-short return and '
  f'"excess" is the same series. P3 long leg = P2 holdings (avg {f(PF["P3"]["avg_long"], 1)} series), short leg '
  f'avg {f(PF["P3"]["avg_short"], 1)} series; both legs are non-empty from {PF["P3"]["first_month_both_legs"]} '
  f'({PF["P3"]["months_both_legs"]} months). P1 skipped a held series for missing data in '
  f'{PF["P1"]["months_series_skipped_for_data"]} months (801193/801951 gaps, C14). The last month (2026-10) is '
  'partial.')
A('')
A('## 11. Exploratory: placebo 1 variant preserving within-document repetition (not in the plan)')
A('')
A('Because many events in one document map to the same industry while C8 gives them distinct replacement industries, '
  'the registered placebo 1 may understate how much a document\'s win rate can vary by chance. This **exploratory** '
  'variant relabels each document\'s distinct actual series to distinct random series of the same level, so events '
  'that shared an industry still share one. It is reported only as a sensitivity check.')
A('')
A('| subset | rule | h | n | actual win | relabel win median [5–95%] | p win | actual mean | relabel mean median '
  '[5–95%] | p mean |')
A('|---|---|---|---|---|---|---|---|---|---|')
for r_ in RJ['exploratory']['placebo1_relabel']:
    if r_['rule'] in ('S+', 'R-demand'):
        A(f'| {r_["subset"]} | {r_["rule"]} | {r_["h"]} | {r_["n"]} | {f(r_["win_rate"])} | '
          f'{f(r_["relabel_win_median"])} {ci(r_["relabel_win_p05"], r_["relabel_win_p95"])} | '
          f'{f(r_["p_relabel_win"])} | {f(r_["mean_bhar"])} | {f(r_["relabel_mean_median"])} '
          f'{ci(r_["relabel_mean_p05"], r_["relabel_mean_p95"])} | {f(r_["p_relabel_mean"])} |')
A('')
A('## Checks')
A('')
hc = checks['hand_recompute']
A(f'1. **Hand recomputation** (seed {SEEDS["self_check"]}): BHAR(12) and BHAR(36) for 5 random tested events were '
  f'recomputed with the csv module directly from `sw_monthly.csv` closes (equal-weight monthly-rebalanced for '
  f'multi-code events). Max absolute difference vs `event_level.csv`: {hc["max_abs_diff"]:.1e} — '
  f'{"PASS" if hc["pass"] else "FAIL"}.')
A('')
A('   | event | series | entry | h | hand | event_level.csv |')
A('   |---|---|---|---|---|---|')
for x in hc['rows']:
    A(f'   | {x["event_id"]} | {x["series_used"]} | {x["entry_month"]} | {x["h"]} | {x["hand"]:.10f} | '
      f'{x["csv"]:.10f} |')
wc = checks['win_rate_consistency']
A(f'2. **Win rates vs event_level.csv:** primary test n = {wc["primary_n_csv"]} (csv) vs {wc["primary_n_json"]} (json); '
  f'win share {wc["primary_win_csv"]:.6f} vs {wc["primary_win_json"]:.6f}; mean BHAR(36) {wc["primary_mean_csv"]:.6f} '
  f'vs {wc["primary_mean_json"]:.6f}; h = 12: {wc["h12_win_csv"]:.6f} vs {wc["h12_win_json"]:.6f}. Every '
  f'non-empty S+ / R-demand / R-supply H-a row at h = 12 and 36 in every subset also matches the csv: '
  f'{"yes" if wc["all_h12_h36_rows_match"] else "NO"} — {"PASS" if wc["pass"] else "FAIL"}.')
tc = checks['timing']
A(f'3. **Timing:** events whose entry month precedes the event month: {tc["entry_before_event_month"]}; every entry '
  f'bar date is strictly after the event date: {tc["entry_bar_strictly_after_event_date"]}; BHAR values whose horizon '
  f'runs past the last bar: {tc["bhar_beyond_last_bar"]}; daily CARs running past the last day or with day 0 before '
  f'the event date: {tc["car_beyond_last_day_or_day0_before_event"]}; portfolio holdings before t0+1: '
  f'{tc["portfolio_hold_before_t0_plus_1"]} — {"PASS" if tc["pass"] else "FAIL"}.')
A(f'4. **Counts.** Events {NE}; tested {NT}; excluded by reason: ' + ', '.join(f'{k} {v}' for k, v in excl.items())
  + '. Incomplete horizons (tested events excluded from that horizon): '
  + ', '.join(f'h={h} {v}' for h, v in incomplete_by_h.items()) + '. Events used per subset and horizon (all '
  'stances; per-stance counts are in `results.json` meta.n_by_subset_stance_h and the n column of each win-rate row):')
A('')
A('   | subset | ' + ' | '.join(f'h={h}' for h in HS) + ' |')
A('   |---|' + '---|' * len(HS))
for s_ in SUBSETS:
    A(f'   | {s_} | ' + ' | '.join(str(n_by_subset_h[s_][str(h)]) for h in HS) + ' |')
A('')
A('   | subset | stance | ' + ' | '.join(f'h={h}' for h in HS) + ' |')
A('   |---|---|' + '---|' * len(HS))
for s_ in SUBSETS:
    for st in ['S+', 'R-demand', 'R-supply', 'S0']:
        A(f'   | {s_} | {st} | ' + ' | '.join(str(n_by_subset_stance_h[s_][st][str(h)]) for h in HS) + ' |')
A('')
pm_ = checks['placebo_machinery']
A(f'5. **Placebo machinery (additional).** 200 random placebo-1 (draw, event) BHARs recomputed by the slow '
  f'per-event path: max relative difference {pm_["placebo1_recompute_200_max_rel_diff"]:.1e} (float32 storage). The '
  f'date-shift code path run with a zero shift reproduces every actual BHAR (max abs diff '
  f'{pm_["shift0_reproduces_actual_max_abs_diff"]:.1e}, same missing pattern: {pm_["shift0_same_missing_pattern"]}). '
  f'Share of (document, shift) pairs whose shifted entry month equals t0 + shift: '
  f'{pm_["share_doc_shifts_with_entry_eq_t0_plus_shift"]:.3f} (the rest are dates near month-end, where the shifted '
  f'date can fall after that month\'s last trading day) — {"PASS" if pm_["pass"] else "FAIL"}.')
A('')
A(f'Other measures: pre_12 available for {int((~np.isnan(pre12)).sum())} events, pre_3 {int((~np.isnan(pre3)).sum())}; '
  f'CAR[0,1]/[0,5]/[0,20] {int((~np.isnan(car[1])).sum())}/{int((~np.isnan(car[5])).sum())}/'
  f'{int((~np.isnan(car[20])).sum())}; turnover pre/post 1–12/post 25–36 {int((~np.isnan(tsh_pre)).sum())}/'
  f'{int((~np.isnan(tsh_p1)).sum())}/{int((~np.isnan(tsh_p25)).sum())}.')
A('')
A('## Deviations')
A('')
A('All items below were decided from the plan text before any outcome was computed and applied uniformly. None changes '
  'a hypothesis, win rule, horizon or test.')
A('')
over = [p for p in pool_info if p['over_capacity']]
_over_list = ', '.join(f'{p["doc_id"]} {p["level"]} {p["codes_needed"]}/{p["pool"]}' for p in over)
for j, (title, txt) in enumerate(DEVIATIONS, 1):
    A(f'{j}. **{title}.** ' + txt.replace('{N_OVER}', str(len(over))).replace('{OVER_LIST}', _over_list))
A(f'{len(DEVIATIONS) + 1}. **Occurrence note (portfolio cash months).** The P1/P2 cash rule in item 12 was triggered: '
  f'P2 held no series in {PF["P2"]["months_empty"]} months ({_p2_empty_txt}, no S+ event active in its 36-month '
  f'window); those months earn 0 and P3 is 0 there (C12). P1 had {PF["P1"]["months_empty"]} such months.')
_dd = TE.groupby('event_date').doc_id.nunique()
_shared = [(d_, sorted(set(TE.doc_id[TE.event_date == d_]))) for d_ in _dd[_dd > 1].index]
A(f'{len(DEVIATIONS) + 2}. **Plan section 5 vs C10.** The plan text says "resample event dates"; C10 sets the cluster '
  f'to doc_id. C10 was applied. Tested documents: {len(DOCS_T)}; distinct event dates: {TE.event_date.nunique()}'
  + ('; documents sharing a date: ' + '; '.join(f'{"/".join(ds)} ({d_})' for d_, ds in _shared) if _shared else '')
  + '. Placebo 2 shifts each document independently (C9).')
A(f'{len(DEVIATIONS) + 3}. **Plan section 7 vs C12 for P1.** The plan says active "60 months after the proposal '
  'date"; C12 says through December of the plan\'s last year. C12 was applied.')
A('')
A('## Limitations')
A('')
A('- **Few independent clusters.** The primary test rests on 5 documents (P10-A1…P14-A1), FYP subsets on 10–11, and '
  'each plan-level subgroup on 2. Percentile bootstrap intervals with this few clusters are too narrow and unstable; '
  'the placebo distributions are the more informative comparison for the FYP rows.')
A('- **Overlap and dependence.** Events of one document share a date and often the same industry series (e.g. many '
  'P13-A1 events map to the same L1 index); 36-month windows of successive documents overlap. Event counts overstate '
  'the effective sample size.')
A(f'- **Placebo 1 construction.** In {len(over)} (document, level) groups the pool was too small for draws without '
  'replacement (Deviation 2). Even where feasible, C8 gives a document\'s events distinct industries although the '
  'actual events repeat industries, so the registered null may be narrower than the true chance variation; the '
  'exploratory relabel variant (section 11) shows how much this matters.')
A('- **Heavy-tailed BHAR.** BHAR is a difference of gross growth factors, so windows covering strong markets '
  '(2006–2007, 2014–2015) produce very large magnitudes; means can be dominated by one document. Medians and win '
  'rates are less affected.')
A(f'- **Index availability.** Only current SW2021 indices exist (no predecessor series). Many L1 indices start 2014-02 '
  f'and many L2 indices 2021-12, so {excl.get("no_series_at_entry", 0)} events had no series at entry and early events '
  'are measured on the subset of industries with long histories (often at L1 rather than L2).')
A('- **Price indices.** Both industry and benchmark exclude dividends; differences in dividend yield across industries '
  'are not captured.')
A('- **Data quality.** 801193 证券Ⅱ and 801951 煤炭开采 have long gaps (handled by C14); 14 monthly bars are dated '
  'before month-end (none inside any tested event window); 801003 lacks 18 daily dates that some series have '
  '(Deviation 6). The 2026-10 bar is partial (P15-A1 12-month horizon and the last portfolio month).')
A('- **Document selection.** The `other` documents were chosen by people who know later market history (C1); those '
  'results are exploratory. No document has doc_type GWR_first, so that C13 subset is empty.')
A('- **Many comparisons.** The tables contain many rows (subsets × rules × horizons × subgroups). Only the primary '
  'test is confirmatory; a small p-value elsewhere is expected by chance and is exploratory.')
A('- **One-sided tests.** The registered p-values only test the rule\'s direction. Results in the opposite direction '
  '(e.g. S+ underperformance at 1–12 months, where the one-sided p is 1.000) have no registered test and are '
  'exploratory observations.')
A('')
A(f'Seeds: {json.dumps(SEEDS)}. Bootstrap {N_BOOT:,} draws; placebos {N_PLAC:,} draws each. {results["meta"]["runtime_note"]}.')
with open(os.path.join(OUT, 'report.md'), 'w') as f_:
    f_.write('\n'.join(L) + '\n')
print('report written', time.time() - T_START)
