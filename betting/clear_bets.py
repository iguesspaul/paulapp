import os
import sqlite3


def clear_all_bets():
    db_path = "bets.db"
    if not os.path.exists(db_path):
        print(f"[ERROR] Database {db_path} not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check total count before clearing
        cursor.execute("SELECT COUNT(*) FROM bets")
        bets_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM simulated_bets")
        sim_bets_count = cursor.fetchone()[0]

        print(
            f"[INFO] Currently in database: {bets_count} legacy bets, {sim_bets_count} simulated bets."
        )

        # Clear tables
        cursor.execute("DELETE FROM bets")
        cursor.execute("DELETE FROM simulated_bets")
        conn.commit()
        conn.close()

        print(f"[SUCCESS] Cleared all bets from {db_path}!")

        # Regenerate empty performance segmentation report
        try:
            from src.core.reporter import generate_report

            generate_report()
            print("[SUCCESS] Regenerated empty PERFORMANCE_SEGMENTATION.md report!")
        except Exception as re:
            print(f"[WARNING] Failed to regenerate report: {re}")

    except Exception as e:
        print(f"[ERROR] Failed to clear bets: {e}")


if __name__ == "__main__":
    clear_all_bets()
