#!/usr/bin/env python3
"""
check_results.py — Standalone tool to check and settle finished bets, then regenerate the report.
Does NOT run any league scans or place new bets.
Updates the bankroll with realized P&L from settlements.
"""

import asyncio

from src.core.database import BettingDatabase
from src.core.reporter import generate_report
from src.core.results_checker import resolve_results


async def main():
    db = BettingDatabase()
    print("=" * 50)
    print("  SENTINEL QUANT AGENT — RESULTS SETTLER")
    print("=" * 50)

    balance_before = db.get_bankroll_balance()
    print(f"\n  Bankroll before: ${balance_before:.2f}")

    print("\n[RESULTS] Checking and settling finished bets...")
    result = await resolve_results(db)

    settled = result["settled"]
    skipped = result["skipped"]
    total_pnl = result["total_pnl"]

    if settled > 0:
        balance_after = round(balance_before + total_pnl, 2)
        db.set_bankroll_balance(balance_after)
        db.record_session_summary(
            session_type="settlement",
            actual_pnl=total_pnl,
            bets_settled=settled,
            bets_skipped=skipped,
            balance_before=round(balance_before, 2),
            balance_after=balance_after,
        )
        print("\n[BANKROLL] Settlement summary:")
        print(f"  Bets settled : {settled}")
        print(f"  Bets skipped : {skipped}")
        print(f"  P&L          : ${total_pnl:+.2f}")
        print(f"  Balance      : ${balance_before:.2f} -> ${balance_after:.2f}")
    else:
        print(f"\n[BANKROLL] No bets settled. Bankroll unchanged (${balance_before:.2f}).")

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
