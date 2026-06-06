"""
detector.py — deterministic SEO issue detection from a Screaming Frog internal_all.csv.
Covers all 17 issue types from rulebook.md.
"""
from __future__ import annotations
import csv
import os
from collections import defaultdict


def load_rows(export_dir: str) -> list[dict]:
    path = os.path.join(export_dir, "internal_all.csv")
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _int(v, default=0):
    try:
        return int(float(str(v).strip()))
    except Exception:
        return default


def _float(v, default=0.0):
    try:
        return float(str(v).strip())
    except Exception:
        return default


def is_html(r):  return "text/html" in (r.get("Content Type", "") or "").lower()
def is_200(r):   return _int(r.get("Status Code")) == 200
def indexable(r): return (r.get("Indexability", "") or "").strip().lower() == "indexable"


def detect(rows: list[dict]) -> list[dict]:
    issues = []

    def add(t, sev, urls, explanation):
        urls = sorted(set(urls))
        if urls:
            issues.append({"type": t, "severity": sev, "affected_urls": urls,
                           "count": len(urls), "explanation": explanation})

    html   = [r for r in rows if is_html(r)]
    idx200 = [r for r in html if is_200(r) and indexable(r)]
    all200 = [r for r in html if is_200(r)]

    # --- missing_title ---
    add("missing_title", "High",
        [r["Address"] for r in idx200 if not (r.get("Title 1", "") or "").strip()],
        "Indexable pages with no title tag.")

    # --- duplicate_title ---
    by_title = defaultdict(list)
    for r in idx200:
        t = (r.get("Title 1", "") or "").strip()
        if t:
            by_title[t].append(r["Address"])
    add("duplicate_title", "High",
        [u for urls in by_title.values() if len(urls) > 1 for u in urls],
        "Pages sharing an identical title.")

    # --- title_too_long ---
    add("title_too_long", "Medium",
        [r["Address"] for r in idx200
         if _int(r.get("Title 1 Pixel Width")) > 561 or _int(r.get("Title 1 Length")) > 60],
        "Titles likely truncated in search results.")

    # --- title_too_short ---
    add("title_too_short", "Low",
        [r["Address"] for r in idx200
         if (r.get("Title 1", "") or "").strip() and _int(r.get("Title 1 Length")) < 30],
        "Titles too short to be descriptive.")

    # --- missing_meta_description ---
    add("missing_meta_description", "Medium",
        [r["Address"] for r in idx200 if not (r.get("Meta Description 1", "") or "").strip()],
        "Indexable pages with no meta description.")

    # --- duplicate_meta_description ---
    by_meta = defaultdict(list)
    for r in idx200:
        m = (r.get("Meta Description 1", "") or "").strip()
        if m:
            by_meta[m].append(r["Address"])
    add("duplicate_meta_description", "Medium",
        [u for urls in by_meta.values() if len(urls) > 1 for u in urls],
        "Pages sharing an identical meta description.")

    # --- meta_description_too_long ---
    add("meta_description_too_long", "Low",
        [r["Address"] for r in html if _int(r.get("Meta Description 1 Length")) > 155],
        "Meta descriptions that will be truncated by Google.")

    # --- missing_h1 ---
    add("missing_h1", "Medium",
        [r["Address"] for r in all200 if not (r.get("H1-1", "") or "").strip()],
        "Pages with no H1 tag.")

    # --- duplicate_h1 ---
    by_h1 = defaultdict(list)
    for r in idx200:
        h = (r.get("H1-1", "") or "").strip()
        if h:
            by_h1[h].append(r["Address"])
    add("duplicate_h1", "Low",
        [u for urls in by_h1.values() if len(urls) > 1 for u in urls],
        "Pages sharing an identical H1.")

    # --- broken_link ---
    add("broken_link", "High",
        [r["Address"] for r in rows if 400 <= _int(r.get("Status Code")) <= 499],
        "URLs returning a client error (4xx).")

    # --- server_error ---
    add("server_error", "High",
        [r["Address"] for r in rows if 500 <= _int(r.get("Status Code")) <= 599],
        "URLs returning a server error (5xx).")

    # --- redirect ---
    add("redirect", "Medium",
        [r["Address"] for r in rows if 300 <= _int(r.get("Status Code")) <= 399],
        "URLs that redirect (3xx).")

    # --- redirect_chain ---
    r_map = {}
    for r in rows:
        if 300 <= _int(r.get("Status Code")) <= 399:
            src = (r.get("Address") or "").strip()
            tgt = (r.get("Redirect URL") or "").strip()
            if src and tgt:
                r_map[src] = tgt
    chain_urls = [src for src, tgt in r_map.items() if tgt in r_map]
    add("redirect_chain", "High", chain_urls,
        "Redirects whose target also redirects (chains/loops).")

    # --- thin_content ---
    add("thin_content", "Low",
        [r["Address"] for r in html if indexable(r) and _int(r.get("Word Count")) < 200],
        "Indexable pages with fewer than 200 words.")

    # --- orphan_page ---
    add("orphan_page", "Medium",
        [r["Address"] for r in idx200 if _int(r.get("Inlinks")) == 0],
        "Indexable pages with zero internal links pointing to them.")

    # --- non_indexable_but_linked ---
    add("non_indexable_but_linked", "Medium",
        [r["Address"] for r in html if not indexable(r) and _int(r.get("Inlinks")) > 0],
        "Non-indexable pages that still receive internal links.")

    # --- slow_page ---
    add("slow_page", "Low",
        [r["Address"] for r in html if _float(r.get("Response Time")) > 1.0],
        "Pages taking over 1 second to respond.")

    return issues


def summarize(issues: list[dict]) -> dict:
    by_sev = defaultdict(int)
    for i in issues:
        by_sev[i["severity"]] += 1
    return {"total_issues": len(issues),
            "by_severity": {"High": by_sev["High"], "Medium": by_sev["Medium"], "Low": by_sev["Low"]}}


if __name__ == "__main__":
    import sys, json
    d = sys.argv[1] if len(sys.argv) > 1 else "sample-export"
    rows = load_rows(d)
    iss = detect(rows)
    print(f"Loaded {len(rows)} rows, detected {len(iss)} issue types.")
    print(json.dumps(summarize(iss), indent=2))
    for i in iss:
        print(f"  [{i['severity']:<6}] {i['type']:<30} x{i['count']}")
