# Coding work log

- 2026-10-26 13:24 UTC — first coding agent launched under `prereg/coding_protocol_v1.md`; it was interrupted at
  14:02 UTC (a user message interrupted the session) before saving any file. No events existed.
- 2026-10-26 22:00 UTC — coding split into stage 1 (extraction, `prereg/extraction_protocol_v1.md`) and stage 2
  (coding) plus a mechanical merge (`scripts/merge_events.py`). Five extraction agents launched in parallel
  (P10–P11, P12–P13, P14–P15, B01–B13, B14–B37).
- 2026-10-26 22:15 UTC — the B14–B37 extraction agent stopped when an output filter blocked a long verbatim output
  (while on B15). All extraction agents were told to extract verbatim key clauses (≤ 60 汉字, exact wording, `…` where cut)
  instead of whole long sentences, written in small batches. Files written before this point contain whole sentences;
  both forms are verbatim.
- 2026-10-27 15:24 UTC — all stage-2 row files written (FYP proposals P10–P15, outlines P10–P15, 44 B documents incl. B06–B13 extracted and coded by one agent). Merged and frozen with scripts/merge_events.py --freeze.
