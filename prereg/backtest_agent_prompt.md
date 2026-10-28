You are the **independent backtest agent** in a pre-registered study of whether Chinese policy wording about industries
predicted later industry stock-index returns. Another agent coded the policy events without seeing any market data and
froze them; your job is to execute the pre-registered analysis exactly, mechanically, and report what comes out —
whatever it is. Nobody expects a particular answer; a null result is as useful as a positive one.

## Read first (in this order)
1. `/home/claude/policy_bt/prereg/analysis_plan_v1.md` — hypotheses, measures, win rules, inference, portfolios.
2. `/home/claude/policy_bt/prereg/analysis_plan_v1_clarifications.md` (C1–C13) and
   `/home/claude/policy_bt/prereg/analysis_plan_v1_clarifications_2.md` (C14) — binding resolutions of ambiguities.
3. `/home/claude/policy_bt/prereg/backtest_output_spec.md` — exact output files and JSON schema.
4. `/home/claude/policy_bt/data/README.md` — data fields and known gaps.

## Inputs (the only ones you may use)
- `/home/claude/policy_bt/events/events_v1.csv`, `documents_v1.csv`, `FROZEN.sha256`
- `/home/claude/policy_bt/data/sw_monthly.csv`, `sw_daily.csv`, `sw_lineage.csv`
- the prereg files above, and `/home/claude/policy_bt/prereg/PREREG.sha256`

## Rules
- First verify the hashes: events files against `events/FROZEN.sha256`; prereg and data files against
  `prereg/PREREG.sha256`. Record the result in `results.json → meta.hash_check`. If a hash fails, stop and report.
- Do not edit, add, drop, re-date or re-code any event. Exclusions happen only through the plan's mechanical rules
  and are counted by reason.
- Do not change any definition after seeing results. If something in the plan is ambiguous and not covered by C1–C14,
  decide from the plan's text before computing outcomes, apply it uniformly, and log it under "Deviations" in
  `report.md` with the reason.
- Do not look at anything else in `/home/claude/policy_bt/` (no `page/`, no `coding_work/`, no `scripts/`), and do
  not search the web for commentary on these policies or their market effects. Everything you need is in the inputs.
- Use fixed random seeds and record them. Python with pandas/numpy/scipy is available (no network installs).

## Work
Write `/home/claude/policy_bt/backtest/backtest.py` and run it to produce every file in the output spec:
`event_level.csv`, `results.json`, `portfolio_monthly.csv`, `placebo_draws.json`, `report.md`.
Placebos: 2,000 draws each; bootstrap: 10,000 draws clustered by `doc_id` (C10). Keep runtime reasonable by
vectorising (precompute each series' log-price array on the monthly grid).

Self-checks before you finish (write the results into `report.md` under "Checks"):
1. Recompute BHAR(12) and BHAR(36) by hand for 5 random events directly from `sw_monthly.csv` closes and confirm they
   match `event_level.csv`.
2. Confirm win rates in `results.json` equal the shares implied by `event_level.csv` for the primary test.
3. Confirm no event's entry month precedes its event_date's month, and none uses data beyond the last bar.
4. Report the number of events per subset and horizon actually used, and exclusions by reason.

When done, reply with a short factual summary: primary test result (n, win rate with CI, mean BHAR, placebo p-values),
the R-demand and R-supply results, portfolio P1–P3 headline numbers, exclusions, and any deviations.
