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
- **`BettingDatabase.__init__(db_name)`**: Initializes the connection and ensures all tables exist.
- **`create_tables()`**: Defines schema for `bets` (legacy), `simulated_bets` (tracking), `bankroll_state` (single-row ledger), and `session_summary` (scan/settlement event log).
- **`insert_simulated_bet(...)`**: Saves a +EV bet with match metadata and team info for later result settling. Stake is now the Kelly-weighted dollar amount (not flat $1.00).
- **`get_unsettled_matches()`**: Fetches a list of matches in the DB that don't have a result yet.
- **`settle_bet(bet_id, is_win, ...)`**: Updates a bet with its win/loss status and calculates actual profit.
- **`get_bankroll_balance()`**: Returns current bankroll from single-row ledger. Initializes to $5,000 on first call.
- **`set_bankroll_balance(new_balance)`**: Overwrites bankroll after stake deduction (scan) or P&L addition (settlement).
- **`record_session_summary(...)`**: Appends one row to `session_summary` capturing either a scan (stakes committed, theoretical EV) or settlement (actual P&L).
- **`get_session_summaries(limit)`**: Returns the N most recent session rows for the PERFORMANCE report.
- **`get_bankroll_summary()`**: Returns dict with current balance, last update timestamp, and aggregate realized P&L.

### `orchestrator.py`
The central logic loop that connects all modules during a scan.
- **`run_full_scan(is_session)`**: Dynamically discovers all active leagues with prelive events from the casino API and processes up to 5 matches per league, capping total matches scanned at 100. Resets session accumulators. After all matches, deducts total committed stakes from bankroll and records a session summary.
- **`process_match(match, ...)`**: Coordinates harvesting (Pinnacle arcadia API + BetExplorer Playwright), lambda calculation (solver → consensus → fallback), and EV detection for a single event.
  - *Kelly stake sizing*: Each +EV bet's stake is `fractional_kelly × current_bankroll` (20% fractional Kelly). The stake is stored in the DB and deducted from bankroll at session end.
  - *Session accumulators*: `_session_stake_total`, `_session_ev_total`, `_session_bets_logged` track aggregate risk across all bets in one scan.
  - *Fallback bet filtering*: When using the hardcoded default lambda (2.65) with no real sharp odds backing, bets are printed as `[FALLBACK BET (SKIPPED)]` and never logged to the `simulated_bets` table during session runs.
  - *Error Risk*: High. If sharp harvesters fail or API schema changes, this function logs a skip and continues.

### `reporter.py`
Generates the markdown analytics report with three sections.
- **`generate_report()`**: 
  1. **Bankroll Overview** — current balance, total realized P&L, overall ROI
  2. **Recent Sessions** — last 10 session_summary rows with bets, stake, EV value, P&L, balance
  3. **Category Performance** — per-category stats plus Stake Exposure ($) and P&L ($)

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
