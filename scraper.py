import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from supabase import create_client

# =========================
# ENV SETUP
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE_URL = "https://YOUR_TARGET_SITE_HERE.com"  # <-- change this


# =========================
# SCRAPER HELPERS
# =========================
def fetch_page(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def parse_table(soup, category_name):
    """
    Generic parser (you may need to adjust selectors depending on site structure)
    """
    rows = []

    table = soup.find("table")
    if not table:
        print(f"No table found for {category_name}")
        return rows

    for tr in table.find_all("tr")[1:]:
        cols = tr.find_all("td")
        if len(cols) < 2:
            continue

        username = cols[0].get_text(strip=True)
        value_text = cols[1].get_text(strip=True)

        # Convert safely
        try:
            value = int(value_text.replace(",", ""))
        except:
            value = 0

        rows.append({
            "category": category_name,
            "username": username,
            "value": value
        })

    return rows


# =========================
# SCRAPE FUNCTIONS
# =========================
def scrape_fame():
    print("Scraping fame...")
    soup = fetch_page(f"{BASE_URL}/fame")
    data = parse_table(soup, "fame")
    print(f"fame: {len(data)} rows")
    return data


def scrape_bounty():
    print("Scraping bounty...")
    soup = fetch_page(f"{BASE_URL}/bounty")
    data = parse_table(soup, "bounty")
    print(f"bounty: {len(data)} rows")
    return data


def scrape_grand_navy():
    print("Scraping grand_navy...")
    soup = fetch_page(f"{BASE_URL}/grand_navy")
    data = parse_table(soup, "grand_navy")
    print(f"grand_navy: {len(data)} rows")
    return data


def scrape_assassin_syndicate():
    print("Scraping assassin_syndicate...")
    soup = fetch_page(f"{BASE_URL}/assassin_syndicate")
    data = parse_table(soup, "assassin_syndicate")
    print(f"assassin_syndicate: {len(data)} rows")
    return data


# =========================
# SUPABASE UPLOAD
# =========================
def upload(all_rows):
    if not all_rows:
        print("No data to upload")
        return

    payload = []

    for row in all_rows:
        payload.append({
            "category": row["category"],
            "username": row["username"],
            "value": row["value"],
            "created_at": datetime.utcnow().isoformat()
        })

    # Insert into correct table
    supabase.table("leaderboard").insert(payload).execute()

    print(f"Uploaded {len(payload)} rows")


# =========================
# MAIN
# =========================
def main():
    all_rows = []

    all_rows.extend(scrape_fame())
    all_rows.extend(scrape_bounty())
    all_rows.extend(scrape_grand_navy())
    all_rows.extend(scrape_assassin_syndicate())

    upload(all_rows)


if __name__ == "__main__":
    main()
