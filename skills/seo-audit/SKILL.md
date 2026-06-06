# SEO Audit Skill

Orchestrates the full SEO audit pipeline for a Screaming Frog export.

## Sub-agents
- **ingest** (`agents/ingest.md`) — loads `internal_all.csv`, validates encoding, returns row count
- **auditor** (`agents/auditor.md`) — runs all 17 deterministic detectors, returns issues sorted by severity
- **fixer** (`agents/fixer.md`) — champion tier: rewrites bad titles/metas via Ollama, builds redirect map for 404s
- **reporter** (`agents/reporter.md`) — writes `outputs/report.json` (schema-validated) and `outputs/report.html`

## Usage
## Pipeline flow
CSV load → 17 detectors → optional AI fixer → report.json + report.html

## Issue severity tiers
- **High**: missing_title, duplicate_title, broken_link, server_error, redirect_chain
- **Medium**: missing_meta_description, duplicate_meta_description, missing_h1, redirect, orphan_page, non_indexable_but_linked
- **Low**: title_too_long, title_too_short, meta_description_too_long, duplicate_h1, thin_content, slow_page

## Hard rules
- Detection in plain Python only — never feed raw rows to the model
- Filter to text/html + status 200 + indexable before title/meta checks
- All CSV reads use `encoding="utf-8-sig"` (Screaming Frog BOM)
- report.json must pass `validate_report.py` before declaring done
