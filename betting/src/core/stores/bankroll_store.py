"""BankrollStore — bankroll balance and session ledger persistence."""

import sqlite3
from datetime import UTC, datetime

DEFAULT_INITIAL_BANKROLL = 5000.0


class BankrollStore:
    """Persistence for bankroll_state (singleton-row balance) and session_summary."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ─── bankroll_state ─────────────────────────────────────────────────────────

    def get_balance(self) -> float:
        cursor = self.conn.cursor()
        cursor.execute("SELECT balance FROM bankroll_state WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return row[0]
        # Initialize with default
        cursor.execute(
            "INSERT OR IGNORE INTO bankroll_state (id, balance, updated_at) VALUES (1, ?, ?)",
            (DEFAULT_INITIAL_BANKROLL, datetime.now(UTC).isoformat()),
        )
        self.conn.commit()
        return DEFAULT_INITIAL_BANKROLL

    def set_balance(self, new_balance: float):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE bankroll_state SET balance = ?, updated_at = ? WHERE id = 1",
            (new_balance, datetime.now(UTC).isoformat()),
        )
        self.conn.commit()

    def get_summary(self) -> dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT balance, updated_at FROM bankroll_state WHERE id = 1")
        bal = cursor.fetchone()
        cursor.execute("""
            SELECT COALESCE(SUM(CASE WHEN actual_pnl IS NOT NULL THEN actual_pnl ELSE 0 END), 0) as total_pnl
            FROM session_summary WHERE session_type = 'settlement'
        """)
        pnl_row = cursor.fetchone()
        return {
            "current_balance": bal[0] if bal else DEFAULT_INITIAL_BANKROLL,
            "updated_at": bal[1] if bal else None,
            "total_realized_pnl": pnl_row[0] if pnl_row else 0.0,
        }

    # ─── session_summary ────────────────────────────────────────────────────────

    def record_session(
        self,
        session_type: str,
        *,
        total_stake_committed=0.0,
        theoretical_ev_profit=0.0,
        bets_logged=0,
        actual_pnl=None,
        bets_settled=0,
        bets_skipped=0,
        balance_before=None,
        balance_after=None,
    ):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO session_summary
               (session_type, total_stake_committed, theoretical_ev_profit,
                bets_logged, actual_pnl, bets_settled, bets_skipped,
                balance_before, balance_after, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_type,
                total_stake_committed,
                theoretical_ev_profit,
                bets_logged,
                actual_pnl,
                bets_settled,
                bets_skipped,
                balance_before,
                balance_after,
                datetime.now(UTC).isoformat(),
            ),
        )
        self.conn.commit()

    def get_recent_sessions(self, limit: int = 10):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM session_summary ORDER BY timestamp DESC LIMIT ?", (limit,))
        return cursor.fetchall()
