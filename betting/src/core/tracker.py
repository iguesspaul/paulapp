import re

# Maps raw market name strings to canonical category names
# Order matters — more specific patterns must come before generic ones.
CATEGORY_MAP = [
    # Half-specific compound markets
    (r"1st half.*correct score", "1H Correct Score"),
    (r"2nd half.*correct score", "2H Correct Score"),
    (r"halftime.?fulltime.*correct", "HT/FT Correct Score"),
    (r"halftime.?fulltime", "HT/FT Result"),
    (r"1st half.*1x2.*both teams", "1H 1x2 & BTTS"),
    (r"2nd half.*1x2.*both teams", "2H 1x2 & BTTS"),
    (r"1st half.*double chance.*both", "1H Double Chance & BTTS"),
    (r"2nd half.*double chance.*both", "2H Double Chance & BTTS"),
    (r"1st half.*both teams", "1H BTTS"),
    (r"2nd half.*both teams", "2H BTTS"),
    (r"1st.?2nd half.*both teams", "HT/FT BTTS Split"),
    (r"1st half.*1x2.*total", "1H 1x2 & Total"),
    (r"2nd half.*1x2.*total", "2H 1x2 & Total"),
    (r"1st half.*total", "1H Total Goals"),
    (r"2nd half.*total", "2H Total Goals"),
    (r"1st half.*corners", "1H Total Corners"),
    # Full match compound markets
    (r"1x2.*both teams", "1x2 & BTTS"),
    (r"double chance.*both teams", "Double Chance & BTTS"),
    (r"double chance.*total", "Double Chance & Total"),
    (r"draw or both teams", "Draw or BTTS"),
    (r".*or both teams", "Team Win or BTTS"),
    (r"halftime.?fulltime.*total", "HT/FT & Total"),
    # Pure markets
    (r"multiscore", "Multiscores"),
    (r"correct score", "Correct Score"),
    (r"both teams to score|btts", "BTTS"),
    (r"total corners", "Total Corners"),
    (r"total bookings", "Total Bookings"),
    (r".*bookings", "Team Bookings"),
    (r"1x2.*total", "1x2 & Total"),
    (r".*total", "Total Goals"),
    (r"winning margin", "Winning Margin"),
    (r"1x2|match winner", "1x2 (Match Result)"),
]


def categorize(market_name: str) -> str:
    """Returns the canonical category for a raw market name string."""
    mn = market_name.lower()
    for pattern, category in CATEGORY_MAP:
        if re.search(pattern, mn):
            return category
    return "Other"


class BetTracker:
    def __init__(self, db):
        self.db = db

    def log(
        self,
        match_id: str,
        market_name: str,
        selection: str,
        odds: float,
        fair_odds: float,
        ev: float,
        stake: float = 1.0,
        home_team: str | None = None,
        away_team: str | None = None,
        be_path: str | None = None,
        start_time: str | None = None,
    ):
        """
        Categorizes the bet and persists it to simulated_bets.
        Detects and updates existing unsettled bets to prevent duplication while tracking line stability.
        """
        category = categorize(market_name)
        row_id = self.db.insert_simulated_bet(
            match_id=match_id,
            category=category,
            selection=selection,
            odds=odds,
            fair_odds=fair_odds,
            ev=ev,
            stake=stake,
            home_team=home_team,
            away_team=away_team,
            be_path=be_path,
            start_time=start_time,
        )
        return category, row_id
