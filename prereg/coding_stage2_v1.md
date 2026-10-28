# Stage 2 coding instructions v1 (supplements coding_protocol_v1.md)

Written 2026-10-27 before any event is coded. Coding agents apply `coding_protocol_v1.md` (§0 blindness, §2 fields and
rubric) to the stage-1 extracts in `coding_work/texts/`. Differences from the original single-agent plan:

1. **Input.** Read the extract files assigned to you (and, for `change_vs_prev`, the previous plan's proposal extract).
   You may re-open a document's source URL (listed in the extract header) only to check a quote or its context.
   Never look up anything about markets (§0).
2. **Output.** One CSV per document: `coding_work/rows/<doc_id>.csv`, UTF-8, written with Python's csv module, header:
   `doc_id,doc_name,doc_type,issuer,event_date,concept_zh,concept_en,sw_l1,sw_l2,stance,intensity,change_vs_prev,quote_zh,quote_en,prev_quote_zh,source_url,notes`
   (no `event_id` and no `pivot`: the merge script assigns `event_id` and computes `pivot` mechanically).
   `event_date` = the document's `publication_date` from its extract header.
3. **One row per (document, industry concept).** If a document names the same concept several times, code one row
   using the strongest wording and put the other phrases in `notes`. Different concepts that map to the same SW code
   stay separate rows (e.g. 集成电路 and 新型显示 both under 电子).
4. **change_vs_prev** for FYP proposals: compare with the same concept in the previous plan's proposal extract
   (十五 = `na`). For each concept in the previous proposal that has no counterpart now, add a `dropped` row
   (stance `S0`, intensity 1, quote `（未提及）`, `prev_quote_zh` = the old wording). For FYP outlines (A2): code a row
   only where the outline's stance, intensity or quantitative target for a concept differs from its own proposal, or
   the concept is absent from the proposal; `change_vs_prev` for outline rows compares with the same plan's proposal.
   Other documents: `change_vs_prev = na`.
5. **SW mapping.** Use `prereg/sw_taxonomy.csv`. Map by what the concept is; use L2 codes where one clearly fits, the
   L1 code always (the L1 parent of the L2 codes). Broad concepts (e.g. 战略性新兴产业 as a whole, 现代服务业 as a whole,
   制造业 as a whole) are coded with `sw_l1 = none`, `sw_l2 = none` and a note: they have no single industry.
6. **Quotes.** `quote_zh` ≤ 40 汉字, copied exactly from the extract (which is verbatim). `quote_en` = your faithful
   translation. `prev_quote_zh` ≤ 40 汉字 from the previous plan's extract.
7. When finished, write a short `coding_work/rows/<group>_log.md`: judgement calls, borderline mappings, concepts
   coded as `none`.
