#!/usr/bin/env python3
"""
check_results.py — Standalone tool to check and settle finished bets, then regenerate the report.
Does NOT run any league scans or place new bets.
"""
import asyncio
from src.core.database import BettingDatabase
from src.core.results_checker import resolve_results
from src.core.reporter import generate_report

async def main():
    db = BettingDatabase()
    print("=" * 50)
    print("  SENTINEL QUANT AGENT — RESULTS SETTLER")
    print("=" * 50)
    
    print("\n[RESULTS] Checking and settling finished bets...")
    await resolve_results(db)
    
    print("\n[REPORTER] Regenerating performance segmentation report...")
    try:
        generate_report()
        print("[SUCCESS] Report docs/PERFORMANCE_SEGMENTATION.md updated successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to generate report: {e}")
        
    print("\n" + "=" * 50)
    print("  SETTLEMENT COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
