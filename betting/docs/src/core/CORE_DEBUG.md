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
- **`run_full_scan(is_session)`**: Dynamically discovers all active leagues with prelive events from the casino API and processes up to 5 matches per league, capping total matches scanned at 100 to maximize coverage.
- **`process_match(match, ...)`**: Coordinates harvesting (Pinnacle arcadia API + BetExplorer Playwright), lambda calculation (solver → consensus → fallback), and EV detection for a single event.
  - *Fallback bet filtering*: When using the hardcoded default lambda (2.65) with no real sharp odds backing, bets are printed as `[FALLBACK BET (SKIPPED)]` and never logged to the `simulated_bets` table during session runs. This prevents performance tracking distortion.
  - *Error Risk*: High. If sharp harvesters fail or API schema changes, this function logs a skip and continues.

### `reporter.py`
Generates the markdown analytics report.
- **`generate_report()`**: Queries the DB for aggregated stats per category and writes to `PERFORMANCE_SEGMENTATION.md`.

### `results_checker.py`
The automation engine for settling bets.
- **`resolve_results(db)`**: Finds unsettled matches in the DB, queries SofaScore daily schedules and search endpoints via Playwright, filters by kickoff time, and fetches detailed scores.
  - *Optimization*: Skips any matches that started less than 2.5 hours ago to avoid unnecessary online lookups.
  - *Time drift & Fuzzy matching*: Queries SofaScore scheduled events for the match date (and adjacent dates to handle time drift), matching team names using cleaning and SequenceMatcher/subset metrics. Ensures kickoff timestamp is within 24 hours of target.
  - *Swapped team handling*: Automatically detects if the home/away teams are swapped in SofaScore's listing relative to our database and swaps the parsed scores accordingly.
- **`evaluate_selection(category, selection, h1, a1, h2, a2, home_team=None, away_team=None)`**: A rules engine that determines if a specific bet won based on the half and full-time scores. Uses robust helper functions (`evaluate_double_chance`, `evaluate_1x2`, `evaluate_total`, `evaluate_btts`) to correctly match team names and standard formats.

### `tracker.py`
The categorization and logging layer.
- **`BetTracker.log(...)`**: Normalizes raw market names into canonical categories and persists the bet to the DB.
- **`categorize(market_name)`**: Uses regex pattern matching to group similar markets (e.g., all O/U variations into "Total Goals").
