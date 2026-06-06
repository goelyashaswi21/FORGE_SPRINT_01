import json, sys

def validate():
    try:
        r = json.load(open("outputs/report.json", encoding="utf-8"))
    except FileNotFoundError:
        print("FAIL: outputs/report.json not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"FAIL: invalid JSON — {e}")
        sys.exit(1)

    # Check top-level fields
    for field in ("site", "urls_crawled", "summary", "issues", "run_meta"):
        if field not in r:
            print(f"FAIL: missing top-level field: {field}")
            sys.exit(1)

    if not isinstance(r["site"], str):
        print("FAIL: site must be a string")
        sys.exit(1)
    if not isinstance(r["urls_crawled"], int):
        print("FAIL: urls_crawled must be an int")
        sys.exit(1)

    # Check summary
    s = r["summary"]
    if not isinstance(s.get("total_issues"), int):
        print("FAIL: summary.total_issues must be an int")
        sys.exit(1)
    bysev = s.get("by_severity", {})
    for k in ("High", "Medium", "Low"):
        if not isinstance(bysev.get(k, 0), int):
            print(f"FAIL: summary.by_severity.{k} must be an int")
            sys.exit(1)

    # Check every issue
    for idx, issue in enumerate(r["issues"]):
        for f in ("type", "severity", "affected_urls", "count"):
            if f not in issue:
                print(f"FAIL: issues[{idx}] missing field: {f}")
                sys.exit(1)
        if issue["severity"] not in ("High", "Medium", "Low"):
            print(f"FAIL: issues[{idx}].severity invalid: {issue['severity']}")
            sys.exit(1)
        if not isinstance(issue["affected_urls"], list):
            print(f"FAIL: issues[{idx}].affected_urls must be a list")
            sys.exit(1)
        if not isinstance(issue["count"], int):
            print(f"FAIL: issues[{idx}].count must be an int")
            sys.exit(1)

    # Check run_meta
    rm = r.get("run_meta", {})
    if not isinstance(rm.get("model_calls", 0), int):
        print("FAIL: run_meta.model_calls must be an int")
        sys.exit(1)

    # Check fixes if present
    if "fixes" in r:
        if not isinstance(r["fixes"].get("titles", []), list):
            print("FAIL: fixes.titles must be a list")
            sys.exit(1)
        if not isinstance(r["fixes"].get("redirect_map", []), list):
            print("FAIL: fixes.redirect_map must be a list")
            sys.exit(1)

    print(f"PASS — {r['site']}, {r['urls_crawled']} URLs, "
          f"{len(r['issues'])} issue types, {s['total_issues']} total issues")

validate()
