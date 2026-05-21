import os
from datetime import datetime
import pytz
from supabase import create_client

# =========================
# SUPABASE CONNECTION
# =========================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# TIMEZONE SETUP
# =========================

EASTERN = pytz.timezone("America/New_York")

now = datetime.now(EASTERN)

timestamp = now.isoformat()
date = now.strftime("%Y-%m-%d")
time = now.strftime("%H:%M:%S")

# =========================
# FAKE DATA (replace later with scraper)
# =========================

data = [
    {"name": "Player1", "renown": 1200, "renown_change": 50},
    {"name": "Player2", "renown": 900, "renown_change": -20},
    {"name": "Player3", "renown": 1500, "renown_change": 120},
]

# =========================
# UPLOAD FUNCTION
# =========================

def upload_data(rows):
    for row in rows:
        supabase.table("leaderboard").upsert({
            "name": row["name"],
            "renown": row["renown"],
            "renown_change": row["renown_change"],

            # NEW TIME FIELDS
            "timestamp": timestamp,
            "date": date,
            "time": time
        }).execute()

    print(f"Upload complete at {timestamp}")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    upload_data(data)
