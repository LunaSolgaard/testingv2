import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from supabase import create_client

print("🔥 RUNNING FINAL CLEAN SCRAPER")

# =========================
# SUPABASE
# =========================
SUPABASE_URL = "https://yiskdpphlrrmfhhpwght.supabase.co"
SUPABASE_KEY = "sb_publishable_M-1TzpN8Nd2-x5KnyfhghQ_dx0nXKpN"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# TIME
# =========================
def get_time_fields():
    now = datetime.now(timezone.utc)
    return {
        "timestamptxt": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "timezonetimestampz": now.isoformat()
    }

# =========================
# FETCH
# =========================
def fetch(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

# =========================
# PARSE
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

        try:
            renown = int(cols[1].get_text(strip=True).replace(",", ""))
        except:
            renown = 0

        rows.append({
            "name": name,
            "renown": renown
        })

    return rows

# =========================
# SCRAPE ALL (NO BASE_URL)
# =========================
def scrape_all():
    urls = {
        "fame": "https://leaderboards.arcaneodyssey.dev/fame",
        "bounty": "https://leaderboards.arcaneodyssey.dev/bounty",
        "grand_navy": "https://leaderboards.arcaneodyssey.dev/grand-navy",
        "assassin_syndicate": "https://leaderboards.arcaneodyssey.dev/assassin-syndicate"
    }

    all_rows = []
    time_fields = get_time_fields()

    for category, url in urls.items():
        print(f"Scraping {category}...")

        soup = fetch(url)
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
