# Pre-registered analysis plan v1 — "If you buy what the policy wording favours, how often do you win?"

Frozen: 2026-10-26, before the event table exists and before any event is joined to prices.
Executor: an independent backtest agent that did not write the event table and did not write this narrative.

## 1. Inputs
- `events_v1.csv` (frozen by sha256 in `events/FROZEN.sha256`). The backtest agent must not edit, add, drop or
  re-code events. Any exclusion happens only through the mechanical rules below and is counted in the report.
- SW index data (申万宏源研究 public data): monthly OHLC + turnover; daily closes. Current SW2021 L1/L2 codes plus
  predecessor (discontinued) codes with a lineage table.
- Benchmarks: primary 申万A指 (801003); secondary = equal-weight average monthly return of all SW L1 indices
  available that month.

## 2. Event → return series
1. Use the event's `sw_l2` codes if the series exists at the entry date; otherwise its `sw_l1`; otherwise the
   predecessor series given in the lineage table. Several codes → equal-weight average of their monthly returns.
2. `sw_l1 = none` and `sw_l2 = none` → excluded (counted).
3. Entry = close of the first month-end strictly after `event_date` (a policy published on the 30th enters at the
   next month-end). Returns are price-index returns (SW indices exclude dividends; so does the benchmark).

## 3. Measures
- Buy-and-hold abnormal return BHAR(h) = Π(1+r_ind) − Π(1+r_bench) over h = 1, 3, 6, 12, 24, 36 months after entry.
- Pre-event drift: BHAR over the 12 and 3 months before entry (anticipation, leaks, drafting news).
- Turnover share: industry monthly turnover ÷ 申万A指 turnover, average over months [−12,−1] vs [+1,+12] and
  [+25,+36] (attention / capital inflow).
- Short-window reaction (daily data): cumulative abnormal return, days [0,+1], [0,+5], [0,+20] from the first
  trading day on/after `event_date`, abnormal = index − 申万A指.
- Horizons that run past the last available month are reported as "incomplete" and excluded from that horizon's
  statistics (counts reported).

## 4. Win definitions (fixed in advance)
- `S+` (support/expansion): win if BHAR(h) > 0.
- `R-demand` (demand/regulatory restriction): a policy follower avoids or underweights → win if BHAR(h) < 0.
- `R-supply` (supply restriction): two competing hypotheses reported side by side — H-a "avoid": win if BHAR < 0;
  H-b "incumbents gain": win if BHAR > 0. Neither is declared primary.
- `S0`: no directional bet; reported descriptively.
Primary horizon: 36 months ("three years after the policy turn"). Secondary: 12 months.

## 5. Inference
- Events sharing a date are not independent. Use a date-clustered bootstrap (resample event dates with replacement,
  10,000 draws) for confidence intervals of win rate and mean/median BHAR.
- Placebo 1 (industry permutation): for each event date keep the number of events, replace the industries with a
  random draw (without replacement) from SW indices available at that date at the same level; 2,000 draws →
  null distribution of the win rate and mean BHAR.
- Placebo 2 (date shift): shift each document's date by a random ±6–24 months (same industries), 2,000 draws.
- Report p-values against both placebos. Do not report a significance claim from any test not listed here
  without labelling it exploratory.

## 6. Subgroups (all reported, no selection)
By plan (十五…十五五), doc_type (FYP_proposal / FYP_outline / other / GWR_first), stance, intensity,
change_vs_prev (new / up / same / down / dropped), pivot = 1, decade (2000s / 2010s / 2020s).

## 7. Portfolio (calendar-time) tests
- P1 "follow the plan": each month hold, equal-weighted, every industry with an active `S+` FYP signal
  (active = from entry to 60 months after the plan's proposal date, i.e. through the plan period).
- P2 "follow all S+": same with all `S+` rows, active for 36 months after entry.
- P3 "long S+ / short R-demand": equal-weighted long leg minus short leg, 36-month activity.
- For each: annualised return and excess return vs 申万A指, volatility, information ratio, max drawdown,
  share of months beating the benchmark, and rolling 36-month excess return.

## 8. Event-time paths
Average cumulative abnormal return paths from month −12 to +36 by stance, and for `pivot = 1` events.

## 9. Output
`/home/claude/policy_bt/backtest/`: `results.json` (every number above), `event_level.csv` (one row per event with
all horizons), `portfolio_monthly.csv`, `report.md` (plain-language findings, deviations log, limitations), and the
code used (`backtest.py`). Any deviation from this plan must be logged in `report.md` under "Deviations".
