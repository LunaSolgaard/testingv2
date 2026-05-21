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

timezone_time = now.strftime("%Y-%m-%d %H:%M:%S %Z")
timestamp = now.isoformat()

URLS = {
    "fame": "https://leaderboards.arcaneodyssey.dev/fame",
    "bounty": "https://leaderboards.arcaneodyssey.dev/bounty",
    "grand_navy": "https://leaderboards.arcaneodyssey.dev/grand-navy",
    "assassin_syndicate": "https://leaderboards.arcaneodyssey.dev/assassin-syndicate",
}

headers = {
    "User-Agent": "Mozilla/5.0"
}

def scrape_board(url, board_name):
    res = requests.get(url, headers=headers)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    rows = []

    # These sites typically use table rows
    table_rows = soup.find_all("tr")

    for row in table_rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        try:
            rank = cols[0].get_text(strip=True)
            name = cols[1].get_text(strip=True)

            if name and rank:
                rows.append({
                    "name": name,
                    "renown": rank,  # reuse field for leaderboard value
                    "renown_change": board_name
                })
        except:
            continue

    return rows


def upload(rows):
    for r in rows:
        result = supabase.table("leaderboard").upsert({
            "name": r["name"],
            "renown": r["renown"],
            "renown_change": r["renown_change"],
            "timezone_time": timezone_time,
            "timestamp": timestamp
        }).execute()

    print(f"Uploaded {len(rows)} rows")


def main():
    all_rows = []

    for board_name, url in URLS.items():
        print(f"Scraping {board_name}...")
        rows = scrape_board(url, board_name)
        print(f"{board_name}: {len(rows)} rows")
        all_rows.extend(rows)

    upload(all_rows)
    print("done")


if __name__ == "__main__":
    main()
