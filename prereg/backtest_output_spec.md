# Backtest output specification

All files go to `/home/claude/policy_bt/backtest/`. Numbers are decimals (0.123 = 12.3%), not percent.

## event_level.csv — one row per event in events_v1.csv (excluded events included, with a reason)
`event_id, doc_id, doc_type, stance, event_date, entry_month (YYYY-MM), series_used, level_used, excluded_reason,
bhar_1, bhar_3, bhar_6, bhar_12, bhar_24, bhar_36, pre_12, pre_3, car_d1, car_d5, car_d20,
tshare_pre, tshare_post_1_12, tshare_post_25_36, win_12, win_36, ends_on_partial_month`
- `win_12`, `win_36`: 1/0 under the stance's win rule (S+ win if BHAR > 0; R-demand win if BHAR < 0;
  R-supply: write the H-a result, i.e. win if BHAR < 0; S0: empty). Empty when the horizon is incomplete.

## results.json
```
{
 "meta": {"n_events": int, "n_tested": int, "excluded": {"reason": count, ...},
          "first_entry": "YYYY-MM", "last_bar": "YYYY-MM-DD", "hash_check": {"events": bool, "prereg": bool},
          "seeds": {...}, "runtime_note": str},
 "win_rates": [  // one row per (subset, rule, h); subsets per C13; rules: "S+", "R-demand", "R-supply H-a", "R-supply H-b"
   {"subset": str, "rule": str, "h": int, "n": int, "n_docs": int, "win_rate": float, "ci_lo": float, "ci_hi": float,
    "mean_bhar": float, "mean_ci_lo": float, "mean_ci_hi": float, "median_bhar": float,
    "perm_win_median": float, "perm_win_p05": float, "perm_win_p95": float, "p_perm_win": float,
    "perm_mean_median": float, "perm_mean_p05": float, "perm_mean_p95": float, "p_perm_mean": float,
    "shift_win_median": float, "shift_win_p05": float, "shift_win_p95": float, "p_shift_win": float,
    "shift_mean_median": float, "shift_mean_p05": float, "shift_mean_p95": float, "p_shift_mean": float}
 ],
 "subgroups": [  // dims: plan, doc_type, stance, intensity, change_vs_prev, pivot, decade; each for h = 12 and 36
   {"dim": str, "value": str, "rule": str, "h": int, "n": int, "win_rate": float, "mean_bhar": float,
    "median_bhar": float, "ci_lo": float, "ci_hi": float}
 ],
 "car_paths": {  // event-time average cumulative abnormal return, k = -12..36 relative to entry (k=0 → 0)
   "<group>": {"k": [...], "mean": [...], "lo": [...], "hi": [...], "n": [...]}
   // groups: "S+ FYP_proposal", "S+ all", "R-demand all", "R-supply all", "S0 all", "pivot all"
 },
 "short_window": [{"group": str, "k": 1|5|20, "n": int, "mean_car": float, "ci_lo": float, "ci_hi": float,
                   "pos_rate": float}],
 "turnover": [{"group": str, "n": int, "share_pre": float, "share_post_1_12": float, "share_post_25_36": float,
               "change_pp_1_12": float, "ci_lo": float, "ci_hi": float}],
 "portfolios": {"P1"|"P2"|"P3": {"start": "YYYY-MM", "end": "YYYY-MM", "months": int, "ann_return": float,
               "ann_bench": float, "ann_excess": float, "vol_excess": float, "info_ratio": float,
               "max_drawdown_excess": float, "hit_rate": float, "avg_holdings": float}}
}
```
p-values are one-sided in the direction of the rule (share of placebo draws at least as favourable as actual).

## portfolio_monthly.csv
`month, bench_ret, P1_ret, P1_n, P2_ret, P2_n, P3_ret, P3_long_n, P3_short_n`

## placebo_draws.json
`{"<subset>|<rule>|<h>": {"perm_win": [...2000], "shift_win": [...2000], "actual_win": float}}` for subsets
FYP_proposal and all, rules S+ and R-demand, h = 12 and 36.

## report.md
Plain-language summary of every result above, a "Deviations" section (empty if none), and limitations.
Keep it factual: no claims beyond the tests listed in the plan without the label "exploratory".
