from datetime import datetime
import pytz
import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client
import uuid
import re

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

tz = pytz.timezone("America/New_York")
timestamp = datetime.now(tz).isoformat()
run_id = str(uuid.uuid4())

URLS = {
    "fame": "https://leaderboards.arcaneodyssey.dev/fame",
    "bounty": "https://leaderboards.arcaneodyssey.dev/bounty",
    "grand_navy": "https://leaderboards.arcaneodyssey.dev/grand-navy",
    "assassin_syndicate": "https://leaderboards.arcaneodyssey.dev/assassin-syndicate",
}

headers = {"User-Agent": "Mozilla/5.0"}


def extract_main_stat(text):
    """
    Extract the REAL leaderboard stat.
    We ignore Save File numbers completely.
    """
    # remove commas
    clean = text.replace(",", "")

    # split into numbers
    nums = re.findall(r"\d+", clean)

    if not nums:
        return None

    # ❌ RULE: Save File pattern always appears before junk number
    # We assume:
    # - last large number = actual stat
    # - earlier numbers may be Save File or UI junk
    return int(nums[-1])


def extract_name(text):
    """
    Remove numbers and known junk keywords.
    """
    text = re.sub(r"\d+", "", text)
    text = text.replace("Save File", "")
    text = text.strip()

    # remove repeated UI words
    bad_words = ["Top", "Leaderboard", "Players", "Updates", "Last", "Updated", "#"]
    for w in bad_words:
        text = text.replace(w, "")

    return " ".join(text.split()).strip()


def scrape_board(url, board_name):
    res = requests.get(url, headers=headers, timeout=20)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    rows = []

    # grab full visible text blocks
    for block in soup.find_all("div"):
        text = " ".join(block.stripped_strings)

        if not text:
            continue

        # must contain a number or it's irrelevant
        if not re.search(r"\d", text):
            continue

        # must NOT be header junk
        if "Leaderboard" in text and "Save File" not in text:
            continue

        name = extract_name(text)
        value = extract_main_stat(text)

        # HARD RULE: ignore Save File noise
        if "save file" in text.lower():
            continue

        if not name or value is None:
            continue

        # final sanity check (ignore UI garbage)
        if len(name) < 2:
            continue

        rows.append({
            "name": name,
            "renown": value,
            "board": board_name
        })

    # dedupe
    seen = set()
    clean = []

    for r in rows:
        key = (r["name"], r["renown"], r["board"])
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
            "run_id": run_id,
            "name": r["name"],
            "renown": r["renown"],
            "board": r["board"],
            "timestamp": timestamp
        })

    supabase.table("leaderboard").insert(payload).execute()

    print(f"Uploaded {len(payload)} clean rows")


def main():
    all_rows = []

    for board, url in URLS.items():
        print(f"Scraping {board}...")
        rows = scrape_board(url, board)
        print(f"{board}: {len(rows)} rows")
        all_rows.extend(rows)

    upload(all_rows)
    print("done")


if __name__ == "__main__":
    main()
