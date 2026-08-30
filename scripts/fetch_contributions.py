#!/usr/bin/env python3
"""
Scrape real daily contribution counts from GitHub's public, unauthenticated
contributions endpoint (the same fragment the profile page itself uses) and
write data/contributions.json with raw days plus derived stats.
"""
import datetime
import json
import os
import re
import sys
import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "Tguleryuz52")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")

def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        print("no calendar cells found -- github markup may have changed", file=sys.stderr)
        sys.exit(1)

    days = []
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        td_id = td.get("id")
        tooltip_el = soup.find("tool-tip", attrs={"for": td_id}) if td_id else None
        text = tooltip_el.get_text(strip=True) if tooltip_el else ""
        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            m = re.match(r"(\d+)", text)
            count = int(m.group(1)) if m else 0
        days.append({"date": date, "count": count})

    days.sort(key=lambda d: d["date"])
    return days

def compute_current_streak(days):
    today = datetime.date.today().isoformat()
    by_date = {d["date"]: d["count"] for d in days}
    streak = 0
    cur = datetime.date.today()
    if by_date.get(cur.isoformat(), 0) == 0:
        cur -= datetime.timedelta(days=1)
    while True:
        s = cur.isoformat()
        if by_date.get(s, 0) > 0:
            streak += 1
            cur -= datetime.timedelta(days=1)
        else:
            break
    return streak

def compute_longest_streak(days):
    longest = 0
    cur = 0
    for d in days:
        if d["count"] > 0:
            cur += 1
            if cur > longest:
                longest = cur
        else:
            cur = 0
    return longest

def main():
    days = fetch_days()
    total = sum(d["count"] for d in days)
    best_day = max(days, key=lambda d: d["count"]) if days else {"date": None, "count": 0}
    current_streak = compute_current_streak(days)
    longest_streak = compute_longest_streak(days)

    out = {
        "username": USERNAME,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "days": days,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"saved {len(days)} days ({total} total contributions) to {OUT_PATH}")

if __name__ == "__main__":
    main()
