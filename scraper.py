import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from supabase import create_client

# =========================
# SUPABASE
# =========================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://yiskdpphlrrmfhhpwght.supabase.co")
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# TIME
# =========================
def get_time_fields():
    now = datetime.now(timezone.utc)
    return {
        "timestamptxt":       now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "timezonetimestampz": now.isoformat()
    }

# =========================
# FETCH PREVIOUS SCAN
# =========================
def get_previous_scan():
    try:
        result = supabase.table("leaderboard") \
            .select("timezonetimestampz") \
            .order("timezonetimestampz", desc=True) \
            .limit(1) \
            .execute()

        if not result.data:
            print("No previous scan found — first run, renownchange will be 0.")
            return {}

        latest_ts = result.data[0]["timezonetimestampz"]

        rows = supabase.table("leaderboard") \
            .select("name,renown") \
            .eq("timezonetimestampz", latest_ts) \
            .execute()

        prev = {row["name"]: row["renown"] for row in rows.data}
        print(f"Loaded {len(prev)} entries from previous scan ({latest_ts})")
        return prev

    except Exception as e:
        print(f"Warning: could not load previous scan ({e}) — renownchange will be 0.")
        return {}

# =========================
# FETCH HTML
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
        try:
            renown = int(cols[1].get_text(strip=True).replace(",", ""))
        except:
            renown = 0
        rows.append({"name": name, "renown": renown})
    return rows

# =========================
# SCRAPE ALL LEADERBOARDS
# =========================
def scrape_all(prev_scan):
    urls = {
        "fame":               "https://leaderboards.arcaneodyssey.dev/fame",
        "bounty":             "https://leaderboards.arcaneodyssey.dev/bounty",
        "grand_navy":         "https://leaderboards.arcaneodyssey.dev/grand-navy",
        "assassin_syndicate": "https://leaderboards.arcaneodyssey.dev/assassin-syndicate"
    }
    all_rows = []
    time_fields = get_time_fields()

    for category, url in urls.items():
        print(f"Scraping {category}...")
        soup = fetch(url)
        data = parse_table(soup)
        print(f"  → {len(data)} rows found")

        for row in data:
            prev_renown = prev_scan.get(row["name"])
            change = (row["renown"] - prev_renown) if prev_renown is not None else 0

            all_rows.append({
                "name":               row["name"],
                "renown":             row["renown"],
                "renownchange":       change,
                "category":           category,
                "timestamptxt":       time_fields["timestamptxt"],
                "timezonetimestampz": time_fields["timezonetimestampz"]
            })

    return all_rows

# =========================
# UPLOAD TO SUPABASE
# =========================
def upload(rows):
    if not rows:
        print("No data to upload.")
        return
    supabase.table("leaderboard").insert(rows).execute()
    print(f"✅ Uploaded {len(rows)} rows")

# =========================
# MAIN
# =========================
def main():
    prev_scan = get_previous_scan()
    all_rows  = scrape_all(prev_scan)
    upload(all_rows)

if __name__ == "__main__":
    main()
