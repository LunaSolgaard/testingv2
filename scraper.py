import os
from datetime import datetime, timezone
from supabase import create_client
from playwright.sync_api import sync_playwright

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://yiskdpphlrrmfhhpwght.supabase.co")
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_time_fields():
    now = datetime.now(timezone.utc)
    return {
        "timestamptxt":       now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "timezonetimestampz": now.isoformat()
    }

def get_previous_scan():
    try:
        result = supabase.table("leaderboard") \
            .select("timezonetimestampz") \
            .order("timezonetimestampz", desc=True) \
            .limit(1) \
            .execute()
        if not result.data:
            print("First run — renownchange will be 0.")
            return {}
        latest_ts = result.data[0]["timezonetimestampz"]
        rows = supabase.table("leaderboard") \
            .select("name,renown,category") \
            .eq("timezonetimestampz", latest_ts) \
            .execute()
        prev = {(row["name"], row["category"]): row["renown"] for row in rows.data}
        print(f"Loaded {len(prev)} entries from previous scan.")
        return prev
    except Exception as e:
        print(f"Warning: could not load previous scan ({e})")
        return {}

def parse_table(page, url):
    print(f"  Loading {url} ...")
    page.goto(url, wait_until="networkidle", timeout=30000)
    page.wait_for_selector("table", timeout=15000)
    rows = []
    trs = page.query_selector_all("table tr")
    for tr in trs[1:]:
        cols = tr.query_selector_all("td")
        if len(cols) < 2:
            continue
        name = cols[0].inner_text().strip()
        try:
            renown = int(cols[1].inner_text().strip().replace(",", ""))
        except:
            renown = 0
        rows.append({"name": name, "renown": renown})
    print(f"  → {len(rows)} rows found")
    return rows

def scrape_all(prev_scan):
    urls = {
        "fame":               "https://leaderboards.arcaneodyssey.dev/fame",
        "bounty":             "https://leaderboards.arcaneodyssey.dev/bounty",
        "grand_navy":         "https://leaderboards.arcaneodyssey.dev/grand-navy",
        "assassin_syndicate": "https://leaderboards.arcaneodyssey.dev/assassin-syndicate"
    }
    all_rows = []
    time_fields = get_time_fields()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for category, url in urls.items():
            print(f"Scraping {category}...")
            try:
                data = parse_table(page, url)
                for row in data:
                    key = (row["name"], category)
                    prev_renown = prev_scan.get(key)
                    change = (row["renown"] - prev_renown) if prev_renown is not None else 0
                    all_rows.append({
                        "name":               row["name"],
                        "renown":             row["renown"],
                        "renownchange":       change,
                        "category":           category,
                        "timestamptxt":       time_fields["timestamptxt"],
                        "timezonetimestampz": time_fields["timezonetimestampz"]
                    })
            except Exception as e:
                print(f"  ERROR scraping {category}: {e}")

        browser.close()

    return all_rows

def upload(rows):
    if not rows:
        print("No data to upload.")
        return
    supabase.table("leaderboard").insert(rows).execute()
    print(f"✅ Uploaded {len(rows)} rows")

def main():
    prev_scan = get_previous_scan()
    all_rows  = scrape_all(prev_scan)
    upload(all_rows)

if __name__ == "__main__":
    main()
