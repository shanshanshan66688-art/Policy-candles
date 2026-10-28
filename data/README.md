# SW industry index data

Source: 申万宏源研究 (SWS Research) public index pages, https://www.swsresearch.com/institute_sw/allIndex/releasedIndex,
retrieved 2026-10-26 through a browser (current SW2021 indices only: 31 L1, 124 L2, 9 market indices).
Raw file: `raw/sw_index_data_20261026.json.gz`, sha256 716cf3acd088a7638af4ef7c1188ae0862ff610e1658beff9caf9974ffba56fc.

## Files
- `sw_monthly.csv` — `code, name, level (L1/L2/MKT), parent_l1, bar_date (last trading day of the month), month,
  open, high, low, close, turnover_100m_cny` (monthly turnover, 100 million CNY). 2000-01 … 2026-10.
- `sw_daily.csv` — `code, date, close`. 1999-12-30 … 2026-10-23.
- `sw_lineage.csv` — predecessor (discontinued) series; empty: none were used.

## Notes
- SW indices are price indices (no dividends). Base 1000 on 1999-12-30 (that base row is dropped from the monthly file).
- 801003 申万Ａ指 is the benchmark.
- Many current indices start late: several L1 (e.g. 801730 电力设备, 801780 银行, 801880 汽车, 801750 计算机) on
  2014-02; many L2 (e.g. 801735 光伏设备, 801737 电池, 801125 白酒, 801994 教育) on 2021-12. Start month = first row.
- 2026-10 is a partial month (bar dated 2026-10-23).
- Source gaps: 801193 证券Ⅱ is missing 82 months (from 2015-05, scattered to 2026) and 1,905 trading days;
  801951 煤炭开采 is missing 58 months (2017-02 … 2021-11) and 1,183 trading days. A few market indices miss 2–4 days.
  Months/days absent from the files are missing, not zero-return.
