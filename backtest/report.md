# Backtest report — policy wording vs. SW industry index returns (analysis plan v1)

Executed by the independent backtest agent with `backtest/backtest.py` (Python 3.13.17, numpy 2.5.3, pandas 3.0.5). Numbers are decimals (0.123 = 12.3%) unless shown with a % sign. Every figure here is also in `results.json`; per-event values are in `event_level.csv`.

## 1. Inputs and what was tested

- **Hash check:** events files match `events/FROZEN.sha256`; all 11 prereg and data files listed in `prereg/PREREG.sha256` match. Not checked: scripts/merge_events.py (outside the inputs this agent may open).
- **Events:** 2234 events from 64 documents. Tested: 1607 events from 62 documents (971 on L2 series, 636 on L1). Excluded: no_series_at_entry = 335, no_sw_code = 292. No event was edited, added, dropped or re-dated; data_gap (C14) removed no event (0 events lost one of several series to the gap rule and kept the rest at the same level; 6 events had L2 series at entry that all failed the gap rule and fell back to L1 under C14: E1048 [L2 801951, entry 2015-11], E1111 [L2 801951, entry 2016-02], E1112 [L2 801951, entry 2016-02], E1149 [L2 801951, entry 2016-03], E1190 [L2 801951, entry 2016-03], E1243 [L2 801951, entry 2016-12]).
- **Timing:** entry = close of the first month-end (801003 bar date) strictly after the event date; first entry 2000-08; last bar 2026-10-23 (2026-10 is a partial month). Incomplete horizons (excluded from that horizon): h=1: 0, h=3: 0, h=6: 0, h=12: 111, h=24: 297, h=36: 393. 139 events have their 12-month horizon ending on the partial month (P15-A1 (139 of 139 tested events)); other horizons ending there: h=1: 0, h=3: 0, h=6: 0, h=24: 0, h=36: 0.
- **Measure:** BHAR(h) = compounded industry return minus compounded 申万A指 (801003) return from the entry close to the close h months later; multi-code events use an equal-weight, monthly-rebalanced average. Price indices on both sides.
- **Win rules (plan section 4, C11):** S+ wins if BHAR > 0; R-demand wins if BHAR < 0; R-supply is shown under H-a (win if BHAR < 0) and H-b (win if BHAR > 0); ties lose; S0 is descriptive.
- **Inference:** doc-clustered bootstrap (C10, 10,000 draws, percentile 95% CI); placebo 1 = random industries at the same dates (C8, 2,000 draws); placebo 2 = each document shifted by ±6–24 months (C9, 2,000 draws). p-values are one-sided in the direction of the rule (share of placebo draws at least as favourable as the actual result).
- **Primary test (C1):** doc_type = FYP_proposal, stance = S+, h = 36. Everything else is secondary; results on doc_type = other are **exploratory** (C1).

## 2. Plain-language findings

**Primary test.** 279 S+ events from the 5 five-year-plan proposals with a complete 36-month window (P10-A1, P11-A1, P12-A1, P13-A1, P14-A1; the 十五五 proposal P15-A1 is too recent). Of these, 124 beat 申万A指 over 36 months: win rate 44.4% (95% CI 32.6%–55.9%). Mean BHAR(36) -0.010 (CI [-0.045, 0.023]), median -0.028. Random industries on the same dates (placebo 1) give a median win rate of 45.5% (5–95%: 42.3%–48.7%); p = 0.707 for the win rate and 0.927 for the mean. The same industries at shifted dates (placebo 2) give a median win rate of 44.1%; p = 0.486 (win rate) and 0.653 (mean). None of the four placebo p-values is below 0.05 and the win-rate CI includes 50%: the primary test does not show that buying the industries favoured in FYP-proposal wording beat the market over the following three years.

**Secondary horizon (12 months).** S+ FYP-proposal events (n = 371, 6 documents incl. P15-A1) won 34.2% of the time (CI 28.3%–39.7%), mean BHAR(12) -0.039 (CI [-0.057, -0.019]). One-sided p-values in the rule's direction: placebo 1 1.000 / 1.000, placebo 2 0.971 / 0.950 (win rate / mean). The actual win rate lies below the industry-permutation distribution (5–95%: 42.9%–48.8%), i.e. the favoured industries tended to lag the market over the first year. The plan registers only tests in the direction of the rule, so this underperformance is an **exploratory** observation, not a registered finding. One-sided p (perm win) for FYP_proposal S+ at h = 1/3/6: 1.000/1.000/1.000; for all S+ events at h = 12: 1.000 (section 4).

**R-demand (all, exploratory for the other-document part).** 36 months: n = 73 (22 docs), win rate (BHAR < 0) 52.1% (CI 31.4%–66.3%), mean BHAR 0.058 (CI [-0.013, 0.162]), median -0.010; p (perm win/mean) 0.457/0.644, p (shift win/mean) 0.618/0.469. 12 months: n = 84, win rate 46.4%, mean BHAR 0.041, p (perm win) 0.924, p (shift win) 0.779. Restricted-demand industries did not, on average, underperform: the mean BHAR at 36 months is positive.

**R-demand (FYP_proposal).** 36 months: n = 19 (4 docs), win rate (BHAR < 0) 31.6% (CI 12.5%–40.0%), mean BHAR 0.116 (CI [0.055, 0.290]), median 0.110; p (perm win/mean) 0.957/0.895, p (shift win/mean) 0.875/0.310. 12 months: n = 24, win rate 41.7%, mean BHAR 0.081, p (perm win) 0.968, p (shift win) 0.802. Restricted-demand industries did not, on average, underperform: the mean BHAR at 36 months is positive.

**R-supply (all documents; neither hypothesis primary).** 36 months, n = 71 (23 docs), mean BHAR 0.025, median 0.074. H-a "avoid" win rate 45.1% (CI 31.4%–58.0%; p perm/shift 0.522/0.895); H-b "incumbents gain" win rate 54.9% (CI 41.9%–68.7%; p perm/shift 0.581/0.121). 12 months: H-a 45.9%, H-b 54.1% (n = 74); p (perm mean, H-a) at 12 months = 0.013 (one of many secondary rows; exploratory weight). Neither hypothesis has a win-rate CI that excludes 50% at the primary horizon.

**Other rows with a placebo p ≤ 0.05 (all exploratory/secondary; 16 of 95 non-empty non-primary rows, each with 4 p-values).** FYP_proposal R-supply H-a h=6 (n=9, win 0.889, mean -0.064; p_shift_win 0.004); FYP_proposal R-supply H-a h=12 (n=9, win 0.778, mean -0.033; p_shift_win 0.049); FYP_proposal R-supply H-b h=36 (n=8, win 0.625, mean 0.028; p_shift_mean 0.028); FYP R-demand h=1 (n=68, win 0.632, mean -0.015; p_shift_mean 0.042); FYP R-demand h=3 (n=68, win 0.662, mean -0.057; p_perm_mean 0.017, p_shift_win 0.030, p_shift_mean 0.000); FYP R-supply H-b h=1 (n=19, win 0.526, mean 0.025; p_perm_mean 0.026); FYP R-supply H-b h=24 (n=18, win 0.667, mean 0.053; p_shift_win 0.009); FYP R-supply H-b h=36 (n=18, win 0.556, mean -0.035; p_shift_win 0.046); other R-demand h=1 (n=26, win 0.692, mean -0.022; p_perm_mean 0.016, p_shift_mean 0.018); other R-supply H-a h=12 (n=55, win 0.436, mean 0.019; p_perm_mean 0.006); other R-supply H-b h=24 (n=54, win 0.704, mean 0.156; p_shift_win 0.004); all R-demand h=1 (n=94, win 0.649, mean -0.017; p_perm_mean 0.037, p_shift_win 0.023, p_shift_mean 0.006); all R-demand h=3 (n=94, win 0.564, mean -0.032; p_shift_mean 0.001); all R-supply H-a h=6 (n=74, win 0.486, mean 0.007; p_perm_mean 0.035); all R-supply H-a h=12 (n=74, win 0.459, mean 0.015; p_perm_mean 0.013); all R-supply H-b h=24 (n=72, win 0.694, mean 0.130; p_shift_win 0.001).

**Portfolios (calendar time, 申万A指 benchmark).** P1 "follow the plan" (2000-11–2026-10, 312 months, avg 44.3 series): annualised return 5.2% vs benchmark 4.0%; annualised excess (12 x mean monthly) 1.3%, tracking volatility 7.0%, information ratio 0.19, max drawdown of excess -23.4%, beats the benchmark in 50.6% of months. P2 "all S+" (2000-09–2026-10): 7.4% vs 3.9%, excess 3.5%, IR 0.36, max DD -23.0%, hit rate 54.8% (P2 was empty and held cash at 0 in 19 months, 2004-04…2005-10). P3 "long S+ / short R-demand" (2000-09–2026-10): long-short annualised -4.3%, mean -3.6% a year, volatility 12.1%, IR -0.30, max DD -75.8%, positive in 37.9% of months (48 months had an empty leg and count as 0). The portfolio tests have no registered significance test; the numbers are descriptive.

**Before and around the event.** Pre-entry drift (BHAR over the 12 months up to entry) for S+ FYP-proposal events: mean 0.019 (CI [-0.048, 0.107]); all S+: 0.047. Daily reaction CAR[0,+5] for all S+ events: 0.0038 (CI [-0.0004, 0.0083]); S+ FYP proposals: 0.0005. Turnover share after S+ FYP proposals changed by -0.0038 (share units; ×100 = percentage points; CI [-0.0047, -0.0029]) from months −12…−1 to +1…+12, i.e. the favoured industries' share of market turnover fell slightly rather than rose. Short-window, drift and turnover results carry no registered test; they are descriptive (doc-clustered CIs).

## 3. Main win-rate table (C13 subsets; h = 36 primary, h = 12 secondary)

`other` rows are exploratory (C1). GWR_first: no event in the table has this doc_type, so the subset is empty. p-values: one-sided, placebo draws at least as favourable as actual.

| subset | rule | h | n (docs) | win rate [95% CI] | mean BHAR [95% CI] | median | perm win: median [5–95%] | p perm win | p perm mean | shift win: median [5–95%] | p shift win | p shift mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FYP_proposal | S+ | 36 | 279 (5) | 0.444 [0.326, 0.559] | -0.010 [-0.045, 0.023] | -0.028 | 0.455 [0.423, 0.487] | 0.707 | 0.927 | 0.441 [0.376, 0.547] | 0.486 | 0.653 |
| FYP_proposal | R-demand | 36 | 19 (4) | 0.316 [0.125, 0.400] | 0.116 [0.055, 0.290] | 0.110 | 0.474 [0.316, 0.684] | 0.957 | 0.895 | 0.421 [0.263, 0.632] | 0.875 | 0.310 |
| FYP_proposal | R-supply H-a | 36 | 8 (3) | 0.375 [0.000, 0.600] | 0.028 [-0.044, 0.150] | 0.104 | 0.625 [0.250, 0.875] | 0.948 | 0.635 | 0.625 [0.375, 0.857] | 0.990 | 0.973 |
| FYP_proposal | R-supply H-b | 36 | 8 (3) | 0.625 [0.400, 1.000] | 0.028 [-0.044, 0.150] | 0.104 | 0.375 [0.125, 0.750] | 0.191 | 0.364 | 0.375 [0.143, 0.625] | 0.057 | 0.028 |
| FYP | S+ | 36 | 581 (10) | 0.468 [0.385, 0.551] | 0.037 [-0.021, 0.131] | -0.014 | 0.458 [0.437, 0.480] | 0.258 | 0.142 | 0.460 [0.408, 0.525] | 0.418 | 0.534 |
| FYP | R-demand | 36 | 53 (9) | 0.528 [0.226, 0.690] | 0.055 [-0.021, 0.199] | -0.010 | 0.509 [0.396, 0.604] | 0.392 | 0.617 | 0.509 [0.396, 0.635] | 0.430 | 0.320 |
| FYP | R-supply H-a | 36 | 18 (7) | 0.444 [0.182, 0.593] | -0.035 [-0.110, 0.080] | 0.057 | 0.556 [0.389, 0.722] | 0.910 | 0.278 | 0.611 [0.471, 0.824] | 0.979 | 0.537 |
| FYP | R-supply H-b | 36 | 18 (7) | 0.556 [0.407, 0.818] | -0.035 [-0.110, 0.083] | 0.057 | 0.444 [0.278, 0.611] | 0.214 | 0.723 | 0.389 [0.176, 0.529] | 0.046 | 0.463 |
| other (expl.) | S+ | 36 | 260 (34) | 0.500 [0.385, 0.627] | 0.018 [-0.058, 0.100] | -0.001 | 0.510 [0.465, 0.554] | 0.668 | 0.949 | 0.523 [0.433, 0.609] | 0.673 | 0.977 |
| other (expl.) | R-demand | 36 | 20 (13) | 0.500 [0.267, 0.737] | 0.068 [-0.086, 0.227] | 0.018 | 0.500 [0.350, 0.700] | 0.663 | 0.646 | 0.600 [0.421, 0.789] | 0.865 | 0.805 |
| other (expl.) | R-supply H-a | 36 | 53 (16) | 0.453 [0.288, 0.623] | 0.046 [-0.050, 0.155] | 0.089 | 0.396 [0.302, 0.509] | 0.272 | 0.114 | 0.509 [0.358, 0.679] | 0.766 | 0.464 |
| other (expl.) | R-supply H-b | 36 | 53 (16) | 0.547 [0.380, 0.714] | 0.046 [-0.049, 0.153] | 0.089 | 0.604 [0.491, 0.698] | 0.822 | 0.886 | 0.491 [0.321, 0.642] | 0.291 | 0.536 |
| GWR_first | S+ | 36 | 0 | – | – | – | – | – | – | – | – | – |
| GWR_first | R-demand | 36 | 0 | – | – | – | – | – | – | – | – | – |
| GWR_first | R-supply H-a | 36 | 0 | – | – | – | – | – | – | – | – | – |
| GWR_first | R-supply H-b | 36 | 0 | – | – | – | – | – | – | – | – | – |
| all | S+ | 36 | 841 (44) | 0.478 [0.409, 0.548] | 0.031 [-0.019, 0.097] | -0.012 | 0.474 [0.454, 0.493] | 0.408 | 0.609 | 0.480 [0.433, 0.530] | 0.526 | 0.882 |
| all | R-demand | 36 | 73 (22) | 0.521 [0.314, 0.663] | 0.058 [-0.013, 0.162] | -0.010 | 0.507 [0.411, 0.589] | 0.457 | 0.644 | 0.535 [0.438, 0.639] | 0.618 | 0.469 |
| all | R-supply H-a | 36 | 71 (23) | 0.451 [0.314, 0.580] | 0.025 [-0.050, 0.114] | 0.074 | 0.451 [0.366, 0.535] | 0.522 | 0.086 | 0.543 [0.423, 0.671] | 0.895 | 0.426 |
| all | R-supply H-b | 36 | 71 (23) | 0.549 [0.419, 0.687] | 0.025 [-0.050, 0.112] | 0.074 | 0.549 [0.465, 0.634] | 0.581 | 0.913 | 0.457 [0.329, 0.577] | 0.121 | 0.574 |
| FYP_proposal | S+ | 12 | 371 (6) | 0.342 [0.283, 0.397] | -0.039 [-0.057, -0.019] | -0.040 | 0.458 [0.429, 0.488] | 1.000 | 1.000 | 0.452 [0.354, 0.570] | 0.971 | 0.950 |
| FYP_proposal | R-demand | 12 | 24 (5) | 0.417 [0.083, 0.571] | 0.081 [0.029, 0.168] | 0.075 | 0.583 [0.417, 0.708] | 0.968 | 0.942 | 0.500 [0.316, 0.667] | 0.802 | 0.858 |
| FYP_proposal | R-supply H-a | 12 | 9 (4) | 0.778 [0.571, 1.000] | -0.033 [-0.078, -0.013] | -0.026 | 0.556 [0.222, 0.778] | 0.112 | 0.232 | 0.556 [0.333, 0.750] | 0.049 | 0.315 |
| FYP_proposal | R-supply H-b | 12 | 9 (4) | 0.222 [0.000, 0.429] | -0.033 [-0.078, -0.013] | -0.026 | 0.444 [0.222, 0.778] | 0.975 | 0.768 | 0.444 [0.250, 0.667] | 0.971 | 0.685 |
| FYP | S+ | 12 | 673 (11) | 0.373 [0.321, 0.440] | -0.013 [-0.037, 0.022] | -0.035 | 0.473 [0.453, 0.493] | 1.000 | 1.000 | 0.474 [0.395, 0.556] | 0.982 | 0.931 |
| FYP | R-demand | 12 | 58 (10) | 0.500 [0.269, 0.615] | 0.025 [-0.024, 0.105] | -0.002 | 0.534 [0.431, 0.638] | 0.763 | 0.569 | 0.509 [0.377, 0.623] | 0.553 | 0.508 |
| FYP | R-supply H-a | 12 | 19 (8) | 0.526 [0.273, 0.778] | 0.001 [-0.040, 0.043] | -0.008 | 0.526 [0.316, 0.684] | 0.514 | 0.386 | 0.556 [0.389, 0.737] | 0.693 | 0.485 |
| FYP | R-supply H-b | 12 | 19 (8) | 0.474 [0.222, 0.727] | 0.001 [-0.039, 0.042] | -0.008 | 0.474 [0.316, 0.684] | 0.674 | 0.615 | 0.444 [0.263, 0.611] | 0.365 | 0.514 |
| other (expl.) | S+ | 12 | 374 (42) | 0.487 [0.387, 0.589] | 0.006 [-0.033, 0.047] | -0.006 | 0.505 [0.471, 0.543] | 0.826 | 0.985 | 0.473 [0.399, 0.551] | 0.388 | 0.834 |
| other (expl.) | R-demand | 12 | 26 (16) | 0.385 [0.200, 0.609] | 0.079 [0.004, 0.151] | 0.072 | 0.538 [0.385, 0.692] | 0.954 | 0.934 | 0.538 [0.318, 0.720] | 0.876 | 0.896 |
| other (expl.) | R-supply H-a | 12 | 55 (18) | 0.436 [0.283, 0.588] | 0.019 [-0.027, 0.067] | 0.051 | 0.364 [0.273, 0.473] | 0.163 | 0.006 | 0.500 [0.345, 0.655] | 0.755 | 0.256 |
| other (expl.) | R-supply H-b | 12 | 55 (18) | 0.564 [0.408, 0.723] | 0.019 [-0.027, 0.067] | 0.051 | 0.636 [0.527, 0.727] | 0.904 | 0.994 | 0.500 [0.345, 0.655] | 0.267 | 0.744 |
| GWR_first | S+ | 12 | 0 | – | – | – | – | – | – | – | – | – |
| GWR_first | R-demand | 12 | 0 | – | – | – | – | – | – | – | – | – |
| GWR_first | R-supply H-a | 12 | 0 | – | – | – | – | – | – | – | – | – |
| GWR_first | R-supply H-b | 12 | 0 | – | – | – | – | – | – | – | – | – |
| all | S+ | 12 | 1047 (53) | 0.414 [0.363, 0.481] | -0.006 [-0.028, 0.022] | -0.027 | 0.485 [0.467, 0.503] | 1.000 | 1.000 | 0.474 [0.415, 0.533] | 0.953 | 0.957 |
| all | R-demand | 12 | 84 (26) | 0.464 [0.298, 0.575] | 0.041 [-0.003, 0.103] | 0.001 | 0.536 [0.452, 0.619] | 0.924 | 0.804 | 0.513 [0.405, 0.613] | 0.779 | 0.783 |
| all | R-supply H-a | 12 | 74 (26) | 0.459 [0.325, 0.589] | 0.015 [-0.022, 0.052] | 0.033 | 0.405 [0.324, 0.486] | 0.178 | 0.013 | 0.517 [0.392, 0.644] | 0.769 | 0.254 |
| all | R-supply H-b | 12 | 74 (26) | 0.541 [0.407, 0.671] | 0.015 [-0.022, 0.051] | 0.033 | 0.595 [0.514, 0.676] | 0.877 | 0.988 | 0.483 [0.356, 0.608] | 0.239 | 0.747 |

## 4. All horizons (descriptive except h = 36 / 12)

| subset | rule | h | n | win rate [CI] | mean BHAR | median BHAR [CI] | p perm win | p shift win |
|---|---|---|---|---|---|---|---|---|
| FYP_proposal | S+ | 1 | 371 | 0.426 [0.341, 0.508] | 0.003 | -0.006 [-0.020, 0.001] | 1.000 | 0.811 |
| FYP_proposal | S+ | 3 | 371 | 0.337 [0.274, 0.397] | -0.010 | -0.026 [-0.043, -0.015] | 1.000 | 0.980 |
| FYP_proposal | S+ | 6 | 371 | 0.342 [0.282, 0.415] | -0.030 | -0.049 [-0.080, -0.024] | 1.000 | 0.973 |
| FYP_proposal | S+ | 12 | 371 | 0.342 [0.283, 0.397] | -0.039 | -0.040 [-0.095, -0.013] | 1.000 | 0.971 |
| FYP_proposal | S+ | 24 | 279 | 0.391 [0.221, 0.552] | -0.135 | -0.085 [-0.231, 0.019] | 0.919 | 0.941 |
| FYP_proposal | S+ | 36 | 279 | 0.444 [0.326, 0.559] | -0.010 | -0.028 [-0.100, 0.031] | 0.707 | 0.486 |
| FYP | S+ | 1 | 763 | 0.374 [0.300, 0.457] | -0.005 | -0.012 [-0.024, -0.003] | 1.000 | 0.992 |
| FYP | S+ | 3 | 763 | 0.346 [0.260, 0.438] | -0.028 | -0.032 [-0.057, -0.013] | 1.000 | 0.996 |
| FYP | S+ | 6 | 763 | 0.356 [0.284, 0.447] | -0.021 | -0.039 [-0.058, -0.016] | 1.000 | 0.995 |
| FYP | S+ | 12 | 673 | 0.373 [0.321, 0.440] | -0.013 | -0.035 [-0.055, -0.013] | 1.000 | 0.982 |
| FYP | S+ | 24 | 581 | 0.434 [0.313, 0.543] | -0.026 | -0.051 [-0.105, 0.023] | 0.940 | 0.899 |
| FYP | S+ | 36 | 581 | 0.468 [0.385, 0.551] | 0.037 | -0.014 [-0.075, 0.026] | 0.258 | 0.418 |
| all | S+ | 1 | 1137 | 0.377 [0.322, 0.438] | -0.008 | -0.012 [-0.021, -0.004] | 1.000 | 0.998 |
| all | S+ | 3 | 1137 | 0.381 [0.313, 0.455] | -0.022 | -0.024 [-0.043, -0.008] | 1.000 | 0.996 |
| all | S+ | 6 | 1137 | 0.370 [0.314, 0.437] | -0.020 | -0.033 [-0.047, -0.017] | 1.000 | 0.998 |
| all | S+ | 12 | 1047 | 0.414 [0.363, 0.481] | -0.006 | -0.027 [-0.047, -0.007] | 1.000 | 0.953 |
| all | S+ | 24 | 915 | 0.434 [0.350, 0.515] | -0.012 | -0.049 [-0.090, 0.005] | 0.988 | 0.971 |
| all | S+ | 36 | 841 | 0.478 [0.409, 0.548] | 0.031 | -0.012 [-0.064, 0.031] | 0.408 | 0.526 |
| all | R-demand | 1 | 94 | 0.649 [0.507, 0.769] | -0.017 | -0.015 [-0.034, -0.001] | 0.060 | 0.023 |
| all | R-demand | 3 | 94 | 0.564 [0.388, 0.705] | -0.032 | -0.020 [-0.073, 0.035] | 0.731 | 0.246 |
| all | R-demand | 6 | 94 | 0.511 [0.342, 0.651] | 0.019 | -0.002 [-0.054, 0.044] | 0.891 | 0.542 |
| all | R-demand | 12 | 84 | 0.464 [0.298, 0.575] | 0.041 | 0.001 [-0.023, 0.100] | 0.924 | 0.779 |
| all | R-demand | 24 | 78 | 0.487 [0.316, 0.600] | 0.104 | 0.006 [-0.042, 0.126] | 0.861 | 0.688 |
| all | R-demand | 36 | 73 | 0.521 [0.314, 0.663] | 0.058 | -0.010 [-0.036, 0.116] | 0.457 | 0.618 |
| all | R-supply H-a | 1 | 74 | 0.568 [0.404, 0.716] | -0.003 | -0.014 [-0.029, 0.020] | 0.505 | 0.243 |
| all | R-supply H-a | 3 | 74 | 0.500 [0.364, 0.642] | 0.002 | -0.003 [-0.038, 0.033] | 0.368 | 0.501 |
| all | R-supply H-a | 6 | 74 | 0.486 [0.338, 0.648] | 0.007 | 0.007 [-0.048, 0.042] | 0.181 | 0.596 |
| all | R-supply H-a | 12 | 74 | 0.459 [0.325, 0.589] | 0.015 | 0.033 [-0.019, 0.089] | 0.178 | 0.769 |
| all | R-supply H-a | 24 | 72 | 0.306 [0.182, 0.430] | 0.130 | 0.100 [0.059, 0.236] | 0.967 | 1.000 |
| all | R-supply H-a | 36 | 71 | 0.451 [0.314, 0.580] | 0.025 | 0.074 [-0.109, 0.151] | 0.522 | 0.895 |

Note: the FYP_proposal S+ mean at h = 24 (-0.135) is pulled down by P11-A1 (entry 2005-10, window ending at the 2007 market peak, where BHAR as a difference of gross growth reaches −3.7 for industries that lagged a ~5x benchmark rise); the median is -0.085.

## 5. Subgroups (all reported, no selection; secondary/exploratory)

CIs are doc-clustered win-rate intervals; with 2–5 documents per cell (every plan and FYP-only cell) they are not reliable and are shown only for completeness. R-demand h = 12, R-supply and S0 rows (and values with no S+ or R-demand events, e.g. change_vs_prev = dropped) are in `results.json`.

| dim | value | S+ h=36: n (docs) | win [CI] | mean | median | S+ h=12: n | win | mean | R-demand h=36: n | win | mean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| plan | 十五 | 82 (2) | 0.402 [0.381, 0.425] | -0.005 | -0.037 | 82 | 0.500 | -0.002 | 1 | 0.000 | 0.224 |
| plan | 十一五 | 97 (2) | 0.495 [0.349, 0.611] | 0.216 | -0.064 | 97 | 0.361 | 0.045 | 7 | 0.286 | 0.264 |
| plan | 十二五 | 86 (2) | 0.616 [0.568, 0.667] | 0.070 | 0.042 | 86 | 0.535 | 0.005 | 5 | 0.000 | 0.130 |
| plan | 十三五 | 147 (2) | 0.299 [0.296, 0.303] | -0.053 | -0.084 | 147 | 0.272 | -0.041 | 12 | 0.750 | 0.100 |
| plan | 十四五 | 169 (2) | 0.556 [0.522, 0.595] | 0.017 | 0.010 | 169 | 0.325 | -0.026 | 28 | 0.607 | -0.036 |
| plan | 十五五 | – | – | – | – | 92 | 0.370 | -0.029 | – | – | – |
| plan | other | 260 (34) | 0.500 [0.386, 0.625] | 0.018 | -0.001 | 374 | 0.487 | 0.006 | 20 | 0.500 | 0.068 |
| doc_type | FYP_proposal | 279 (5) | 0.444 [0.326, 0.559] | -0.010 | -0.028 | 371 | 0.342 | -0.039 | 19 | 0.316 | 0.116 |
| doc_type | FYP_outline | 302 (5) | 0.490 [0.370, 0.599] | 0.080 | -0.008 | 302 | 0.411 | 0.020 | 34 | 0.647 | 0.021 |
| doc_type | other | 260 (34) | 0.500 [0.388, 0.624] | 0.018 | -0.001 | 374 | 0.487 | 0.006 | 20 | 0.500 | 0.068 |
| stance | S+ | 841 (44) | 0.478 [0.408, 0.548] | 0.031 | -0.012 | 1047 | 0.414 | -0.006 | – | – | – |
| stance | R-demand | – | – | – | – | – | – | – | 73 | 0.521 | 0.058 |
| intensity | 1 | 84 (21) | 0.321 [0.157, 0.548] | -0.082 | -0.075 | 129 | 0.395 | -0.028 | 8 | 0.125 | 0.107 |
| intensity | 2 | 500 (39) | 0.504 [0.452, 0.565] | 0.062 | 0.002 | 620 | 0.444 | 0.004 | 39 | 0.590 | 0.030 |
| intensity | 3 | 257 (35) | 0.479 [0.366, 0.593] | 0.009 | -0.009 | 298 | 0.359 | -0.017 | 26 | 0.538 | 0.086 |
| change_vs_prev | new | 303 (9) | 0.488 [0.384, 0.596] | 0.069 | -0.008 | 333 | 0.390 | 0.001 | 37 | 0.649 | 0.016 |
| change_vs_prev | up | 124 (9) | 0.500 [0.378, 0.586] | 0.070 | -0.001 | 142 | 0.366 | -0.013 | 9 | 0.333 | 0.129 |
| change_vs_prev | same | 84 (4) | 0.417 [0.299, 0.559] | -0.055 | -0.063 | 117 | 0.342 | -0.042 | 2 | 0.000 | 0.420 |
| change_vs_prev | down | 28 (4) | 0.393 [0.172, 0.667] | -0.104 | -0.037 | 39 | 0.308 | -0.050 | 5 | 0.200 | 0.067 |
| change_vs_prev | na | 302 (35) | 0.483 [0.385, 0.599] | 0.015 | -0.014 | 416 | 0.478 | 0.005 | 20 | 0.500 | 0.068 |
| pivot | 1 | 104 (25) | 0.433 [0.328, 0.576] | -0.035 | -0.078 | 117 | 0.410 | -0.038 | 47 | 0.553 | 0.037 |
| pivot | 0 | 737 (41) | 0.484 [0.403, 0.566] | 0.041 | -0.008 | 930 | 0.414 | -0.002 | 26 | 0.462 | 0.097 |
| decade | 2000s | 251 (16) | 0.550 [0.443, 0.710] | 0.130 | 0.078 | 251 | 0.538 | 0.047 | 9 | 0.222 | 0.344 |
| decade | 2010s | 339 (16) | 0.416 [0.322, 0.551] | -0.002 | -0.065 | 339 | 0.354 | -0.025 | 25 | 0.520 | 0.056 |
| decade | 2020s | 251 (12) | 0.490 [0.296, 0.551] | -0.022 | -0.003 | 457 | 0.389 | -0.021 | 39 | 0.590 | -0.006 |

## 6. Event-time paths (section 8)

Mean of path(k) = I(t0+k)/I(t0) − B(t0+k)/B(t0) (k > 0: BHAR(k); k < 0: a positive value means the industry lagged the market before entry). n in parentheses. Bootstrap bands are in `results.json`.

| group | k=-12 | k=-6 | k=-3 | k=-1 | k=0 | k=1 | k=3 | k=6 | k=12 | k=24 | k=36 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S+ FYP_proposal | 0.012 (329) | 0.032 (371) | 0.031 (371) | 0.010 (371) | 0.000 (371) | 0.003 (371) | -0.010 (371) | -0.030 (371) | -0.039 (371) | -0.135 (279) | -0.010 (279) |
| S+ all | 0.005 (1089) | 0.016 (1137) | 0.008 (1137) | 0.000 (1137) | 0.000 (1137) | -0.008 (1137) | -0.022 (1137) | -0.020 (1137) | -0.006 (1047) | -0.012 (915) | 0.031 (841) |
| R-demand all | 0.019 (90) | 0.043 (94) | 0.023 (94) | 0.007 (94) | 0.000 (94) | -0.017 (94) | -0.032 (94) | 0.019 (94) | 0.041 (84) | 0.104 (78) | 0.058 (73) |
| R-supply all | 0.018 (73) | -0.020 (74) | 0.002 (74) | 0.007 (74) | 0.000 (74) | -0.003 (74) | 0.002 (74) | 0.007 (74) | 0.015 (74) | 0.130 (72) | 0.025 (71) |
| S0 all | 0.032 (289) | 0.023 (302) | 0.014 (302) | 0.004 (302) | 0.000 (302) | -0.002 (302) | -0.019 (302) | -0.014 (302) | -0.006 (291) | -0.020 (245) | 0.026 (229) |
| pivot all | 0.028 (223) | 0.013 (230) | 0.007 (230) | -0.004 (230) | 0.000 (230) | -0.009 (230) | -0.024 (230) | 0.005 (230) | -0.014 (213) | -0.058 (203) | -0.001 (189) |

## 7. Pre-event drift (BHAR from t0−12 / t0−3 to entry)

| group | window | n (docs) | mean [CI] | median | share > 0 |
|---|---|---|---|---|---|
| S+ FYP_proposal | 12 m | 329 (5) | 0.019 [-0.048, 0.107] | 0.001 | 0.502 |
| S+ FYP_proposal | 3 m | 371 (6) | -0.026 [-0.044, -0.002] | -0.037 | 0.364 |
| S+ all | 12 m | 1089 (52) | 0.047 [0.008, 0.098] | -0.006 | 0.497 |
| S+ all | 3 m | 1137 (54) | 0.004 [-0.011, 0.025] | -0.013 | 0.445 |
| R-demand all | 12 m | 90 (26) | 0.030 [-0.066, 0.108] | -0.040 | 0.467 |
| R-demand all | 3 m | 94 (27) | -0.021 [-0.050, 0.001] | -0.020 | 0.351 |
| R-supply all | 12 m | 73 (25) | 0.032 [-0.047, 0.107] | 0.001 | 0.521 |
| R-supply all | 3 m | 74 (26) | 0.012 [-0.022, 0.042] | -0.001 | 0.473 |
| S0 all | 12 m | 289 (31) | -0.015 [-0.057, 0.035] | -0.033 | 0.429 |
| S0 all | 3 m | 302 (32) | -0.008 [-0.032, 0.015] | -0.013 | 0.440 |
| pivot all | 12 m | 223 (45) | 0.015 [-0.027, 0.055] | -0.026 | 0.471 |
| pivot all | 3 m | 230 (45) | 0.005 [-0.019, 0.028] | -0.018 | 0.422 |

## 8. Short-window reaction (daily CAR vs 801003)

| group | window | n (docs) | mean CAR [CI] | median | share > 0 |
|---|---|---|---|---|---|
| S+ FYP_proposal | [0,+1] | 371 (6) | 0.0009 [-0.0007, 0.0032] | -0.0012 | 0.474 |
| S+ FYP_proposal | [0,+5] | 371 (6) | 0.0005 [-0.0083, 0.0099] | -0.0006 | 0.491 |
| S+ FYP_proposal | [0,+20] | 371 (6) | 0.0032 [-0.0146, 0.0219] | -0.0029 | 0.477 |
| S+ all | [0,+1] | 1137 (54) | 0.0016 [-0.0003, 0.0036] | 0.0006 | 0.515 |
| S+ all | [0,+5] | 1137 (54) | 0.0038 [-0.0004, 0.0083] | 0.0025 | 0.536 |
| S+ all | [0,+20] | 1137 (54) | 0.0001 [-0.0078, 0.0083] | -0.0029 | 0.477 |
| R-demand all | [0,+1] | 94 (27) | 0.0009 [-0.0062, 0.0055] | 0.0022 | 0.553 |
| R-demand all | [0,+5] | 94 (27) | -0.0015 [-0.0118, 0.0061] | 0.0061 | 0.574 |
| R-demand all | [0,+20] | 94 (27) | -0.0034 [-0.0158, 0.0112] | 0.0030 | 0.511 |
| R-supply all | [0,+1] | 74 (26) | -0.0025 [-0.0079, 0.0030] | -0.0057 | 0.365 |
| R-supply all | [0,+5] | 74 (26) | -0.0061 [-0.0163, 0.0045] | -0.0059 | 0.446 |
| R-supply all | [0,+20] | 74 (26) | 0.0089 [-0.0125, 0.0328] | 0.0018 | 0.514 |
| S0 all | [0,+1] | 302 (32) | 0.0013 [-0.0009, 0.0040] | -0.0006 | 0.490 |
| S0 all | [0,+5] | 302 (32) | 0.0016 [-0.0035, 0.0073] | 0.0017 | 0.540 |
| S0 all | [0,+20] | 302 (32) | 0.0065 [-0.0050, 0.0167] | 0.0034 | 0.530 |
| pivot all | [0,+1] | 230 (45) | 0.0020 [-0.0025, 0.0053] | 0.0014 | 0.543 |
| pivot all | [0,+5] | 230 (45) | 0.0041 [-0.0048, 0.0123] | 0.0028 | 0.535 |
| pivot all | [0,+20] | 230 (45) | 0.0063 [-0.0056, 0.0176] | 0.0073 | 0.539 |

## 9. Turnover share (industry turnover ÷ 申万A指 turnover)

| group | n | share −12…−1 | share +1…+12 | change [CI] | median ratio after/before | n (25–36) | share +25…+36 | change 25–36 [CI] |
|---|---|---|---|---|---|---|---|---|
| S+ FYP_proposal | 329 | 0.0276 | 0.0237 | -0.0038 [-0.0047, -0.0029] | 0.902 | 237 | 0.0265 | -0.0021 [-0.0060, 0.0027] |
| S+ all | 999 | 0.0251 | 0.0239 | -0.0012 [-0.0023, 0.0001] | 0.969 | 796 | 0.0253 | -0.0001 [-0.0022, 0.0020] |
| R-demand all | 80 | 0.0280 | 0.0298 | 0.0018 [-0.0005, 0.0042] | 0.973 | 73 | 0.0273 | -0.0009 [-0.0032, 0.0035] |
| R-supply all | 73 | 0.0262 | 0.0268 | 0.0006 [-0.0016, 0.0030] | 1.014 | 70 | 0.0262 | -0.0007 [-0.0051, 0.0043] |
| S0 all | 278 | 0.0273 | 0.0270 | -0.0003 [-0.0015, 0.0009] | 0.978 | 218 | 0.0281 | -0.0019 [-0.0048, 0.0010] |
| pivot all | 206 | 0.0244 | 0.0235 | -0.0009 [-0.0030, 0.0008] | 0.969 | 187 | 0.0219 | -0.0021 [-0.0045, 0.0002] |

## 10. Portfolios (C12)

| | start–end | months | ann. return | ann. 申万A指 | ann. excess (12×mean) | vol of excess | IR | max DD of excess | hit rate | avg holdings | rolling 36m excess: median / min / max / share > 0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 2000-11–2026-10 | 312 | 0.052 | 0.040 | 0.013 | 0.070 | 0.19 | -0.234 | 0.506 | 44.3 | 0.045 / -0.800 / 0.633 / 0.570 |
| P2 | 2000-09–2026-10 | 314 | 0.074 | 0.039 | 0.035 | 0.096 | 0.36 | -0.230 | 0.548 | 40.3 | 0.078 / -0.226 / 1.487 / 0.731 |
| P3 | 2000-09–2026-10 | 314 | -0.043 | 0.039 | -0.036 | 0.121 | -0.30 | -0.758 | 0.379 | 46.1 | -0.115 / -0.493 / 0.205 / 0.136 |

P3 is a long-short return (no benchmark subtraction): its "ann. return" is the compounded long-short return and "excess" is the same series. P3 long leg = P2 holdings (avg 40.3 series), short leg avg 5.9 series; both legs are non-empty from 2001-04 (266 months). P1 skipped a held series for missing data in 8 months (801193/801951 gaps, C14). The last month (2026-10) is partial.

## 11. Exploratory: placebo 1 variant preserving within-document repetition (not in the plan)

Because many events in one document map to the same industry while C8 gives them distinct replacement industries, the registered placebo 1 may understate how much a document's win rate can vary by chance. This **exploratory** variant relabels each document's distinct actual series to distinct random series of the same level, so events that shared an industry still share one. It is reported only as a sensitivity check.

| subset | rule | h | n | actual win | relabel win median [5–95%] | p win | actual mean | relabel mean median [5–95%] | p mean |
|---|---|---|---|---|---|---|---|---|---|
| FYP_proposal | S+ | 12 | 371 | 0.342 | 0.461 [0.396, 0.526] | 1.000 | -0.039 | 0.000 [-0.022, 0.028] | 0.999 |
| FYP_proposal | S+ | 36 | 279 | 0.444 | 0.452 [0.380, 0.534] | 0.568 | -0.010 | 0.009 [-0.035, 0.064] | 0.737 |
| FYP_proposal | R-demand | 12 | 24 | 0.417 | 0.583 [0.417, 0.750] | 0.955 | 0.081 | 0.001 [-0.071, 0.088] | 0.931 |
| FYP_proposal | R-demand | 36 | 19 | 0.316 | 0.474 [0.316, 0.684] | 0.962 | 0.116 | 0.019 [-0.082, 0.159] | 0.889 |
| FYP | S+ | 12 | 673 | 0.373 | 0.474 [0.425, 0.520] | 1.000 | -0.013 | 0.012 [-0.005, 0.032] | 0.992 |
| FYP | S+ | 36 | 581 | 0.468 | 0.458 [0.406, 0.513] | 0.384 | 0.037 | 0.027 [-0.007, 0.064] | 0.321 |
| FYP | R-demand | 12 | 58 | 0.500 | 0.534 [0.414, 0.655] | 0.723 | 0.025 | 0.020 [-0.031, 0.086] | 0.543 |
| FYP | R-demand | 36 | 53 | 0.528 | 0.491 [0.377, 0.623] | 0.390 | 0.055 | 0.042 [-0.041, 0.149] | 0.588 |
| all | S+ | 12 | 1047 | 0.414 | 0.485 [0.450, 0.521] | 1.000 | -0.006 | 0.017 [0.002, 0.033] | 0.995 |
| all | S+ | 36 | 841 | 0.478 | 0.473 [0.435, 0.517] | 0.444 | 0.031 | 0.034 [0.007, 0.063] | 0.559 |
| all | R-demand | 12 | 84 | 0.464 | 0.524 [0.429, 0.643] | 0.887 | 0.041 | 0.020 [-0.025, 0.071] | 0.773 |
| all | R-demand | 36 | 73 | 0.521 | 0.507 [0.397, 0.616] | 0.450 | 0.058 | 0.041 [-0.032, 0.132] | 0.634 |

## Checks

1. **Hand recomputation** (seed 44): BHAR(12) and BHAR(36) for 5 random tested events were recomputed with the csv module directly from `sw_monthly.csv` closes (equal-weight monthly-rebalanced for multi-code events). Max absolute difference vs `event_level.csv`: 8.9e-16 — PASS.

   | event | series | entry | h | hand | event_level.csv |
   |---|---|---|---|---|---|
   | E0487 | 801131 | 2009-04 | 12 | 0.1347778040 | 0.1347778040 |
   | E0487 | 801131 | 2009-04 | 36 | 0.1580826462 | 0.1580826462 |
   | E0236 | 801178 | 2005-10 | 12 | 0.0294118335 | 0.0294118335 |
   | E0236 | 801178 | 2005-10 | 36 | -0.1504934217 | -0.1504934217 |
   | E1231 | 801170 | 2016-03 | 12 | -0.0506650244 | -0.0506650244 |
   | E1231 | 801170 | 2016-03 | 36 | -0.0846477163 | -0.0846477163 |
   | E1229 | 801191 | 2016-03 | 12 | 0.0309204519 | 0.0309204519 |
   | E1229 | 801191 | 2016-03 | 36 | -0.1432924481 | -0.1432924481 |
   | E0401 | 801191;801193 | 2006-03 | 12 | 1.9666257171 | 1.9666257171 |
   | E0401 | 801191;801193 | 2006-03 | 36 | 2.8390811994 | 2.8390811994 |
2. **Win rates vs event_level.csv:** primary test n = 279 (csv) vs 279 (json); win share 0.444444 vs 0.444444; mean BHAR(36) -0.009690 vs -0.009690; h = 12: 0.342318 vs 0.342318. Every non-empty S+ / R-demand / R-supply H-a row at h = 12 and 36 in every subset also matches the csv: yes — PASS.
3. **Timing:** events whose entry month precedes the event month: 0; every entry bar date is strictly after the event date: True; BHAR values whose horizon runs past the last bar: 0; daily CARs running past the last day or with day 0 before the event date: 0; portfolio holdings before t0+1: 0 — PASS.
4. **Counts.** Events 2234; tested 1607; excluded by reason: no_series_at_entry 335, no_sw_code 292. Incomplete horizons (tested events excluded from that horizon): h=1 0, h=3 0, h=6 0, h=12 111, h=24 297, h=36 393. Events used per subset and horizon (all stances; per-stance counts are in `results.json` meta.n_by_subset_stance_h and the n column of each win-rate row):

   | subset | h=1 | h=3 | h=6 | h=12 | h=24 | h=36 |
   |---|---|---|---|---|---|---|
   | FYP_proposal | 577 | 577 | 577 | 577 | 438 | 438 |
   | FYP | 1111 | 1111 | 1111 | 1000 | 861 | 861 |
   | other | 496 | 496 | 496 | 496 | 449 | 353 |
   | GWR_first | 0 | 0 | 0 | 0 | 0 | 0 |
   | all | 1607 | 1607 | 1607 | 1496 | 1310 | 1214 |

   | subset | stance | h=1 | h=3 | h=6 | h=12 | h=24 | h=36 |
   |---|---|---|---|---|---|---|---|
   | FYP_proposal | S+ | 371 | 371 | 371 | 371 | 279 | 279 |
   | FYP_proposal | R-demand | 24 | 24 | 24 | 24 | 19 | 19 |
   | FYP_proposal | R-supply | 9 | 9 | 9 | 9 | 8 | 8 |
   | FYP_proposal | S0 | 173 | 173 | 173 | 173 | 132 | 132 |
   | FYP | S+ | 763 | 763 | 763 | 673 | 581 | 581 |
   | FYP | R-demand | 68 | 68 | 68 | 58 | 53 | 53 |
   | FYP | R-supply | 19 | 19 | 19 | 19 | 18 | 18 |
   | FYP | S0 | 261 | 261 | 261 | 250 | 209 | 209 |
   | other | S+ | 374 | 374 | 374 | 374 | 334 | 260 |
   | other | R-demand | 26 | 26 | 26 | 26 | 25 | 20 |
   | other | R-supply | 55 | 55 | 55 | 55 | 54 | 53 |
   | other | S0 | 41 | 41 | 41 | 41 | 36 | 20 |
   | GWR_first | S+ | 0 | 0 | 0 | 0 | 0 | 0 |
   | GWR_first | R-demand | 0 | 0 | 0 | 0 | 0 | 0 |
   | GWR_first | R-supply | 0 | 0 | 0 | 0 | 0 | 0 |
   | GWR_first | S0 | 0 | 0 | 0 | 0 | 0 | 0 |
   | all | S+ | 1137 | 1137 | 1137 | 1047 | 915 | 841 |
   | all | R-demand | 94 | 94 | 94 | 84 | 78 | 73 |
   | all | R-supply | 74 | 74 | 74 | 74 | 72 | 71 |
   | all | S0 | 302 | 302 | 302 | 291 | 245 | 229 |

5. **Placebo machinery (additional).** 200 random placebo-1 (draw, event) BHARs recomputed by the slow per-event path: max relative difference 4.9e-08 (float32 storage). The date-shift code path run with a zero shift reproduces every actual BHAR (max abs diff 2.7e-15, same missing pattern: True). Share of (document, shift) pairs whose shifted entry month equals t0 + shift: 0.966 (the rest are dates near month-end, where the shifted date can fall after that month's last trading day) — PASS.

Other measures: pre_12 available for 1541 events, pre_3 1607; CAR[0,1]/[0,5]/[0,20] 1607/1607/1607; turnover pre/post 1–12/post 25–36 1541/1496/1214.

## Deviations

All items below were decided from the plan text before any outcome was computed and applied uniformly. None changes a hypothesis, win rule, horizon or test.

1. **Plan dimension for subgroups.** The events table has no plan column. Plan is derived mechanically from the doc_id prefix: P10->十五, P11->十一五, P12->十二五, P13->十三五, P14->十四五, P15->十五五; every other document (B..) gets plan = 'other'. Applied as instructed by the caller.
2. **Placebo 1: draw without replacement within a document is infeasible for some document-level groups.** C8 asks each document's replacement industries to be drawn without replacement. In 14 (document, level) groups (P10-A1 L1 30/16, P10-A2 L1 17/16, P11-A1 L1 37/16, P11-A2 L2 48/42, P11-A2 L1 37/16, P12-A1 L2 45/44, P12-A1 L1 39/16, P12-A2 L1 26/16, P13-A1 L1 75/28, P13-A2 L1 48/28, P14-A1 L1 78/28, P14-A2 L1 61/28, P15-A1 L2 126/124, P15-A1 L1 48/31; codes needed / eligible pool) the document needs more replacement codes than the pool holds. Resolution, applied to every group: codes are drawn by walking through a random permutation of the pool; when the pool is exhausted a fresh independent permutation is started (no repeats until every eligible series has been used once). Within one event, codes are always distinct (a duplicate at a permutation boundary is redrawn from the rest of the pool). Groups where the pool is large enough are unaffected (pure draw without replacement).
3. **Placebo 1: eligibility of replacement series.** Replacement series must satisfy the same eligibility as the actual selection: a close at the entry month (C8) and no missing month between t0 and min(t0+36, last bar) (C14). Only 801193 and 801951 are affected.
4. **Placebo 2: which series a shifted event uses.** 'Same industries' is implemented as the event's actual series_used (same codes, same level). At the shifted entry month the C2/C14 filters are applied within series_used (keep codes with a close at the shifted t0 and no missing month to min(t0+36, last bar)); if none remain the event has lost data and is dropped from that draw. No level fallback is done for shifted events. A shifted date whose entry month falls before 2000-01 (no monthly data) or after the last bar is dropped.
5. **Month-end calendar.** Entry months (C3) use the benchmark 801003's bar dates as the month-end calendar. In 14 months a few series carry a bar dated a few days earlier (801193, 801951) or one day later (801952 in 2022-03) than 801003; no event date falls inside such a gap, so no entry month depends on this. Monthly closes are used exactly as they appear in sw_monthly.csv (a present bar is data; C14 treats only absent months as missing). None of these early-dated bars lies inside any tested event's [t0, t0+36] window (checked in the run).
6. **Daily trading calendar.** For C7/C14 the trading-day calendar is the set of dates on which 801003 has a close. The source has 18 dates on which some series have a close but 801003 does not (2015-11-27 is held by 95 series; the other 17 only by 801950 and/or 801952). On those dates no abnormal return can be formed, so they are not trading days of the calendar; returns are close-to-close between consecutive calendar days for index and benchmark alike. A code is used in a CAR only if it has a close on every calendar day from day -1 to day k (day -1 is needed for the day-0 return). Codes are the event's series_used.
7. **Multi-code events: pre-event, turnover and path windows.** C5/C6/C14 windows for multi-code events are computed only when every code in series_used has data in every month of the window; otherwise missing. Turnover sums the codes' turnover (C6) and divides by 801003's.
8. **Event-time paths (section 8).** path(k) = I(t0+k)/I(t0) - B(t0+k)/B(t0), where I is the event's equal-weight monthly-rebalanced industry index and B is 801003. For k > 0 this is BHAR(k); for k < 0 it is the relative-wealth gap normalised at entry (a pre-entry outperformance shows as a negative value rising to 0 at k = 0).
9. **Exclusion reason names.** Both sw_l1 and sw_l2 equal to none (or empty) -> 'no_sw_code' (plan section 2.2). C2 -> 'no_series_at_entry'. C14 -> 'data_gap' (used when at least one coded series had a close at entry but every candidate was removed by the gap rule). An empty sw_l2 cell is treated like 'none'.
10. **Horizons and placebos reported.** win_rates rows are produced for h = 1, 3, 6, 12, 24, 36 (all section 3 horizons); placebos are run for all of them. Primary is h = 36 (C1); h = 12 is secondary; other horizons are descriptive.
11. **p-values.** One-sided share of placebo draws at least as favourable as the actual statistic (spec): win rate - draws with placebo win rate >= actual; mean BHAR - draws with placebo mean >= actual for S+ and R-supply H-b, <= actual for R-demand and R-supply H-a. No +1 correction. Date-shift draws in which no event of a row survives are dropped from that row's distribution (count reported).
12. **Portfolio statistics.** ann_return/ann_bench are geometric annualised returns over the portfolio's months (start = first month with a holding, end = last bar 2026-10 which is a partial month). ann_excess = 12 x mean monthly excess return, vol_excess = sqrt(12) x st.dev. of monthly excess return, info_ratio = ann_excess / vol_excess, max drawdown on the compounded excess-return series, hit_rate = share of months with excess > 0. For P3 the 'excess' series is the long-short return itself (C12). A month in which a leg holds no series with valid data has P3 return 0 (C12); for P1/P2 such a month (if any) would be held in cash at 0. The rolling 36-month excess return (section 7) is compounded portfolio minus compounded benchmark over the trailing 36 months (P3: compounded long-short return), stored in results.json under portfolios.<P>.rolling36_excess. P1 plan end = December of the plan's last year (C12), plan from doc_id prefix.
13. **Bootstrap of medians and subgroup CIs.** Section 5 also asks for CIs of the median BHAR; win_rates rows carry extra fields median_ci_lo/median_ci_hi (doc-clustered, same draws). Subgroup ci_lo/ci_hi are win-rate CIs; subgroup rows also carry mean_ci_lo/hi. S0 rows are descriptive: win_rate is null, pos_rate (share BHAR > 0) is given.
14. **Occurrence note (portfolio cash months).** The P1/P2 cash rule in item 12 was triggered: P2 held no series in 19 months (2004-04…2005-10, no S+ event active in its 36-month window); those months earn 0 and P3 is 0 there (C12). P1 had 0 such months.
15. **Plan section 5 vs C10.** The plan text says "resample event dates"; C10 sets the cluster to doc_id. C10 was applied. Tested documents: 62; distinct event dates: 60; documents sharing a date: B05a/B05b (2009-03-20); B05g/B05h (2009-05-18). Placebo 2 shifts each document independently (C9).
16. **Plan section 7 vs C12 for P1.** The plan says active "60 months after the proposal date"; C12 says through December of the plan's last year. C12 was applied.

## Limitations

- **Few independent clusters.** The primary test rests on 5 documents (P10-A1…P14-A1), FYP subsets on 10–11, and each plan-level subgroup on 2. Percentile bootstrap intervals with this few clusters are too narrow and unstable; the placebo distributions are the more informative comparison for the FYP rows.
- **Overlap and dependence.** Events of one document share a date and often the same industry series (e.g. many P13-A1 events map to the same L1 index); 36-month windows of successive documents overlap. Event counts overstate the effective sample size.
- **Placebo 1 construction.** In 14 (document, level) groups the pool was too small for draws without replacement (Deviation 2). Even where feasible, C8 gives a document's events distinct industries although the actual events repeat industries, so the registered null may be narrower than the true chance variation; the exploratory relabel variant (section 11) shows how much this matters.
- **Heavy-tailed BHAR.** BHAR is a difference of gross growth factors, so windows covering strong markets (2006–2007, 2014–2015) produce very large magnitudes; means can be dominated by one document. Medians and win rates are less affected.
- **Index availability.** Only current SW2021 indices exist (no predecessor series). Many L1 indices start 2014-02 and many L2 indices 2021-12, so 335 events had no series at entry and early events are measured on the subset of industries with long histories (often at L1 rather than L2).
- **Price indices.** Both industry and benchmark exclude dividends; differences in dividend yield across industries are not captured.
- **Data quality.** 801193 证券Ⅱ and 801951 煤炭开采 have long gaps (handled by C14); 14 monthly bars are dated before month-end (none inside any tested event window); 801003 lacks 18 daily dates that some series have (Deviation 6). The 2026-10 bar is partial (P15-A1 12-month horizon and the last portfolio month).
- **Document selection.** The `other` documents were chosen by people who know later market history (C1); those results are exploratory. No document has doc_type GWR_first, so that C13 subset is empty.
- **Many comparisons.** The tables contain many rows (subsets × rules × horizons × subgroups). Only the primary test is confirmatory; a small p-value elsewhere is expected by chance and is exploratory.
- **One-sided tests.** The registered p-values only test the rule's direction. Results in the opposite direction (e.g. S+ underperformance at 1–12 months, where the one-sided p is 1.000) have no registered test and are exploratory observations.

Seeds: {"bootstrap": 20261027, "placebo_perm": 11, "placebo_shift": 22, "perm_relabel_exploratory": 33, "self_check": 44}. Bootstrap 10,000 draws; placebos 2,000 draws each. full run 43 s on 2 CPUs; placebo BHARs vectorised by gathering monthly returns for replacement codes; date-shift outcomes precomputed for all 38 shifts.
