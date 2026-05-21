import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE_URL = "https://YOUR_SITE_HERE.com"


# -----------------------
# TIME
# -----------------------
def get_timestamp():
    now = datetime.utcnow()
    return now.strftime("%Y-%m-%d %H:%M:%S UTC")


# -----------------------
# SCRAPER
# -----------------------
def fetch(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def parse_table(soup):
    rows = []

    table = soup.find("table")
    if not table:
        return rows

    for tr in table.find_all("tr")[1:]:
        cols = tr.find_all("td")
        if len(cols) < 2:
            continue

        name = cols[0].get_text(strip=True)
        renown = cols[1].get_text(strip=True)

        try:
            renown = int(renown.replace(",", ""))
        except:
            renown = 0

        rows.append({
            "name": name,
            "renown": renown
        })

    return rows


# -----------------------
# MAIN
# -----------------------
def main():
    timestamp = get_timestamp()

    categories = {
        "fame": "/fame",
        "bounty": "/bounty",
        "grand_navy": "/grand_navy",
        "assassin_syndicate": "/assassin_syndicate"
    }

    all_rows = []

    for category, url in categories.items():
        print(f"Scraping {category}...")

        soup = fetch(BASE_URL + url)
        data = parse_table(soup)

        print(f"{category}: {len(data)} rows")

        for row in data:
            all_rows.append({
                "name": row["name"],
                "renown": row["renown"],
                "renownchange": 0,
                "timestamp": timestamp
            })

    upload(all_rows)


# -----------------------
# UPLOAD
# -----------------------
def upload(rows):
    supabase.table("leaderboard").insert(rows).execute()
    print(f"Uploaded {len(rows)} rows")


if __name__ == "__main__":
    main()
