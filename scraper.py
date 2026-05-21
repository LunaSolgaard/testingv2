from datetime import datetime
import pytz
import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

eastern = pytz.timezone("America/New_York")
now = datetime.now(eastern)

timezone_time = now.strftime("%Y-%m-%d %H:%M:%S %Z")
timestamp = now.isoformat()

def upload(rows):
    for r in rows:
        supabase.table("leaderboard").upsert({
            "name": r["name"],
            "renown": r["renown"],
            "renown_change": r["renown_change"],
            "timezone_time": timezone_time,
            "timestamp": timestamp
        }).execute()

print("done")
