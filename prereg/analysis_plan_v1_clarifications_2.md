# Clarifications to analysis plan v1 — addendum 2 (data gaps)

Written 2026-10-27 after inspecting data completeness and before any event exists or is joined to prices.

C14. Missing data. Two series have long gaps in the source (801193 证券Ⅱ, 801951 煤炭开采; see data/README.md).
     A month or day absent from the data is missing, never a zero return. For each event, a selected series is dropped
     from the event's set if it has any missing month between t0 and min(t0+36, last bar); if no series remain at that
     level, fall back to the next level under C2 (L2 → L1), and otherwise exclude with reason `data_gap`. Pre-event
     windows (C5) and turnover windows (C6) are computed only when every month in the window has data; otherwise they
     are missing. Daily CARs (C7) use only codes that have every trading day in the window; otherwise missing.
     Portfolios (C12) skip a series in any month where it lacks the close of that month or of the previous month.
