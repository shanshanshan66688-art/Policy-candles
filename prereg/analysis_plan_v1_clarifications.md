# Clarifications to analysis plan v1 (written before any event is joined to prices)

Written: 2026-10-26, while the event table was still being coded and before any price data was joined to any
event. These resolve ambiguities in `analysis_plan_v1.md`; they do not change its hypotheses, win definitions or
tests. The backtest agent applies them as written.

C1. Primary test. The primary test is `doc_type = FYP_proposal`, `stance = S+`, horizon 36 months (the complete
    five-year-plan universe). Everything else is secondary or exploratory. The seed list of other documents was chosen
    by people who know later market history, so results on `doc_type = other` are exploratory and must be labelled so.

C2. Series selection. Take the subset of the event's `sw_l2` codes whose series has a close at the entry month. If
    that subset is non-empty, the event's return is the equal-weighted average of those series' monthly returns
    (rebalanced monthly). Otherwise apply the same rule to `sw_l1`. Otherwise exclude with reason `no_series_at_entry`.
    `none` codes are skipped. No predecessor (discontinued) series are available, so the lineage table is empty.
    Record `series_used` (codes joined by `;`) and `level_used` (L2 / L1) per event.

C3. Entry month. Monthly bars are dated by each month's last trading day. Entry month t0 = the first month whose bar
    date is strictly after `event_date`. The last bar (2026-10, dated 2026-10-23) is a partial month; it counts as the
    latest available close and any horizon that ends on it is flagged `ends_on_partial_month`.

C4. Horizons. BHAR(h) = close-to-close compounding from the t0 close to the t0+h close for the industry series minus
    the same for 申万A指 (801003). A horizon is "incomplete" when t0+h is later than the last bar; incomplete horizons
    are excluded from that horizon's statistics and counted.

C5. Pre-event drift. BHAR from the t0−12 close to the t0 close, and from the t0−3 close to the t0 close. Missing if the
    series has no close at t0−12 (or t0−3).

C6. Turnover share. Monthly turnover of the series (sum over codes for multi-code events) divided by 801003's
    turnover. Windows: months t0−12…t0−1, t0+1…t0+12, t0+25…t0+36 (averages of monthly shares). Report the change in
    percentage points and the ratio after/before.

C7. Daily reaction. Day 0 = first trading day on or after `event_date`. Daily abnormal return = industry close-to-close
    return − 801003 close-to-close return. CAR[0,k] = sum of daily abnormal returns over days 0…k, k = 1, 5, 20.
    Multi-code events use the equal-weighted average daily return of the codes available on day 0.

C8. Placebo 1 (industry permutation). For each event, draw replacement series at the same level as `level_used`,
    from series that have a close at the event's entry month, as many codes as the event used; within one document,
    draw without replacement so a document's events get distinct replacement industries. 2,000 draws.

C9. Placebo 2 (date shift). Shift each document's date by a random whole number of months, magnitude uniform on
    6…24, sign random; all events of a document share the shift. Recompute entry and outcomes; events that lose data
    or become incomplete are dropped from that draw. 2,000 draws.

C10. Bootstrap. Cluster = `doc_id`. Resample documents with replacement, 10,000 draws, percentile 95% intervals.

C11. Ties. BHAR exactly 0 counts as a loss for every win definition.

C12. Portfolios. Holdings for month m are decided from information at the end of month m−1: an event with entry
    month t0 is first held in month t0+1. Each industry series appears once per leg per month however many events
    point to it.
    - P1: `S+` rows with doc_type FYP_proposal or FYP_outline; held from t0+1 through the end of the plan's last year
      (e.g. 十二五 → December 2015).
    - P2: all `S+` rows; held months t0+1…t0+36.
    - P3: long leg = P2 holdings; short leg = `R-demand` rows held t0+1…t0+36; return = mean(long) − mean(short).
      A month with an empty leg has P3 return 0.
    Excess return = portfolio return − 801003 return. P3 is reported as a long-short return (no benchmark subtraction).

C13. Subsets reported for the main win-rate table: FYP_proposal (primary), FYP (proposal + outline), other,
    GWR_first, all.
