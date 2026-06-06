"""
run.py — headless runner for the SEO Command Center (also the grader's entry point).
Runs the full pipeline on a Screaming Frog export with no Claude Code:
  load -> detect -> (starter recommendations) -> write report.json + report.html
Usage:
  python run.py sample-export/
  python run.py sample-export/ --no-fixes
  python run.py sample-export/ --no-dashboard
"""
from __future__ import annotations
import argparse, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "mcp"))
sys.path.insert(0, HERE)
import server

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export_dir")
    ap.add_argument("--no-dashboard", action="store_true")
    ap.add_argument("--no-fixes", action="store_true")
    args = ap.parse_args()

    if not args.no_dashboard:
        server.start_dashboard()
        print(f"[seo] dashboard: http://localhost:{server.PORT}", flush=True)
        time.sleep(1)

    t0 = time.time()
    server.seo_load(args.export_dir)
    res = server.seo_detect()

    # Champion tier: AI-powered fixes (only when --no-fixes is NOT set)
    if not args.no_fixes:
        try:
            from seo import fixer as seo_fixer
            print("[seo] running AI fixer (titles, metas, redirects)...", flush=True)
            fix_result = seo_fixer.run_fixes(server.RUN["issues"], server.RUN.get("rows", []))
            server.seo_set_fixes(fix_result["titles"], fix_result["redirect_map"])
            server.RUN["model_calls"] = fix_result.get("model_calls", 0)
            print(f"[seo] fixes: {len(fix_result['titles'])} title rewrites, {len(fix_result['redirect_map'])} redirects", flush=True)
        except Exception as e:
            print(f"[seo] fixer skipped: {e}", flush=True)
            server.RUN["model_calls"] = 0
    else:
        print("[seo] fixes skipped (--no-fixes)", flush=True)
        server.RUN["model_calls"] = 0

    issues = sorted(server.RUN["issues"], key=lambda x: {"High":0,"Medium":1,"Low":2}.get(x["severity"],3))
    recs = []
    for i in issues[:5]:
        recs.append(f"Fix the {i['count']} {i['severity']}-severity '{i['type']}' issue(s) first.")
    if not recs:
        recs.append("No issues detected on this crawl.")
    server.seo_recommend(recs)
    server.RUN["duration_sec"] = round(time.time() - t0, 1)
    server.seo_report()
    server.seo_export()
    s = server.RUN["summary"]
    print("\n=== SEO AUDIT RESULT ===")
    print(f"Site         : {server.RUN['site']}  ({server.RUN['urls']} URLs)")
    print(f"Total issues : {s['total_issues']}  (High {s['by_severity'].get('High',0)} / "
          f"Medium {s['by_severity'].get('Medium',0)} / Low {s['by_severity'].get('Low',0)})")
    print("Wrote outputs/report.json and outputs/report.html")

if __name__ == "__main__":
    main()
