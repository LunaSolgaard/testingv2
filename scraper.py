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

tz = pytz.timezone("America/New_York")
now = datetime.now(tz)
timestamp = now.isoformat()


URLS = {
    "fame": "https://leaderboards.arcaneodyssey.dev/fame",
    "bounty": "https://leaderboards.arcaneodyssey.dev/bounty",
    "grand_navy": "https://leaderboards.arcaneodyssey.dev/grand-navy",
    "assassin_syndicate": "https://leaderboards.arcaneodyssey.dev/assassin-syndicate",
}

headers = {"User-Agent": "Mozilla/5.0"}


def clean_int(value: str):
    return int(value.replace(",", "").strip())


def get_previous_snapshot():
    """Get last stored values for comparison"""
    res = supabase.table("leaderboard").select("*").execute()
    data = {}

    for row in res.data:
        data[row["name"]] = row["renown"]

    return data


def scrape_board(url):
    res = requests.get(url, headers=headers, timeout=20)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    rows = []

    # 🔥 KEY FIX: leaderboard rows are usually repeated card elements
    # We filter by elements containing BOTH a number + text pattern
    candidates = soup.find_all(["div", "tr", "li"])

    for c in candidates:
        text = " ".join(c.stripped_strings)

        if not text:
            continue

        # must contain at least one large number
        parts = text.split()

        numbers = []
        for p in parts:
            if p.replace(",", "").isdigit():
                numbers.append(p)

        if not numbers:
            continue

        try:
            value = clean_int(numbers[-1])

            # name = everything before number, cleaned
            name_parts = []
            for p in parts:
                if p.replace(",", "").isdigit():
                    break
                name_parts.append(p)

            name = " ".join(name_parts).strip()

            if len(name) < 2:
                continue

            rows.append({
                "name": name,
                "renown": value
            })

        except:
            continue

    # remove duplicates
    seen = set()
    clean = []
    for r in rows:
        if r["name"] not in seen:
            seen.add(r["name"])
            clean.append(r)

    return clean


def upload(rows, previous):
    if not rows:
        print("No rows to upload")
        return

    for r in rows:
        old = previous.get(r["name"], 0)
        change = r["renown"] - old

        supabase.table("leaderboard").upsert({
            "name": r["name"],
            "renown": r["renown"],
            "renown_change": change,
            "timezone_time": timestamp
        }).execute()

    print(f"Uploaded {len(rows)} rows")


def main():
    previous = get_previous_snapshot()

    all_rows = []

    for name, url in URLS.items():
        print(f"Scraping {name}...")
        rows = scrape_board(url)
        print(f"{name}: {len(rows)} rows scraped")
        all_rows.extend(rows)

    upload(all_rows, previous)
    print("done")


if __name__ == "__main__":
    main()
