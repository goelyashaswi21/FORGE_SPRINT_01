# DECISIONS.md — decision & learnings log

## My log

- `[08:30]` Chose plain csv parsing over pandas for detection → fewer deps, no install issues on grader machine, fast enough for 5k rows. Model quota saved for fixer only.

- `[08:45]` Decided to filter to `text/html` + `Status Code 200` + `Indexability: Indexable` before title/meta checks → SF exports include redirect rows with blank Title 1; including them caused false positives on missing_title. Added `is_html()`, `is_200()`, `indexable()` helpers in detector.py.

- `[09:10]` Title duplicate detector initially flagged single-occurrence titles → bug was iterating all rows not just duplicated groups. Fixed: group by title value, emit only groups where `len(urls) > 1`.

- `[09:30]` Chose `utf-8-sig` encoding for all CSV reads → Screaming Frog exports include a BOM that Python's default utf-8 decoder misreads, causing the first column header to appear as `\ufeffAddress` instead of `Address`. All `open()` calls in detector.py use `encoding="utf-8-sig"`.

- `[09:50]` Implemented redirect_chain as: build `{src: target}` map for all 3xx rows, then flag any src whose target is also a key in the map → correctly identifies chains without flagging simple single-hop redirects.

- `[10:15]` fixer.py first version had no length guard on rewritten titles → model occasionally returned 70+ char titles. Added a second Ollama call to shorten if `len(new_title) > 60`. This validation loop is applied to both title and meta rewrites.

- `[10:40]` Ollama connection errors (ConnectionTimeout on localhost:11434) blocked MCP tool usage during dashboard upgrade phases → switched to direct terminal writes using shell commands for phases 6-7 instead of relying on model-generated code edits via MCP tools.

- `[11:00]` Dashboard initial version had no sorting → added sortable column headers to the issues table so severity/count columns can be reordered by the user. Done banner added to signal pipeline completion.

- `[11:20]` report.html first version was plain text dump → upgraded with CSS cards, severity colour badges (red/amber/grey), exec summary block showing High/Medium/Low counts at top.

- `[11:35]` validate_report.py initially ran without error handling → added try/except around schema validation and printed specific field failures to make debugging faster. Confirmed PASS on sample export before final commit.

- `[11:50]` Wired `--no-fixes` flag: initially fixer ran unconditionally, slow on large exports and burns model quota → added conditional branch in run.py that skips fixer entirely but still runs ingest + detection + report generation.

- `[12:10]` Confirmed 5 issue types (hreflang, canonical, favicon, mobile-meta, non-text-html) absent from sample export data — not detection gaps but genuine absence in the crawl. Detectors still coded and will fire on exports that contain these columns.

- `[12:30]` Chose `_best_match()` path-similarity heuristic for redirect targets on 404s → avoids a model call per broken URL, stays within efficiency budget, and produces reasonable suggestions for common URL restructuring patterns.
