"""
reporter.py — Generates PERFORMANCE_SEGMENTATION.md from the simulated_bets table.
Includes bankroll overview and recent session summaries.
Run directly: python3 -m src.core.reporter
"""
import sqlite3
from datetime import datetime, timezone

DB_PATH = "bets.db"
OUTPUT_PATH = "docs/PERFORMANCE_SEGMENTATION.md"

def generate_report():
    from src.core.database import BettingDatabase

    db = BettingDatabase()
    conn = db.conn
    cursor = conn.cursor()

    # ── 1. Bankroll Header ────────────────────────────────────────────────────────
    bankroll_info = db.get_bankroll_summary()
    initial = 5000.0
    total_pnl = bankroll_info["total_realized_pnl"]
    current = bankroll_info["current_balance"]
    roi_pct = (total_pnl / initial * 100) if initial > 0 else 0.0

    lines = [
        "# Performance Segmentation Report",
        f"\n_Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_\n",
        "---",
        "## Bankroll Overview",
        "| Metric | Value |",
        "|---|---|",
        f"| Initial Bankroll | ${initial:,.2f} |",
        f"| Current Balance  | ${current:,.2f} |",
        f"| Total Realized P&L | ${total_pnl:+,.2f} |",
        f"| Overall ROI      | {roi_pct:+.1f}% |",
        "",
        "---",
    ]

    # ── 2. Session History ────────────────────────────────────────────────────────
    sessions = db.get_session_summaries(limit=10)
    if sessions:
        lines.append("## Recent Sessions\n")
        lines.append("| # | Type | Bets | Stake | EV Value | Actual P&L | Balance |")
        lines.append("|---|---|---|---|---|---|---|")
        for i, s in enumerate(sessions, 1):
            s_type = s["session_type"]
            bets = s["bets_logged"] if s["session_type"] == "scan" else s["bets_settled"]
            stake_str = f"${s['total_stake_committed']:.2f}" if s["total_stake_committed"] else "—"
            ev_str = f"${s['theoretical_ev_profit']:+.2f}" if s["theoretical_ev_profit"] else "—"
            pnl_str = f"${s['actual_pnl']:+.2f}" if s["actual_pnl"] is not None else "—"
            bal_str = f"${s['balance_after']:.2f}" if s["balance_after"] is not None else "—"
            lines.append(f"| {i} | {s_type} | {bets} | {stake_str} | {ev_str} | {pnl_str} | {bal_str} |")
        lines.append("")

    # ── 3. Category Performance ────────────────────────────────────────────────────
    cursor.execute('''
        SELECT
            category,
            COUNT(*) AS total_volume,
            SUM(CASE WHEN is_win IS NOT NULL THEN 1 ELSE 0 END) AS settled,
            SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) AS wins,
            AVG(1.0 / fair_odds) AS avg_expected_win_rate,
            SUM(COALESCE(actual_profit, 0)) AS total_profit,
            SUM(stake) AS total_stake
        FROM simulated_bets
        GROUP BY category
        ORDER BY total_volume DESC
    ''')
    rows = cursor.fetchall()
    conn.close()

    lines.append("## Category Performance\n")
    lines.extend([
        "> **How to read this report:**",
        "> - **Volume**: How many times this category appeared as a +EV opportunity.",
        "> - **Win Rate**: Actual % of settled bets that won.",
        "> - **Yield (ROI)**: Total profit / total stake. Positive = the model is generating real value.",
        "> - **Model Accuracy**: Expected win rate vs actual win rate. Near 0% = the Poisson model is well-calibrated.",
        "> - **Stake Exposure**: Total Kelly-weighted $ committed to this category.",
        "> - Unsettled bets (is_win = NULL) are excluded from win rate / yield calculations.",
        "",
    ])

    if not rows:
        lines.append("_No simulated bets found yet. Run `main.py` to populate the database._")
    else:
        lines.append("| Category | Volume | Settled | Win Rate | Expected WR | Model Accuracy | Yield (ROI) | Stake Exposure | P&L ($) |")
        lines.append("|---|---|---|---|---|---|---|---|---|")

        for row in rows:
            category      = row["category"]
            total_volume  = row["total_volume"]
            settled       = row["settled"] or 0
            wins          = row["wins"] or 0
            total_profit  = row["total_profit"] or 0.0
            total_stake   = row["total_stake"] or 1.0
            avg_exp_wr    = row["avg_expected_win_rate"] or 0.0

            actual_wr   = (wins / settled * 100) if settled > 0 else None
            yield_pct   = (total_profit / total_stake * 100) if settled > 0 else None
            model_acc   = ((actual_wr / 100) - avg_exp_wr) if actual_wr is not None else None

            is_high_accuracy = model_acc is not None and -0.05 <= model_acc <= 0.05
            cat_display = f"⭐ **{category}**" if is_high_accuracy else category
            wr_str      = f"{actual_wr:.1f}%" if actual_wr is not None else "—"
            yield_str   = f"{yield_pct:+.1f}%" if yield_pct is not None else "—"
            model_str   = f"**{model_acc*100:+.1f}pp**" if is_high_accuracy else (f"{model_acc*100:+.1f}pp" if model_acc is not None else "—")
            exp_wr_str  = f"{avg_exp_wr*100:.1f}%"
            stake_exposure = f"${total_stake:.2f}"
            pnl_str     = f"${total_profit:+.2f}" if settled > 0 else "—"

            lines.append(f"| {cat_display} | {total_volume} | {settled} | {wr_str} | {exp_wr_str} | {model_str} | {yield_str} | {stake_exposure} | {pnl_str} |")

    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(lines))

    print(f"[REPORTER] Report saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_report()
