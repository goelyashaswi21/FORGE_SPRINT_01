"""
seo/fixer.py — champion-tier AI fixes using local Ollama model.
"""
import json
import urllib.request


def build_rows_index(rows):
    """Return {Address: row dict} for fast lookup."""
    return {r["Address"]: r for r in rows if "Address" in r}


def _call_ollama(prompt: str) -> str:
    payload = json.dumps({
        "model": "qwen3.5:9b",
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 80, "temperature": 0.3}
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
            return result.get("response", "").strip()
    except Exception:
        return ""


def _best_match(broken_url, live_pages):
    if not live_pages:
        return ""
    broken_parts = broken_url.rstrip("/").split("/")
    best_url, best_score = live_pages[0], -1
    for page in live_pages:
        parts = page.rstrip("/").split("/")
        score = sum(1 for a, b in zip(reversed(broken_parts), reversed(parts)) if a == b)
        if score > best_score:
            best_score, best_url = score, page
    return best_url


def run_fixes(issues, rows):
    idx = build_rows_index(rows)
    titles = []
    redirect_map = []
    model_calls = 0
    URL_LIMIT = 20

    for issue in issues:
        if issue["type"] in ("missing_title", "title_too_long"):
            for url in issue["affected_urls"][:URL_LIMIT]:
                row = idx.get(url, {})
                old_title = row.get("Title 1", "")
                h1 = row.get("H1-1", "")
                new_title = _call_ollama(
                    f"Write an SEO page title for this page. Max 60 characters. "
                    f"Return ONLY the title, nothing else.\n"
                    f"URL: {url}\nH1: {h1}\nCurrent title: {old_title}"
                )
                model_calls += 1
                if len(new_title) > 60:
                    new_title = _call_ollama(
                        f"Shorten this SEO title to under 60 characters. "
                        f"Return ONLY the shortened title, nothing else.\nTitle: {new_title}"
                    )
                    model_calls += 1
                if new_title:
                    titles.append({"url": url, "old": old_title, "new": new_title})

        if issue["type"] in ("missing_meta_description", "meta_description_too_long"):
            for url in issue["affected_urls"][:URL_LIMIT]:
                row = idx.get(url, {})
                old_meta = row.get("Meta Description 1", "")
                title = row.get("Title 1", "")
                h1 = row.get("H1-1", "")
                new_meta = _call_ollama(
                    f"Write an SEO meta description for this page. Max 155 characters. "
                    f"Return ONLY the description, nothing else.\n"
                    f"URL: {url}\nTitle: {title}\nH1: {h1}"
                )
                model_calls += 1
                if len(new_meta) > 155:
                    new_meta = _call_ollama(
                        f"Shorten this meta description to under 155 characters. "
                        f"Return ONLY the shortened description, nothing else.\n"
                        f"Description: {new_meta}"
                    )
                    model_calls += 1
                if new_meta:
                    titles.append({"url": url, "old": old_meta, "new": new_meta})

    for issue in issues:
        if issue["type"] == "broken_link":
            live_pages = [
                r["Address"] for r in rows
                if str(r.get("Status Code", "")) == "200"
                and r.get("Indexability", "") == "Indexable"
            ]
            for url in issue["affected_urls"][:URL_LIMIT]:
                best = _best_match(url, live_pages)
                if best:
                    redirect_map.append({
                        "from": url,
                        "to": best,
                        "reason": "404 -> closest live page by path similarity"
                    })

    return {"titles": titles, "redirect_map": redirect_map, "model_calls": model_calls}
