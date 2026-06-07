"""BetStore — simulated_bets CRUD and settlement queries."""

import sqlite3


class BetStore:
    """Persistence for simulated_bets (performance-tracked bets) and legacy bets."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ─── simulated_bets ──────────────────────────────────────────────────────────

    def insert(
        self,
        match_id,
        category,
        selection,
        odds,
        fair_odds,
        ev,
        stake=1.0,
        home_team=None,
        away_team=None,
        be_path=None,
        start_time=None,
    ):
        """Insert a new simulated bet, or update an existing unsettled one (dedup)."""
        import datetime as dt

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM simulated_bets WHERE match_id = ? AND category = ? AND selection = ? AND is_win IS NULL",
            (match_id, category, selection),
        )
        existing = cursor.fetchone()
        timestamp = dt.datetime.utcnow().isoformat()

        if existing:
            cursor.execute(
                "UPDATE simulated_bets SET odds = ?, fair_odds = ?, expected_value = ?, timestamp = ? WHERE id = ?",
                (odds, fair_odds, ev, timestamp, existing[0]),
            )
            self.conn.commit()
            return existing[0]

        cursor.execute(
            """INSERT INTO simulated_bets
               (match_id, home_team, away_team, be_path, start_time, timestamp,
                category, selection, odds, fair_odds, expected_value, stake)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                match_id,
                home_team,
                away_team,
                be_path,
                start_time,
                timestamp,
                category,
                selection,
                odds,
                fair_odds,
                ev,
                stake,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_unsettled_matches(self):
        """Return distinct (match_id, home_team, away_team, be_path, start_time) rows."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT DISTINCT match_id, home_team, away_team, be_path, start_time "
            "FROM simulated_bets WHERE is_win IS NULL AND home_team IS NOT NULL"
        )
        return cursor.fetchall()

    def get_unsettled_for_match(self, match_id):
        """Return all unsettled bet rows for a given match_id."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, category, selection, odds, stake "
            "FROM simulated_bets WHERE match_id = ? AND is_win IS NULL",
            (match_id,),
        )
        return cursor.fetchall()

    def settle(self, bet_id, is_win: bool, odds: float, stake: float):
        """Mark a single bet as settled and calculate actual_profit."""
        profit = (odds - 1) * stake if is_win else -stake
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE simulated_bets SET is_win = ?, actual_profit = ? WHERE id = ?",
            (1 if is_win else 0, profit, bet_id),
        )
        self.conn.commit()

    def get_category_stats(self):
        """Aggregate stats grouped by category for reporting."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT category,
                   COUNT(*) as total_volume,
                   SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN is_win IS NOT NULL THEN 1 ELSE 0 END) as settled,
                   AVG(1.0 / fair_odds) as avg_expected_win_rate,
                   SUM(actual_profit) as total_profit,
                   SUM(stake) as total_stake
            FROM simulated_bets
            GROUP BY category ORDER BY total_volume DESC
        """)
        return cursor.fetchall()

    def count_since(self, timestamp: str) -> int:
        """Count bets inserted after a given timestamp."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM simulated_bets WHERE timestamp >= ?", (timestamp,))
            return cursor.fetchone()[0]
        except Exception:
            return 0

    def total_count(self) -> int:
        """Total number of simulated_bets rows."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM simulated_bets")
            return cursor.fetchone()[0]
        except Exception:
            return 0

    # ─── legacy bets table ──────────────────────────────────────────────────────

    def insert_legacy(self, match_url, market_name, selection_name, price, fair_odds, ev):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO bets (match_url, market_name, selection_name, price, fair_odds, expected_value) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (match_url, market_name, selection_name, price, fair_odds, ev),
        )
        self.conn.commit()

    def get_best_legacy(self, match_url):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT market_name, selection_name, price, expected_value "
            "FROM bets WHERE match_url = ? AND expected_value > 0 "
            "ORDER BY expected_value DESC LIMIT 1",
            (match_url,),
        )
        return cursor.fetchone()
