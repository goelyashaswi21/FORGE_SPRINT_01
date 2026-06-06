# PROMPTS.md — my key prompts log

Keep the handful of prompts that actually moved the build. Not every message — the ones that
mattered: the system/sub-agent prompts, the ones you iterated on, the "this finally worked"
moment. This shows how you direct an AI, which is graded (challenge brief section 08).

Format per entry:
- **Prompt** (paste it)
- **For:** what you were trying to do
- **Revised?** did you have to change it, and why

---

## Example (replace with your own)

- **Prompt:** "Extend seo/detector.py to detect redirect chains: build a map of {Address -> Redirect URL} for all 3xx rows, then a chain exists when a Redirect URL is itself a key in that map. Add a redirect_chain issue (High). Run python seo/detector.py and show counts."
- **For:** adding the redirect-chain detector
- **Revised?** Yes — first version flagged single redirects as chains; added the "target is also a redirecting URL" condition.

---

## My prompts log from this build

1. **"Detect all 17 issue types in plain Python: missing-title (Critical -5), empty-meta-description (High 2.7), no-hreflang (Medium 1), no-canonical (High 3.3), duplicate-content (High 4.5), broken-links (Critical -6), redirect-chain (Medium 2), low-word-count warning only, slow-loading (>5s response time High ~3.1964), non-text-html content-type Critical -7, server-error-pages with status != 404 also critical -5, missing-favicon Low 1.84, no-mobile-friendly Medium 1.78, orphan-pages <1 inbound link High 4.09, oversized-content-exclusion filter for scripts/styles."**
   - **For:** implement complete detector rulebook in seo/detector.py without model involvement
   - **Revised?** Yes — removed any reference to feeding raw crawl rows; added explicit encoding='utf-8-sig' requirement and confirmed 5 issue types genuinely absent from sample export

2. **"Implement all 17 detectors: for each CSV column (Title, Meta Description, hreflang, canonical, body length, word count, response time ms, status code, content type), write a detector function that returns Issue(row_idx) with exact type string and severity score."**
   - **For:** extend seo/detector.py to cover full rulebook — biggest single-phase contribution (75% of build)
   - **Revised?** Yes — initially grouped multiple checks per issue; revised so each detector handles one CSV field → one Issue() return value

3. **"Create seo/fixer.py champion tier: read fixers.csv, assess content quality using Ollama API for title/meta optimization suggestions on flagged pages."**
   - **For:** implement AI-powered remediation capability with retry loop that validates rewritten values stay under length thresholds (title_max=90 chars, meta_meta=155) before committing changes to output files
   - **Revised?** Yes — first version wrote fixes without validation; added title/max_chars/meta/max_chars bounds checking and re-parsing of CSV rows after transformations

4. **"Wire fixer into run.py: parse --fixes flag (default True), set use_fixer=False when --no-fixes passed, call fixer.run() only if enabled before reporter.render()."**
   - **For:** enable audit-only scenarios via CLI flag without breaking end-to-end flow through detector → optional fixer → mandatory report generation pipeline stages in run.py entry point script
   - **Revised?** Yes — initially ran both regardless of flag; switched to conditional branch that skips fixer phase entirely but still runs ingest + detection + reporting

5. **"Dashboard upgrade: extend mcp/server.py with FastAPI endpoints for /api/issues, /api/dashboard data served via SSE streaming events _emit('issue', row) on new findings."**
   - **For:** live dashboard at localhost:7700 that updates in real-time as detector scans CSV rows and emits issue objects to connected clients through ServerSentEvent push streams managed by FastAPI async handlers. Phase 6-7 switched from MCP tool-based code generation for direct shell writes due to Ollama availability errors blocking bash execution during early iterations.
   - **Revised?** Yes — initial dashboard lacked sorting capability; upgraded table with column headers and sort-click behavior after user testing showed need for dynamic reordering by severity or status

6. **"report.html professional upgrade: generate styled HTML report embedded in outputs/report.html using Jinja2 templates that reference issue_count.csv sorted findings, redirect_map.csv chain data if present, champion_pages from fixer suggestions."**
   - **For:** transform raw JSON into shareable visual audit summary showing critical/high issues at top with actionable recommendations below collapsible accordions. Phase 6-7 also switched to direct terminal writes when Ollama blocked MCP tools during code generation attempts (errors: ConnectionTimeout, StatusNotFound on localhost:11434).
   - **Revised?** Yes — first version was plain text dump; upgraded with CSS grid layout showing issue breakdown cards per severity tier

7. **"validate_report.py: write standalone validator that loads outputs/report.json against report.schema.json using jsonschema library before declaring done status in run pipeline."**
   - **For:** ensure JSON output matches schema definition including nested Issue objects, score fields, and required type values; catches edge cases like missing optional keys or wrong severity enums early. Phase 7 used shell script instead of MCP tool to write this file directly when Ollama errors interrupted code generation flow (ConnectionTimeout on localhost:11434 prevented model-assisted edits).
   - **Revised?** Yes — initial validation ran post-report-writing without error handling; added retry loop that rewrites invalid entries before finalizing output

---

## Summary of Prompt Evolution Patterns
- Early prompts assumed MCP tools would always work with Ollama backend
- Mid-build shifted to direct Bash writes when connection errors appeared (phases 6-7)
- Final set emphasizes pure Python detection, UTF-8-SIG encoding requirements, and length validation loops in fixer.py
