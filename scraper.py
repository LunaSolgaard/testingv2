import os
import re
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

def parse_page(page, url, category):
    print(f"  Loading {url} ...")
    page.goto(url, wait_until="networkidle", timeout=60000)
    # extra wait for JS rendering
    page.wait_for_timeout(3000)
    # screenshot for debugging
    page.screenshot(path=f"screenshot_{category}.png")

    # dump all text from the page
    text = page.inner_text("body")
    print(f"  --- RAW TEXT SAMPLE ---")
    print(text[:500])
    print(f"  -----------------------")

    rows = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines):
        # look for a line that is purely a big number (the renown value)
        clean = line.replace(",", "")
        if clean.isdigit() and len(clean) >= 3:
            renown = int(clean)
            # the name is likely the line before this one
            if i > 0:
                name = lines[i - 1]
                # skip if name looks like a header or number
                if name and not name.replace(",", "").isdigit():
                    rows.append({"name": name, "renown": renown})

    print(f"  → {len(rows)} rows parsed")
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
                data = parse_page(page, url, category)
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
