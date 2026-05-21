from datetime import datetime
import pytz
import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

eastern = pytz.timezone("America/New_York")
timezone_time = datetime.now(eastern).isoformat()

URLS = {
    "fame": "https://leaderboards.arcaneodyssey.dev/fame",
    "bounty": "https://leaderboards.arcaneodyssey.dev/bounty",
    "grand_navy": "https://leaderboards.arcaneodyssey.dev/grand-navy",
    "assassin_syndicate": "https://leaderboards.arcaneodyssey.dev/assassin-syndicate",
}

headers = {
    "User-Agent": "Mozilla/5.0"
}


def extract_text(el):
    return el.get_text(" ", strip=True) if el else None


def scrape_board(url):
    res = requests.get(url, headers=headers, timeout=20)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    rows = []

    # 🔥 KEY FIX: look for ANY repeated “row-like” containers
    # These sites usually use div-based leaderboard rows
    candidates = soup.find_all("div")

    for c in candidates:
        text = c.get_text(" ", strip=True)

        # filter out useless blocks
        if not text or len(text) < 5:
            continue

        # heuristic: leaderboard rows usually contain numbers + name
        parts = text.split()

        if len(parts) < 2:
            continue

        # try to detect a name + number pattern
        name = None
        number = None

        for p in parts:
            if p.isdigit():
                number = int(p)
                break

        # crude but effective fallback:
        # assume last word is name if mixed content
        name = parts[-1]

        if name and number is not None:
            rows.append({
                "name": name,
                "renown": number,
                "renown_change": 0
            })

    # remove duplicates (VERY important for div scraping)
    seen = set()
    clean = []
    for r in rows:
        key = (r["name"], r["renown"])
        if key not in seen:
            seen.add(key)
            clean.append(r)

    return clean


def upload(rows):
    if not rows:
        print("No rows to upload")
        return

    for r in rows:
        supabase.table("leaderboard").upsert({
            "name": r["name"],
            "renown": r["renown"],
            "renown_change": r["renown_change"],
            "timezone_time": timezone_time
        }).execute()

    print(f"Uploaded {len(rows)} rows")


def main():
    all_rows = []

    for name, url in URLS.items():
        print(f"Scraping {name}...")
        rows = scrape_board(url)
        print(f"{name}: {len(rows)} rows scraped")
        all_rows.extend(rows)

    upload(all_rows)
    print("done")


if __name__ == "__main__":
    main()
