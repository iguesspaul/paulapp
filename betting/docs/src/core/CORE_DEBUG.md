# Sentinel Quant Agent — `src/core/` (CORE_DEBUG) Documentation

## Files

### `config.py`
Contains global constants and configuration mappings.
- **`LEAGUES`**: List of dictionaries mapping Altenar Championship IDs to BetExplorer URL paths.
- **`INITIAL_BANKROLL`**: Starting capital used for Kelly stake calculations.
- **`KELLY_MULTIPLIER`**: Fractional factor (e.g., 0.20) used to reduce betting volatility.
- **`ALTENAR_BASE_URL / PARAMS`**: Endpoints and static parameters for the JustBet (Altenar) API.

### `database.py`
Handles all persistence logic for the SQLite `bets.db`.
- **`BettingDatabase.__init__(db_name)`**: Initializes the connection and ensures tables exist.
- **`create_tables()`**: Defines the schema for `bets` (legacy) and `simulated_bets` (tracking) tables.
- **`insert_simulated_bet(...)`**: Saves a +EV bet with match metadata and team info for later result settling.
- **`get_unsettled_matches()`**: Fetches a list of matches in the DB that don't have a result yet.
- **`settle_bet(bet_id, is_win, ...)`**: Updates a bet with its win/loss status and calculates actual profit.

### `orchestrator.py`
The central logic loop that connects all modules during a scan.
- **`run_full_scan(is_session)`**: Dynamically discovers all active leagues with prelive events from the casino API and processes up to 3 matches for each, capping total matches scanned at 50 to maximize coverage while maintaining performance.
- **`process_match(match, ...)`**: Coordinates harvesting, lambda calculation, and EV detection for a single event.
  - *Error Risk*: High. If sharp harvesters fail or API schema changes, this function logs a skip and continues.

### `reporter.py`
Generates the markdown analytics report.
- **`generate_report()`**: Queries the DB for aggregated stats per category and writes to `PERFORMANCE_SEGMENTATION.md`.

### `results_checker.py`
The automation engine for settling bets.
- **`resolve_results(db)`**: Finds unsettled matches in the DB and attempts to find their scores on BetExplorer.
- **`fetch_result_from_betexplorer(page, be_path, ...)`**: Scrapes the results page for a specific league and fuzzy-matches team names to find scores.
  - *Error Risk*: Medium. Website structure changes can break the scraper logic.
- **`evaluate_selection(category, selection, home_goals, away_goals)`**: A rules engine that determines if a specific bet (e.g., "Over 2.5") won based on the final score.

### `tracker.py`
The categorization and logging layer.
- **`BetTracker.log(...)`**: Normalizes raw market names into canonical categories and persists the bet to the DB.
- **`categorize(market_name)`**: Uses regex pattern matching to group similar markets (e.g., all O/U variations into "Total Goals").
