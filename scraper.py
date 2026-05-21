import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from supabase import create_client
print("🔥 THIS IS THE LATEST SCRAPER FILE")
# =========================
# SUPABASE SETUP
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE_URL = "https://YOUR_SITE_HERE.com"


# =========================
# TIME HELPERS
# =========================
def get_time_fields():
    now_utc = datetime.now(timezone.utc)

    return {
        "timestamptxt": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "timezonetimestampz": now_utc.isoformat()
    }


# =========================
# FETCH PAGE
# =========================
def fetch(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


# =========================
# PARSE TABLE
# =========================
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
        renown_raw = cols[1].get_text(strip=True)

        try:
            renown = int(renown_raw.replace(",", ""))
        except:
            renown = 0

        rows.append({
            "name": name,
            "renown": renown
        })

    return rows


# =========================
# SCRAPE ALL BOARDS
# =========================
def scrape_all():
    categories = {
        "fame": "/fame",
        "bounty": "/bounty",
        "grand_navy": "/grand_navy",
        "assassin_syndicate": "/assassin_syndicate"
    }

    all_rows = []
    time_fields = get_time_fields()

    for category, endpoint in categories.items():
        print(f"Scraping {category}...")

        soup = fetch(BASE_URL + endpoint)
        data = parse_table(soup)

        print(f"{category}: {len(data)} rows")

        for row in data:
            all_rows.append({
                "name": row["name"],
                "renown": row["renown"],
                "renownchange": 0,
                "timestamptxt": time_fields["timestamptxt"],
                "timezonetimestampz": time_fields["timezonetimestampz"]
            })

    return all_rows


# =========================
# UPLOAD
# =========================
def upload(rows):
    if not rows:
        print("No data to upload")
        return

    supabase.table("leaderboard").insert(rows).execute()
    print(f"Uploaded {len(rows)} rows")


# =========================
# MAIN
# =========================
def main():
    all_rows = scrape_all()
    upload(all_rows)


if __name__ == "__main__":
    main()
