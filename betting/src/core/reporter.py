"""
reporter.py — Generates PERFORMANCE_SEGMENTATION.md from the simulated_bets table.
Run directly: python3 -m src.core.reporter
"""
import sqlite3
from datetime import datetime, timezone

DB_PATH = "bets.db"
OUTPUT_PATH = "docs/PERFORMANCE_SEGMENTATION.md"

def generate_report():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

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

    lines = [
        "# Performance Segmentation Report",
        f"\n_Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_\n",
        "> **How to read this report:**",
        "> - **Volume**: How many times this category appeared as a +EV opportunity.",
        "> - **Win Rate**: Actual % of settled bets that won.",
        "> - **Yield (ROI)**: Total profit / total stake. Positive = the model is generating real value.",
        "> - **Model Accuracy**: Expected win rate vs actual win rate. Near 0% = the Poisson model is well-calibrated.",
        "> - Unsettled bets (is_win = NULL) are excluded from win rate / yield calculations.",
        "\n---\n",
    ]

    if not rows:
        lines.append("_No simulated bets found yet. Run `main.py` to populate the database._")
    else:
        lines.append("| Category | Volume | Settled | Win Rate | Expected Win Rate | Model Accuracy | Yield (ROI) |")
        lines.append("|---|---|---|---|---|---|---|")

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

            lines.append(f"| {cat_display} | {total_volume} | {settled} | {wr_str} | {exp_wr_str} | {model_str} | {yield_str} |")

    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(lines))

    print(f"[REPORTER] Report saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_report()
