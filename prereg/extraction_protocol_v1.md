# Extraction protocol v1 (stage 1 of blind coding)

Written 2026-10-27 before any event is coded or joined to prices. The first coding agent was interrupted before it
saved anything, so coding is now split into two blind stages:

- **Stage 1 — extraction (this file).** One agent per group of documents finds the official full text, verifies the
  publication date, and copies out, verbatim, every sentence that names a specific industry or sector. No coding.
- **Stage 2 — coding.** Coding agents read only the stage-1 extracts (plus targeted re-checks of the source when a
  quote is in doubt) and code them under `coding_protocol_v1.md` into per-group row files.
- **Merge (mechanical).** A script assigns `event_id`s, computes `pivot` mechanically (per SW code, chronological:
  1 when the stance direction — support vs restriction — reverses against the previous coded event on the same code),
  validates fields and writes `events/events_v1.csv` + `FROZEN.sha256`. Written before any event is joined to prices.

Blindness rules from `coding_protocol_v1.md` §0 apply to every stage: no stock prices, index levels, earnings or
market reactions; do not open anything under `/tmp/claude-0/`, `/home/claude/policy_bt/data/` or `/home/claude/policy_bt/backtest/`.

## What to extract
From each assigned document, every sentence (or list item) that names a specific industry, sector, product class,
technology field or named industrial programme, in the economic, industrial, agricultural, energy, transport,
services, science-and-technology, finance, real-estate/housing, environment/resources and consumption parts of the
text. Include sentences that restrict or regulate an industry (产能过剩、淘汰、调控、整治、规范、限制、反垄断 …) as
carefully as sentences that support one. Skip sentences that mention no specific industry (pure macro, party building,
social policy without an industry, diplomacy, military affairs except defence-industry wording).

Copy the sentence exactly as published (simplified Chinese, original punctuation). Keep the chapter / section heading
above each group of sentences. Do not paraphrase, summarise, translate, merge or reorder.

## Output (one file per document)
`/home/claude/policy_bt/coding_work/texts/<doc_id>.md`:

```
# <doc_id> <full official title>
- issuer: …
- publication_date: YYYY-MM-DD   (date the full text was first published)
- date_source: <URL of a dated source you opened that shows that date>
- fulltext_urls: <URL(s) you actually read the text from>
- coverage: complete | partial (say which chapters are missing and why)

## <chapter / section heading as published>
- <verbatim sentence>
- <verbatim sentence>
## <next heading>
…
```

Write the file progressively (create it after the first chunk, append after every chunk) so nothing is lost if you
are interrupted. Also append one line per document to `/home/claude/policy_bt/coding_work/docs_index.tsv`:
`doc_id<TAB>title<TAB>issuer<TAB>publication_date<TAB>date_source<TAB>fulltext_url<TAB>coverage`.

## How to read long documents
The workspace shell cannot reach most websites. Use WebSearch to find the text and WebFetch to read it. WebFetch pages
through long texts with its `offset` parameter; read the whole document chunk by chunk. Ask WebFetch for verbatim
sentences, e.g. "From this part of the text, return verbatim, in order, every heading and every sentence that names a
specific industry, sector, product or technology field. Do not summarise or paraphrase; copy the Chinese exactly."
If a page is a table of contents, follow the chapter pages. Prefer gov.cn, ndrc.gov.cn, npc.gov.cn, news.cn /
xinhuanet.com, people.com.cn; a reputable reprint is acceptable when the official page is unreachable (note it).
