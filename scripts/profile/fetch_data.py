#!/usr/bin/env python3
"""
Collect everything the README cards need into data/profile.json.

Stdlib only. Works unauthenticated (local preview, ~25 requests) and with
GITHUB_TOKEN inside the Action (higher rate limit). No PAT, no Vercel.

  * contribution calendar -> scraped per year from github.com/users/<u>/contributions
    (same fragment the profile page renders; includes private counts if the
    "Private contributions" profile setting is on)
  * stars / commits / PRs / issues / contributed-to -> REST + search API
  * top languages -> bytes per language over owned, non-fork repos
  * projects -> projects.json merged with live stars / languages / pushed_at
"""
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

USER = os.environ.get("GH_PROFILE_USER", "Tguleryuz52")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EXCLUDE_LANG_REPOS = {
    USER.lower(),                                  # profile repo: its generators would skew "Python"
    "https-github.com-tguleryuz52-portfolio-v2",   # committed build output (6 MB of bundled JS)
}


def get(url, raw=False):
    headers = {"User-Agent": "tguleryuz52-profile", "Accept": "application/vnd.github+json"}
    if TOKEN and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {TOKEN}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
                body = r.read().decode("utf-8")
                return body if raw else json.loads(body)
        except Exception as e:  # noqa: BLE001 - network flakiness, retry then give up
            if attempt == 2:
                raise
            print(f"retry {url}: {e}", file=sys.stderr)
            time.sleep(3 * (attempt + 1))


def search_count(q):
    return get("https://api.github.com/search/issues?per_page=1&q=" + urllib.parse.quote(q))["total_count"]


# ---------------------------------------------------------------- calendar
DAY_RE = re.compile(r'data-date="(\d{4}-\d{2}-\d{2})" id="([^"]+)"')
TIP_RE = re.compile(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>')


def calendar_year(year):
    html = get(f"https://github.com/users/{USER}/contributions?from={year}-01-01&to={year}-12-31", raw=True)
    tips = {cid: txt for cid, txt in TIP_RE.findall(html)}
    days = {}
    for date, cid in DAY_RE.findall(html):
        m = re.match(r"\s*(\d+)", tips.get(cid, ""))
        days[date] = int(m.group(1)) if m else 0
    return days


def streaks(days, created):
    today = dt.date.today()
    dates = sorted(d for d in days if created <= d <= today.isoformat())
    total = sum(days[d] for d in dates)

    longest, run, run_start, best = 0, 0, None, (None, None)
    for d in dates:
        if days[d] > 0:
            run_start = run_start or d
            run += 1
            if run > longest:
                longest, best = run, (run_start, d)
        else:
            run, run_start = 0, None

    cur, end = 0, today
    if days.get(end.isoformat(), 0) == 0:       # today not over yet: keep yesterday's streak alive
        end -= dt.timedelta(days=1)
    start = end
    while days.get((start).isoformat(), 0) > 0:
        cur += 1
        start -= dt.timedelta(days=1)
    start += dt.timedelta(days=1)
    return {
        "total": total, "first_day": created,
        "current": cur, "current_range": [start.isoformat(), end.isoformat()] if cur else [today.isoformat()] * 2,
        "longest": longest, "longest_range": list(best) if longest else [created, created],
    }


# ---------------------------------------------------------------- main
def main():
    user = get(f"https://api.github.com/users/{USER}")
    created = user["created_at"][:10]
    days = {}
    for year in range(int(created[:4]), dt.date.today().year + 1):
        days.update(calendar_year(year))

    repos = get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    own = [r for r in repos if not r["fork"]]
    langs, repo_langs = {}, {}
    for r in own:
        repo_langs[r["full_name"].lower()] = get(r["languages_url"])
        if r["name"].lower() in EXCLUDE_LANG_REPOS:
            continue
        for k, v in repo_langs[r["full_name"].lower()].items():
            langs[k] = langs.get(k, 0) + v

    year_ago = (dt.date.today() - dt.timedelta(days=365)).isoformat()
    commits = get("https://api.github.com/search/commits?per_page=1&q=" + urllib.parse.quote(f"author:{USER}"))["total_count"]
    recent = get("https://api.github.com/search/commits?per_page=100&q="
                 + urllib.parse.quote(f"author:{USER} author-date:>={year_ago}"))
    contributed = {i["repository"]["full_name"] for i in recent.get("items", [])}
    stats = {
        "name": user.get("name") or USER,
        "stars": sum(r["stargazers_count"] for r in own),
        "commits": commits,
        "prs": search_count(f"author:{USER} type:pr"),
        "issues": search_count(f"author:{USER} type:issue"),
        "contributed_to": len(contributed),
        "public_repos": len(own),
        "languages_used": len(langs),
        "top_language": max(langs, key=langs.get) if langs else "n/a",
    }

    with open(os.path.join(ROOT, "projects.json"), encoding="utf-8") as fh:
        projects = json.load(fh)
    for p in projects:
        repo = (p.get("repo") or "").replace("https://github.com/", "").strip("/")
        p["repo"] = repo
        if not repo:                      # private / unreleased project: card from config only
            continue
        try:
            info = get(f"https://api.github.com/repos/{repo}")
            p["stars"] = info["stargazers_count"]
            p["pushed_at"] = info["pushed_at"]
            p.setdefault("description", info.get("description") or "")
            p["languages"] = repo_langs.get(repo.lower()) or get(info["languages_url"])
        except Exception as e:  # noqa: BLE001 - keep the card, drop live data
            print(f"warn: {repo}: {e}", file=sys.stderr)

    out = {
        "user": USER,
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "streak": streaks(days, created),
        "stats": stats,
        "languages": langs,
        "projects": projects,
        "days": [{"date": d, "count": days[d]} for d in sorted(days) if d <= dt.date.today().isoformat()],
    }
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "profile.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    s = out["streak"]
    print(f"ok: {s['total']} contributions, streak {s['current']} / longest {s['longest']}, "
          f"{len(langs)} languages, {len(projects)} projects")


if __name__ == "__main__":
    main()
