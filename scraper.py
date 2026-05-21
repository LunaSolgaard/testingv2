from datetime import datetime
import pytz
import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client
import re

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

tz = pytz.timezone("America/New_York")
timestamp = datetime.now(tz).isoformat()

URLS = {
    "fame": "https://leaderboards.arcaneodyssey.dev/fame",
    "bounty": "https://leaderboards.arcaneodyssey.dev/bounty",
    "grand_navy": "https://leaderboards.arcaneodyssey.dev/grand-navy",
    "assassin_syndicate": "https://leaderboards.arcaneodyssey.dev/assassin-syndicate",
}

headers = {"User-Agent": "Mozilla/5.0"}


def extract_number(text):
    nums = re.findall(r"\d[\d,]*", text.replace(",", ""))
    return int(nums[-1]) if nums else None


def extract_name(text):
    text = re.sub(r"\d[\d,]*", "", text)
    text = text.replace("Save File", "")

    bad_words = ["Top", "Leaderboard", "Players", "Updates", "Last", "Updated", "#"]
    for w in bad_words:
        text = text.replace(w, "")

    return " ".join(text.split()).strip()


def scrape_board(url):
    res = requests.get(url, headers=headers, timeout=20)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    rows = []

    for block in soup.find_all("div"):
        text = " ".join(block.stripped_strings)

        if not text or "Save File" in text:
            continue

        value = extract_number(text)
        if value is None:
            continue

        name = extract_name(text)

        if not name or len(name) < 2:
            continue

        rows.append({
            "name": name,
            "renown": value
        })

    # dedupe
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
        print("No rows found")
        return

    payload = []

    for r in rows:
        payload.append({
            "name": r["name"],
            "renown": r["renown"],
            "renown_change": r["renown"],  # TEMP FIX (important below)
            "timestamp": timestamp
        })

    supabase.table("leaderboard").insert(payload).execute()

    print(f"Uploaded {len(payload)} rows")


def main():
    all_rows = []

    for board, url in URLS.items():
        print(f"Scraping {board}...")
        rows = scrape_board(url)
        print(f"{board}: {len(rows)} rows")
        all_rows.extend(rows)

    upload(all_rows)
    print("done")


if __name__ == "__main__":
    main()
