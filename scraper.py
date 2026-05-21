import os
from supabase import create_client

# =========================
# CONNECT TO SUPABASE
# =========================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# FAKE DATA (REPLACE LATER)
# =========================
# This simulates your scraped leaderboard data

data = [
    {"name": "Player1", "renown": 1200, "renown_change": 50},
    {"name": "Player2", "renown": 900, "renown_change": -20},
    {"name": "Player3", "renown": 1500, "renown_change": 120},
]

# =========================
# PUSH TO SUPABASE
# =========================

def upload_data(rows):
    for row in rows:
        supabase.table("leaderboard").upsert({
            "name": row["name"],
            "renown": row["renown"],
            "renown_change": row["renown_change"]
        }).execute()

    print("Upload complete!")

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    upload_data(data)
