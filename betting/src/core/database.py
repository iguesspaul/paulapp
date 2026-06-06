import sqlite3
from datetime import datetime, timezone
from typing import Optional

# Initial bankroll — matches config.py, kept here as default so table init is self-contained
DEFAULT_INITIAL_BANKROLL = 5000.0

class BettingDatabase:
    def __init__(self, db_name="bets.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Legacy bets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_url TEXT,
                market_name TEXT,
                selection_name TEXT,
                price REAL,
                fair_odds REAL,
                expected_value REAL
            )
        ''')
        # New simulated_bets table for performance attribution
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulated_bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT,
                home_team TEXT,
                away_team TEXT,
                be_path TEXT,
                start_time TEXT,
                timestamp TEXT,
                category TEXT,
                selection TEXT,
                odds REAL,
                fair_odds REAL,
                expected_value REAL,
                stake REAL DEFAULT 1.0,
                is_win INTEGER DEFAULT NULL,
                actual_profit REAL DEFAULT NULL
            )
        ''')
        # Bankroll state — single-row ledger (id 1 always holds the current balance)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bankroll_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                balance REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO bankroll_state (id, balance, updated_at)
            VALUES (1, ?, ?)
        ''', (DEFAULT_INITIAL_BANKROLL, datetime.now(timezone.utc).isoformat()))
        # Session summary — one row per run_session / check_results invocation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                total_stake_committed REAL DEFAULT 0.0,
                theoretical_ev_profit REAL DEFAULT 0.0,
                bets_logged INTEGER DEFAULT 0,
                actual_pnl REAL DEFAULT NULL,
                bets_settled INTEGER DEFAULT 0,
                bets_skipped INTEGER DEFAULT 0,
                balance_before REAL,
                balance_after REAL,
                timestamp TEXT NOT NULL
            )
        ''')
        # Attempt to add new columns to existing DBs without breaking
        for col, coltype in [("home_team", "TEXT"), ("away_team", "TEXT"), ("be_path", "TEXT"), ("start_time", "TEXT")]:
            try:
                cursor.execute(f'ALTER TABLE simulated_bets ADD COLUMN {col} {coltype}')
            except Exception:
                pass
        self.conn.commit()

    def insert_bet(self, match_url, market_name, selection_name, price, fair_odds, ev):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO bets (match_url, market_name, selection_name, price, fair_odds, expected_value)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (match_url, market_name, selection_name, price, fair_odds, ev))
        self.conn.commit()

    def insert_simulated_bet(self, match_id, category, selection, odds, fair_odds, ev,
                               stake=1.0, home_team=None, away_team=None, be_path=None, start_time=None):
        cursor = self.conn.cursor()
        # Check if an unsettled bet already exists for this match, category, and selection
        cursor.execute('''
            SELECT id FROM simulated_bets 
            WHERE match_id = ? AND category = ? AND selection = ? AND is_win IS NULL
        ''', (match_id, category, selection))
        existing = cursor.fetchone()

        timestamp = datetime.utcnow().isoformat()

        if existing:
            # Update existing bet with latest metrics and timestamp
            cursor.execute('''
                UPDATE simulated_bets
                SET odds = ?, fair_odds = ?, expected_value = ?, timestamp = ?
                WHERE id = ?
            ''', (odds, fair_odds, ev, timestamp, existing['id']))
            self.conn.commit()
            return existing['id']

        cursor.execute('''
            INSERT INTO simulated_bets
                (match_id, home_team, away_team, be_path, start_time, timestamp, category, selection, odds, fair_odds, expected_value, stake)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (match_id, home_team, away_team, be_path, start_time,
              timestamp, category, selection, odds, fair_odds, ev, stake))
        self.conn.commit()
        return cursor.lastrowid

    def get_unsettled_matches(self):
        """Returns distinct (match_id, home_team, away_team, be_path, start_time) for all unsettled bets."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT match_id, home_team, away_team, be_path, start_time
            FROM simulated_bets
            WHERE is_win IS NULL AND home_team IS NOT NULL
        ''')
        return cursor.fetchall()

    def settle_bet(self, bet_id, is_win: bool, odds: float, stake: float):
        """Marks a single bet as settled and calculates actual_profit."""
        profit = (odds - 1) * stake if is_win else -stake
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE simulated_bets
            SET is_win = ?, actual_profit = ?
            WHERE id = ?
        ''', (1 if is_win else 0, profit, bet_id))
        self.conn.commit()

    def get_unsettled_bets_for_match(self, match_id):
        """Returns all unsettled bet rows for a given match_id."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, category, selection, odds, stake
            FROM simulated_bets
            WHERE match_id = ? AND is_win IS NULL
        ''', (match_id,))
        return cursor.fetchall()

    def get_best_bet(self, match_url):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT market_name, selection_name, price, expected_value
            FROM bets
            WHERE match_url = ? AND expected_value > 0
            ORDER BY expected_value DESC
            LIMIT 1
        ''', (match_url,))
        return cursor.fetchone()

    def get_category_stats(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT
                category,
                COUNT(*) as total_volume,
                SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN is_win IS NOT NULL THEN 1 ELSE 0 END) as settled,
                AVG(1.0 / fair_odds) as avg_expected_win_rate,
                SUM(actual_profit) as total_profit,
                SUM(stake) as total_stake
            FROM simulated_bets
            GROUP BY category
            ORDER BY total_volume DESC
        ''')
        return cursor.fetchall()

    # ─── Bankroll Management ──────────────────────────────────────────────────────

    def get_bankroll_balance(self) -> float:
        """Returns the current bankroll balance. Initializes to DEFAULT if empty."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT balance FROM bankroll_state WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return row["balance"]
        cursor.execute('''
            INSERT OR IGNORE INTO bankroll_state (id, balance, updated_at)
            VALUES (1, ?, ?)
        ''', (DEFAULT_INITIAL_BANKROLL, datetime.now(timezone.utc).isoformat()))
        self.conn.commit()
        return DEFAULT_INITIAL_BANKROLL

    def set_bankroll_balance(self, new_balance: float):
        """Overwrites the current bankroll balance."""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE bankroll_state SET balance = ?, updated_at = ? WHERE id = 1
        ''', (new_balance, datetime.now(timezone.utc).isoformat()))
        self.conn.commit()

    def record_session_summary(self, session_type: str, *,
                               total_stake_committed: float = 0.0,
                               theoretical_ev_profit: float = 0.0,
                               bets_logged: int = 0,
                               actual_pnl: float | None = None,
                               bets_settled: int = 0,
                               bets_skipped: int = 0,
                               balance_before: float | None = None,
                               balance_after: float | None = None):
        """Records one row in the session_summary ledger."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO session_summary
                (session_type, total_stake_committed, theoretical_ev_profit,
                 bets_logged, actual_pnl, bets_settled, bets_skipped,
                 balance_before, balance_after, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_type,
            total_stake_committed,
            theoretical_ev_profit,
            bets_logged,
            actual_pnl,
            bets_settled,
            bets_skipped,
            balance_before,
            balance_after,
            datetime.now(timezone.utc).isoformat()
        ))
        self.conn.commit()

    def get_session_summaries(self, limit: int = 10):
        """Returns the most recent session summaries for the PERFORMANCE report."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM session_summary
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()

    def get_bankroll_summary(self) -> dict:
        """Aggregate stats for the PERFORMANCE report header."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT balance, updated_at FROM bankroll_state WHERE id = 1")
        bal = cursor.fetchone()
        cursor.execute('''
            SELECT
                COALESCE(SUM(CASE WHEN actual_pnl IS NOT NULL THEN actual_pnl ELSE 0 END), 0) as total_pnl
            FROM session_summary WHERE session_type = 'settlement'
        ''')
        pnl_row = cursor.fetchone()
        return {
            "current_balance": bal["balance"] if bal else DEFAULT_INITIAL_BANKROLL,
            "updated_at": bal["updated_at"] if bal else None,
            "total_realized_pnl": pnl_row["total_pnl"] if pnl_row else 0.0,
        }
