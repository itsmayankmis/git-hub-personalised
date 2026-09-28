#!/usr/bin/env python3
"""
fetch_contributions.py
Scrapes GitHub's public contribution graph HTML fragment for a given user,
extracts daily contribution counts and levels, calculates streak & summary statistics,
and saves the result to data/contributions.json.
"""

import sys
import os
import json
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "itsmayankmis"

def fetch_contributions(username: str):
    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        print(f"Error: Failed to fetch contributions for user '{username}'. HTTP status: {resp.status_code}", file=sys.stderr)
        sys.exit(1)
        
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # 1. Parse tooltips mapping id -> count
    tooltips = {}
    for tt in soup.find_all(["tool-tip", "div"], attrs={"for": True}):
        for_id = tt.get("for")
        text = tt.get_text(strip=True)
        # Patterns like: "No contributions on September 28th." or "1 contribution on September 29th." or "12 contributions on ..."
        if "No contributions" in text:
            count = 0
        else:
            match = re.search(r"(\d[\d,]*)\s+contribution", text)
            if match:
                count = int(match.group(1).replace(",", ""))
            else:
                count = 0
        tooltips[for_id] = count

    # 2. Parse day cells
    day_cells = soup.find_all("td", class_="ContributionCalendar-day")
    if not day_cells:
        print(f"Error: No contribution calendar days found in response for '{username}'.", file=sys.stderr)
        sys.exit(1)
        
    days = []
    for cell in day_cells:
        date_str = cell.get("data-date")
        if not date_str:
            continue
            
        level_str = cell.get("data-level", "0")
        try:
            level = int(level_str)
        except ValueError:
            level = 0
            
        cell_id = cell.get("id")
        count = tooltips.get(cell_id, 0)
        
        # If tooltip didn't match directly, try finding inner or aria-label text if present
        if cell_id not in tooltips and cell.get("aria-label"):
            aria = cell.get("aria-label")
            if "No contributions" in aria:
                count = 0
            else:
                m = re.search(r"(\d[\d,]*)\s+contribution", aria)
                count = int(m.group(1).replace(",", "")) if m else 0

        days.append({
            "date": date_str,
            "count": count,
            "level": level
        })
        
    if not days:
        print(f"Error: Extracted 0 valid days for '{username}'.", file=sys.stderr)
        sys.exit(1)
        
    # Sort chronologically by date
    days.sort(key=lambda d: d["date"])
    
    # 3. Extract total from header
    total = None
    h2 = soup.find("h2")
    if h2:
        h2_text = " ".join(h2.get_text().split())
        match = re.search(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", h2_text, re.IGNORECASE)
        if match:
            total = int(match.group(1).replace(",", ""))
            
    sum_counts = sum(d["count"] for d in days)
    if total is None:
        total = sum_counts

    # 4. Calculate streak stats
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    best_day = {"date": days[0]["date"], "count": days[0]["count"]}
    monthly_totals = {}
    
    for d in days:
        c = d["count"]
        # Best day
        if c > best_day["count"]:
            best_day = {"date": d["date"], "count": c}
            
        # Monthly totals
        month_key = d["date"][:7] # YYYY-MM
        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + c
        
        # Streak tracking
        if c > 0:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0

    # Current streak calculation (looking backwards from the end)
    # Note: today might be 0 yet, allow grace for today if yesterday was active
    idx = len(days) - 1
    if idx >= 0 and days[idx]["count"] == 0 and idx > 0 and days[idx - 1]["count"] > 0:
        # Check if the last day is today
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if days[idx]["date"] == today_str:
            idx -= 1
            
    while idx >= 0 and days[idx]["count"] > 0:
        current_streak += 1
        idx -= 1

    result = {
        "username": username,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "days": days,
        "stats": {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "best_day": best_day,
            "monthly_totals": monthly_totals
        }
    }
    return result

def main():
    username = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_USERNAME", DEFAULT_USERNAME)
    print(f"Fetching contributions for '{username}'...")
    data = fetch_contributions(username)
    
    os.makedirs("data", exist_ok=True)
    out_file = "data/contributions.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    print(f"Successfully wrote {len(data['days'])} days to {out_file}.")
    print(f"Total: {data['total']} contributions | Longest streak: {data['stats']['longest_streak']} | Best day: {data['stats']['best_day']['date']} ({data['stats']['best_day']['count']})")

if __name__ == "__main__":
    main()
