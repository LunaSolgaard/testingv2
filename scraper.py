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
now = datetime.now(eastern)

# PostgreSQL timestampz-friendly format
timezone_time = now.isoformat()

URLS = {
    "fame": "https://leaderboards.arcaneodyssey.dev/fame",
    "bounty": "https://leaderboards.arcaneodyssey.dev/bounty",
    "grand_navy": "https://leaderboards.arcaneodyssey.dev/grand-navy",
    "assassin_syndicate": "https://leaderboards.arcaneodyssey.dev/assassin-syndicate",
}

headers = {
    "User-Agent": "Mozilla/5.0"
}


def to_int(value):
    """Safely convert scraped numbers like '1,234' -> 1234"""
    try:
        return int(value.replace(",", "").strip())
    except:
        return None


def scrape_board(url):
    res = requests.get(url, headers=headers, timeout=20)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    rows = []

    for tr in soup.find_all("tr"):
        cols = tr.find_all("td")

        if len(cols) < 3:
            continue

        try:
            rank_text = cols[0].get_text(strip=True)
            name = cols[1].get_text(strip=True)
            value_text = cols[2].get_text(strip=True)

            rank = to_int(rank_text)
            value = to_int(value_text)

            if name and rank is not None:
                rows.append({
                    "name": name,
                    "renown": rank,              # int8
                    "renown_change": value or 0, # int8 fallback
                })

        except Exception as e:
            print("Row parse error:", e)
            continue

    return rows


def upload(rows):
    if not rows:
        print("No rows to upload")
        return

    for r in rows:
        result = supabase.table("leaderboard").upsert({
            "name": r["name"],                       # text
            "renown": r["renown"],                   # int8
            "renown_change": r["renown_change"],     # int8
            "timezone_time": timezone_time           # timestampz
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
