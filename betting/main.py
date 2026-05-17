import asyncio
from src.core.orchestrator import run_full_scan

import json

USER_TARGET_LAMBDA = 2.65

try:
    with open("data/sharps.json", "r") as f:
        sharp_data = json.load(f)
        print(f"[DEBUG] Loaded {len(sharp_data)} books from sharps.json")
except Exception:
    pass

if __name__ == "__main__":
    print("[INFO] You are running main.py. This is a DRY RUN: bets are displayed but NOT logged to the database.")
    print("[TIP] Use 'python3 run_session.py' to record a session and update reports.")
    asyncio.run(run_full_scan(is_session=False))