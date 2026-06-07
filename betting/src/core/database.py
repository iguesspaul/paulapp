import contextlib
import sqlite3
from datetime import UTC, datetime

from src.core.stores.bankroll_store import DEFAULT_INITIAL_BANKROLL, BankrollStore
from src.core.stores.bet_store import BetStore


class BettingDatabase:
    """Database facade — manages schema creation and composes the domain stores.

    Stores:
        .bets      — BetStore (simulated_bets CRUD + legacy bets)
        .bankroll   — BankrollStore (bankroll balance + session ledger)

    Backward-compat methods delegate to the appropriate store.
    New code should prefer `db.bets.*` and `db.bankroll.*` directly.
    """

    def __init__(self, db_name="bets.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row
        self.bets = BetStore(self.conn)
        self.bankroll = BankrollStore(self.conn)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Legacy bets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_url TEXT, market_name TEXT, selection_name TEXT,
                price REAL, fair_odds REAL, expected_value REAL
            )
        """)
        # New simulated_bets table for performance attribution
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulated_bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT, home_team TEXT, away_team TEXT,
                be_path TEXT, start_time TEXT, timestamp TEXT,
                category TEXT, selection TEXT, odds REAL,
                fair_odds REAL, expected_value REAL, stake REAL DEFAULT 1.0,
                is_win INTEGER DEFAULT NULL, actual_profit REAL DEFAULT NULL
            )
        """)
        # Bankroll state — single-row ledger (id 1 always holds the current balance)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bankroll_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                balance REAL NOT NULL, updated_at TEXT NOT NULL
            )
        """)
        cursor.execute(
            "INSERT OR IGNORE INTO bankroll_state (id, balance, updated_at) VALUES (1, ?, ?)",
            (DEFAULT_INITIAL_BANKROLL, datetime.now(UTC).isoformat()),
        )
        # Session summary — one row per run_session / check_results invocation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                total_stake_committed REAL DEFAULT 0.0,
                theoretical_ev_profit REAL DEFAULT 0.0,
                bets_logged INTEGER DEFAULT 0,
                actual_pnl REAL DEFAULT NULL,
                bets_settled INTEGER DEFAULT 0,
                bets_skipped INTEGER DEFAULT 0,
                balance_before REAL, balance_after REAL,
                timestamp TEXT NOT NULL
            )
        """)
        # Migration: add columns that may be missing in existing DBs
        for col, coltype in [
            ("home_team", "TEXT"),
            ("away_team", "TEXT"),
            ("be_path", "TEXT"),
            ("start_time", "TEXT"),
        ]:
            with contextlib.suppress(Exception):
                cursor.execute(f"ALTER TABLE simulated_bets ADD COLUMN {col} {coltype}")
        self.conn.commit()

    # ─── Backward-compat delegates ──────────────────────────────────────────────

    def insert_bet(self, match_url, market_name, selection_name, price, fair_odds, ev):
        return self.bets.insert_legacy(match_url, market_name, selection_name, price, fair_odds, ev)

    def insert_simulated_bet(self, **kw):
        return self.bets.insert(**kw)

    def get_unsettled_matches(self):
        return self.bets.get_unsettled_matches()

    def get_unsettled_bets_for_match(self, match_id):
        return self.bets.get_unsettled_for_match(match_id)

    def settle_bet(self, bet_id, is_win, odds, stake):
        return self.bets.settle(bet_id, is_win, odds, stake)

    def get_best_bet(self, match_url):
        return self.bets.get_best_legacy(match_url)

    def get_category_stats(self):
        return self.bets.get_category_stats()

    def get_bankroll_balance(self):
        return self.bankroll.get_balance()

    def set_bankroll_balance(self, bal):
        return self.bankroll.set_balance(bal)

    def get_bankroll_summary(self):
        return self.bankroll.get_summary()

    def record_session_summary(self, **kw):
        return self.bankroll.record_session(**kw)

    def get_session_summaries(self, limit=10):
        return self.bankroll.get_recent_sessions(limit)
