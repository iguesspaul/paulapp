# Sentinel Quant Agent — `src/core/harvesters/` (HARVESTERS_DEBUG) Documentation

## Files

### `betexplorer.py`
Aggregator harvester that scrapes 1x2 and O/U odds for multiple books (Pinnacle, Bet365, etc.) via BetExplorer.
- **`harvest_sharp_odds(be_path, team_a, team_b)`**: Main entry point. Navigates to the match page and extracts odds tables.
  - *Inputs*: league path, home team, away team.
  - *Outputs*: List of dicts with book names and odds.
  - *Error Risk*: High. Relies on complex CSS selectors and fuzzy team matching.
- **`find_match_url(page, be_path, team_a, team_b)`**: Uses fuzzy logic to find the specific match link on the league results/upcoming page.

### `pinnacle.py`
Direct harvester for Pinnacle.com to get the highest quality "Source of Truth" odds.
- **`harvest(team_a, team_b)`**: Main entry point. Attempts to find the match on Pinnacle and scrape live sharp lines.
  - *Inputs*: home team, away team.
  - *Outputs*: Dictionary with 1x2 and O/U 2.5 odds.
  - *Error Risk*: Very High. Pinnacle has aggressive anti-bot measures and a dynamic React-based DOM.
- **`find_match_url(page, team_a, team_b)`**: Uses a Google Search "site:pinnacle.com" trick to find the direct match URL.
