#!/usr/bin/env python3
"""
EYC Results Scraper
Fetches the EYC results directory, finds all 2026 result pages,
categorises them, and writes results.json for the PWA to consume.

Run automatically by GitHub Actions every 6 hours.
"""

import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone

RESULTS_BASE = "https://www.essexyachtclub.co.uk/results/"
OUTPUT_FILE  = "results.json"
YEAR         = "2026"

# ── Category rules ────────────────────────────────────────────────────────────
# Each category has:
#   id        - matches the resultsTab in the PWA
#   label     - display name
#   emoji     - shown in the tab
#   patterns  - list of lowercase substrings; first match wins
CATEGORIES = [
    {
        "id": "bfleet",
        "label": "B Fleet",
        "emoji": "⛵",
        "patterns": ["b fleet", "b_fleet"],
    },
    {
        "id": "eod",
        "label": "EOD",
        "emoji": "🚤",
        "patterns": [
            "eod", "forward hands", "tony moore", "ian perkins",
            "edwards casket", "velsheda", "symons", "peter cotgrove",
            "mini shoreline", "estuary", "turmaine",
        ],
    },
    {
        "id": "cruiser",
        "label": "Cruiser",
        "emoji": "⚓",
        "patterns": ["cruiser", "inshore points", "kelvin hughes", "nore race",
                     "river race", "commodore"],
    },
    {
        "id": "trophy",
        "label": "Trophy Races",
        "emoji": "🏆",
        "patterns": ["trophy", "cup", "championship", "champs", "series",
                     "pursuit", "flower race", "summer", "autumn", "winter",
                     "spring", "easter", "bank holiday"],
    },
]

def fetch_html(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "EYC-PWA-ResultsBot/1.0 (github-actions)"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
        # Try UTF-8 then latin-1
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1")

def categorise(filename):
    """Return category id for a filename, or 'other'."""
    name_lower = filename.lower()
    for cat in CATEGORIES:
        if any(p in name_lower for p in cat["patterns"]):
            return cat["id"]
    return "trophy"   # default catch-all

def friendly_name(filename):
    """
    'B%20Fleet%20Spring%20Series%202026.htm'
    -> 'B Fleet Spring Series'
    """
    name = urllib.parse.unquote(filename)          # decode %20 etc.
    name = re.sub(r'\.htm[l]?$', '', name, flags=re.I)  # strip extension
    name = re.sub(r'\s*' + YEAR + r'\s*', ' ', name).strip()  # strip year
    return name

# We need unquote — import it properly
import urllib.parse

def main():
    print(f"[scraper] Fetching results directory: {RESULTS_BASE}")
    try:
        html = fetch_html(RESULTS_BASE)
    except Exception as e:
        print(f"[scraper] ERROR fetching directory: {e}")
        # Write an empty-but-valid results.json so the PWA doesn't break
        output = {
            "updated": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "categories": []
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(output, f, indent=2)
        return

    # Find all .htm links that contain the current year
    raw_links = re.findall(
        r'href=["\']([^"\']*' + YEAR + r'[^"\']*\.htm)["\']',
        html,
        re.IGNORECASE
    )

    # Deduplicate, make absolute, ignore anchors
    seen = set()
    results = []
    for link in raw_links:
        # Make absolute
        if link.startswith("http"):
            url = link
        elif link.startswith("/"):
            url = "https://www.essexyachtclub.co.uk" + link
        else:
            url = RESULTS_BASE + link

        # Extract just the filename for categorisation
        filename = url.split("/")[-1]
        if filename in seen:
            continue
        seen.add(filename)

        cat_id   = categorise(filename)
        name     = friendly_name(filename)

        results.append({
            "name":     name,
            "url":      url,
            "filename": filename,
            "category": cat_id,
        })
        print(f"[scraper]   {cat_id:10s}  {name}")

    # Group by category, preserving CATEGORIES order
    cat_map = {}
    for r in results:
        cat_map.setdefault(r["category"], []).append(r)

    categories_out = []
    for cat in CATEGORIES:
        items = cat_map.get(cat["id"], [])
        # Sort alphabetically within each category
        items.sort(key=lambda x: x["name"])
        categories_out.append({
            "id":    cat["id"],
            "label": cat["label"],
            "emoji": cat["emoji"],
            "results": items,
        })

    # Also include anything that fell into 'other' (shouldn't happen with catch-all)
    if "other" in cat_map:
        categories_out.append({
            "id":      "other",
            "label":   "Other",
            "emoji":   "📋",
            "results": cat_map["other"],
        })

    output = {
        "updated":    datetime.now(timezone.utc).isoformat(),
        "year":       YEAR,
        "categories": categories_out,
        "total":      len(results),
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[scraper] Done. {len(results)} results written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
