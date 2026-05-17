#!/usr/bin/env python3
"""
run_session.py — Daily session runner for the Sentinel Quant Agent.

Usage: python3 run_session.py
Just run this 2-3x per day. It will:
  1. Run the full multi-league scan.
  2. Log all +EV bets to the simulated_bets table.
  3. Regenerate the PERFORMANCE_SEGMENTATION.md report.
  4. Append a summary entry to SESSION_LOG.md.
"""
import asyncio
import subprocess
import sys
import os
from datetime import datetime, timezone

LOG_FILE = "docs/SESSION_LOG.md"
DB_PATH = "bets.db"

def count_bets_today(session_start_ts):
    """Count how many simulated_bets were inserted in this session."""
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM simulated_bets WHERE timestamp >= ?",
            (session_start_ts,)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0

def total_bets_logged():
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM simulated_bets")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0

def write_session_log(session_start, session_end, new_bets, total_bets):
    duration_secs = (session_end - session_start).seconds
    mins, secs = divmod(duration_secs, 60)

    entry = (
        f"\n## Session — {session_start.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"- **Duration**: {mins}m {secs}s\n"
        f"- **New +EV Bets Logged**: {new_bets}\n"
        f"- **Total Bets in DB**: {total_bets}\n"
        f"- **Report**: [PERFORMANCE_SEGMENTATION.md](PERFORMANCE_SEGMENTATION.md)\n"
    )

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("# Sentinel Session Log\n\n")
            f.write("> Each entry represents one manual run of `run_session.py`.\n")
            f.write("> Run 2-3x per day for 4 days to build the performance dataset.\n")

    with open(LOG_FILE, "a") as f:
        f.write(entry)

    print(f"\n[SESSION] Log updated: {LOG_FILE}")

async def run():
    print("=" * 50)
    print("  SENTINEL QUANT AGENT — SESSION RUNNER")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50)

    session_start = datetime.now(timezone.utc)
    session_start_ts = session_start.isoformat()

    # Step 1: Settle any previously tracked bets that have now finished
    from src.core.database import BettingDatabase
    from src.core.results_checker import resolve_results
    db = BettingDatabase()
    print("\n[STEP 1] Checking results for previously tracked bets...")
    await resolve_results(db)

    # Step 2: Run the full new scan (with DB logging enabled)
    print("\n[STEP 2] Running new league scan (RECORDING SESSION)...")
    from src.core.orchestrator import run_full_scan
    await run_full_scan(is_session=True)

    # Step 3: Regenerate the performance report
    from src.core.reporter import generate_report
    generate_report()

    session_end = datetime.now(timezone.utc)

    # Count what was added in this session
    new_bets = count_bets_today(session_start_ts)
    total = total_bets_logged()

    # Write to the session log
    write_session_log(session_start, session_end, new_bets, total)

    print(f"\n{'='*50}")
    print(f"  SESSION COMPLETE")
    print(f"  New bets logged : {new_bets}")
    print(f"  Total in DB     : {total}")
    print(f"  Report          : PERFORMANCE_SEGMENTATION.md")
    print(f"  Session log     : SESSION_LOG.md")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    asyncio.run(run())
