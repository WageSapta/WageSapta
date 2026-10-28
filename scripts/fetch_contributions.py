"""Scrape the public contribution calendar (no token) into data/contributions.json."""

import json
import re
from collections import OrderedDict
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

from common import load_config, resolve

TOOLTIP = re.compile(r"(No|[\d,]+) contribution")


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    counts = {
        tip.get("for"): TOOLTIP.match(tip.get_text().strip()).group(1)
        for tip in soup.find_all("tool-tip")
        if tip.get("for") and TOOLTIP.match(tip.get_text().strip())
    }

    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        raw = counts.get(cell.get("id"), "")
        count = 0 if raw in (None, "", "No") else int(raw.replace(",", ""))
        days.append(
            {
                "date": cell["data-date"],
                "level": int(cell.get("data-level", "0")),
                "count": count,
            }
        )
    return days


def current_streak(days):
    """Consecutive active days ending today; an unfinished today does not break it."""
    ordered = sorted(days, key=lambda d: d["date"])
    run = 0
    for i, day in enumerate(reversed(ordered)):
        if day["count"] > 0:
            run += 1
        elif i == 0:
            continue
        else:
            break
    return run


def streaks(days):
    active = sorted((d for d in days if d["count"] > 0), key=lambda d: d["date"])
    if not active:
        return {"current": 0, "longest": 0, "last_active": None, "best": None}

    dates = [datetime.strptime(d["date"], "%Y-%m-%d").date() for d in active]
    longest = run = 1
    for prev, cur in zip(dates, dates[1:]):
        run = run + 1 if (cur - prev).days == 1 else 1
        longest = max(longest, run)

    best = max(active, key=lambda d: d["count"])
    return {
        "current": current_streak(days),
        "longest": longest,
        "last_active": active[-1]["date"],
        "best": {"date": best["date"], "count": best["count"]},
    }


def monthly(days):
    totals = OrderedDict()
    for d in days:
        key = d["date"][:7]
        totals[key] = totals.get(key, 0) + d["count"]
    return [{"month": k, "count": v} for k, v in totals.items()]


def main():
    cfg = load_config()
    user = cfg["github_user"]
    res = requests.get(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "Mozilla/5.0 (profile-readme fetch)"},
        timeout=30,
    )
    res.raise_for_status()

    days = parse(res.text)
    if not days:
        raise SystemExit(f"no contribution cells found for {user}")
    days.sort(key=lambda d: d["date"])

    payload = {
        "user": user,
        "fetched_at": date.today().isoformat(),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "total": sum(d["count"] for d in days),
        "days": days,
        "stats": streaks(days),
        "monthly": monthly(days),
    }
    out = resolve(cfg["heatmap"]["data"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(
        f"wrote {cfg['heatmap']['data']}: {payload['total']} contributions, "
        f"{len(days)} days, streak {payload['stats']['current']}/{payload['stats']['longest']}"
    )


if __name__ == "__main__":
    main()
