def upload(rows, prev):
    if not rows:
        print("No rows found")
        return

    payload = []

    for r in rows:
        entry = {
            "name": r["name"],
            "renown": r["renown"],
            "timestamp": timestamp
        }

        old = prev.get(r["name"])

        # only include if we actually have previous data
        if old is not None:
            entry["renown_change"] = r["renown"] - old

        payload.append(entry)

    supabase.table("leaderboard").insert(payload).execute()

    print(f"Uploaded {len(payload)} rows")
