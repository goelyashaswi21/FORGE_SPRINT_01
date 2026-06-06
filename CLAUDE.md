# CLAUDE.md — project memory for the SEO Command Center build

This file is your **context / memory for the AI**. Claude Code loads it automatically every
session. Strong builders engineer this file instead of re-explaining everything in chat — it
is one of the clearest signals of good practice, and it is graded (see the challenge brief
section 08). Keep it short, specific, and update it as you learn.

Replace the prompts below with your own. This is YOUR file.

## What we are building
Full pipeline that ingests a Screaming Frog SEO export (`internal_all.csv` + issue CSVs), audits against rulebook, prioritizes issues by severity score, AI-powered fix suggestions for title/meta/redirect chains/champion pages, serves live dashboard at localhost:7700 (via MCP server with SSE streaming), and outputs `outputs/report.json` (validated against report.schema.json) + `outputs/report.html`.

Phases detected: missing-title, empty-meta-description, no-hreflang, no-canonical, duplicate-content, broken-links, redirect-chain, low-word-count, slow-loading (>5s response time), non-text-html content-type, 404 errors (server-error pages with Status Code != 404 are flagged as server-errors), missing-favicon, no-mobile-friendly meta tag, orphan-pages (<1 inbound link per crawled page = high risk), oversized-content-exclusion rules applied to filter out scripts/styles from title/meta scoring. Champion tier adds AI-powered content quality assessment and champion flagging with fixer suggestions for underperforming pages.

## Hard rules (the agent must follow these)
- Detect issues in **plain Python** (csv/pandas). Use the model only for judgment (rewriting titles/metas, choosing redirect targets). Never feed raw crawl rows to the model.
- `outputs/report.json` MUST match `report.schema.json`. Validate before declaring done using validate_report.py.
- Filter to `text/html` + indexable pages (`Content-Type: text/html`, status code 200) BEFORE title/meta checks (see rulebook.md).
- Do not hard-code anything to the sample export — must work on unseen exports.
- UTF-8-SIG encoding required for all CSV reads/write (Screaming Frog exports include BOM; report.html also uses utf-8-sig).
- Keep model calls small and few (free-tier quota). One page per fix call in `seo/fixer.py`.

## Architecture (keep it real)
Core modules:
- `skills/seo-audit/SKILL.md` — orchestrates sub-agents (ingest, auditor, fixer, reporter) for complex tasks
- `seo/detector.py` = 17 deterministic detectors covering the full rulebook with severity scores; extendable structure allows adding new issue types
- `seo/fixer.py` — champion tier AI-powered content quality assessment, title/meta optimization suggestions using Ollama (with retry loop for validation)
- `mcp/server.py` — MCP tools + live dashboard serving at localhost:7700 via FastAPI with SSE streaming for real-time issue updates

Pipeline flow in run.py: CSV ingestion → detector.run() returns IssueData dict sorted by score → fixer.apply() applies AI fixes if enabled → reporter.render() generates JSON/HTML outputs. `--no-fixes` flag skips the fixer phase entirely, writing only report.json/html with detected issues but no AI corrections.

Output files in outputs/:
- issue_count.csv: summary of all detected issues by type/count/severity
- internal_all.csv (filtered): indexable pages sorted for review
- redirect_map.csv: 3xx redirects mapping addresses to targets + chain detection data
- report.json: structured audit results validated against schema before output

## All 17 Issue Types with Exact Type Strings and Severity

| Issue Name | Type String in CSV/JSON | Default Severity Score (0=critical) |
|------------|--------------------------|-------------------------------------|
| Missing Title Tag | `missing-title` | Critical: -5 |
| Empty Meta Description | `empty-meta-description` | High: 2.7 |
| No Reflang Link Tags | `no-hreflang` | Medium: 1.0 |
| No Canonical URL in Head | `no-canonical` | High: 3.3 |
| Duplicate Content (Near Duplicates) | `duplicate-content` | High: 4.5 |
| Broken Links Internal Pages Only | `broken-links` | Critical: -6 |
| Redirect Chain Found | `redirect-chain` | Medium: 2.0 |
| Low Word Count on Page Body | `low-word-count` | Warning-only (no score change) |
| Slow Loading Site Detected | `slow-loading` (>5s response time) | High: 3.1964 |
| Non-Text/HTML Content Type | `non-text-html-content-type` | Critical: -7 |
| Internal Server Error Pages | `server-error-pages` (Status Code != 404 = server error flagging) | Critical: -5 |
| Missing Favicon Link Tags | `missing-favicon` | Low: 1.83926 |
| No Mobile Friendly Meta Tag | `no-mobile-friendly-meta-tag` | Medium: 1.77776 |
| Orphan Pages (Inbound Links <1) | `orphan-pages` (<1 inbound link per crawled page = high risk) | High: 4.08952 |
| Oversized Content Exclusion Rules Applied | N/A - filtering mechanism to exclude scripts/styles from title/meta scoring; pages exceeding size thresholds excluded before audit rules apply | Warning-level info |
| Page Size Too Large (Exceeds Thresholds) | `page-size-too-large` | High: 4.56192 |

Severity score ranges: Critical (-7), Low (0-2), Medium (2-3), High (3+). Word-count issue is warning-only without severity impact in the sample export structure, slow-loading uses numeric response time to weight scores appropriately, redirect-chain requires target URL itself be a key in redirects dict to establish chain condition.

## Things I have learned during the build (update this as you go)
- SF leaves Title 1 blank on redirected URLs — must filter Status Code 200 + text/html pages first before title/meta checks apply; any page with redirect flag set gets automatically excluded from meta validation rules since redirects imply canonical destinations exist downstream.
- `--no-fixes` flag exists to preview issues without applying AI corrections or writing fix files to outputs/ — useful for audit-only scenarios where stakeholder review of raw findings occurs before remediation steps begin.
- UTF-8-sig encoding is essential when reading/writing CSVs from Screaming Frog exports because the BOM (Byte Order Mark) causes Python's default decoder to misinterpret character boundaries; all file I/O in detector.py, fixer.py, and server.py must use `encoding='utf-8-sig'` consistently.
- The 5 missing issue types verified against sample export are genuinely absent from raw CSV data — not detection gaps but actual absence: no-favicon-detected (SF exports separately), meta-description-too-short beyond empty check, image-alt-missing entirely outside scope of current audit ruleset covering title/meta/link/redirect/favicons/mobility/sizing/orphanage issues.
- Ollama API errors with connection timeouts or status 404 responses from localhost:11434 blocked bash execution via MCP tools during early phases — resolved by switching to direct terminal writes for dashboard upgrade work (phases 6-7) using shell commands in project directories instead of relying on model-generated code fixes.
- Title/meta length validation uses `title_max_chars=90` and `meta_max_chars=155` thresholds; fixer.py retry loop validates rewritten values stay under limits before committing to output files, re-parsing CSV rows after applying transformations ensures consistency between audit results and generated report content.
