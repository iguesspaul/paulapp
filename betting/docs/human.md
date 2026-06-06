# Sentinel Quant Betting Agent: System Overview

This script mathematically exploits sports betting casinos using advanced quantitative methods by identifying mispriced odds relative to the global "sharp" market.

## How It Works: Step-by-Step

### 1. The Sharp Consensus (The Intelligence)
We do not attempt to predict match outcomes through intuition. Instead, we pull live odds from multiple "Sharp" sources in parallel:
- **Pinnacle API**: Pulls odds from `guest.api.arcadia.pinnacle.com` REST API — no browser automation needed. Uses league-level markets endpoint for reliability, with per-matchup retry fallback. Handles both 3-way (moneyline) and 2-way (full market including O/U) matchup formats via intelligent counterpart detection.
- **BetExplorer**: Scrapes league pages via Playwright, extracting decimal odds from table rows. Falls back to inline odds (from `<button>` elements) when the JSON odds endpoint is unavailable.
- **1x2-Only Solver**: When O/U 2.5 odds aren't available, the solver can estimate lambdas from just the 1x2 moneyline using 3-constraint fitting (Home/Draw/Away probabilities → 2-parameter Poisson grid).
- **De-Vigging & Weighting**: We remove the bookmaker's margin and apply a weighted consensus (**70% Pinnacle Direct**, **30% others**) to derive the final **Match Lambda** ($\lambda$). This variable represents the mathematically expected goal frequency of the match.

### 2. The Probability Grid (The Engine)
The Match Lambda is fed into a **Poisson Distribution** model to generate a **7x7 Probability Matrix**.
- This grid contains the exact mathematical probability for every scoreline from 0-0 to 6-6.
- It automatically accounts for **Home Advantage** (58/42 split) and **Match Timing** (1st Half vs 2nd Half distribution).

### 3. The Scraper & Parser (The Data)
The system connects directly to the target casino's backend API.
- **Speed**: Downloads thousands of market odds in milliseconds without simulating browser clicks.
- **Coverage**: Dynamically discovers and scans ALL active soccer leagues globally (e.g. up to 140+ championships), prioritizing leagues by activity and capped at a maximum of 50 total matches per scan session. This ensures maximum coverage and discovers a far wider range of +EV betting opportunities automatically.

### 4. The Market Resolver (The Translator)
The casino lists bets in plain English (e.g., *"1x2 & Both Teams to Score"*).
- The Resolver maps these strings to specific filters on the 7x7 Probability Grid.
- It calculates the "Fair Price" for complex combined markets by summing the relevant grid coordinates.

### 5. Expected Value (EV) Calculation
The system compares the casino's price against our Fair Price.
- **Formula**: $EV = (Fair\_Prob \times Casino\_Odds) - 1.0$
- **Edge Detection**: Only bets with an EV between **5% and 25%** are flagged. These are mathematically "mispriced" opportunities.

### 6. Performance Attribution & Category Tracking
Every +EV bet is **categorized** by its parent market type and logged to the `simulated_bets` table in `bets.db` using a flat **$1.00 simulation stake**.
Bets calculated using fallback lambdas (no real sharp odds backing them) are automatically **skipped** during session runs to prevent performance tracking distortion.
- **Categorization**: Raw casino strings like `"1st Half - 1x2 & Both Teams to Score"` are normalized into canonical groups (e.g., `"1H 1x2 & BTTS"`) so performance can be compared across matches.
- **Line Stability**: Even duplicate bets (same selection scraped in two runs) are logged separately. A selection appearing multiple times at the same price indicates a **stable, confident line**.
- **Analytics Report**: The system automatically generates ROI reports in the `docs/` folder. It shows:
  - **Volume**: How often this category appears as +EV.
  - **Win Rate vs Expected Win Rate**: Calibration of our Poisson model.
  - **Yield (ROI)**: Whether the category is actually profitable over time.
  - **Golden Categories**: High volume + positive yield = the casino consistently misprices this market type.

---

## Operational Guide

### 1. Daily Entry Point (`run_session.py`)
This is the primary script you should run 2-3x per day. It orchestrates the entire workflow:
1. **Settle Results**: Checks for finished matches and updates `is_win` in the database.
   - *Optimization*: Automatically skips checking matches that started less than 2.5 hours ago, dramatically speeding up the check-results routine and avoiding unnecessary network calls for matches still in progress.
   - *Unified Lookup*: The system leverages SofaScore's JSON endpoints. It maps the event's UTC date and queries daily schedules (checking match day, day before, and day after to handle timezone drift).
   - *Fuzzy Match & Timestamp Alignment*: Team names are cleaned and fuzzy-matched using substring check, word set intersection, and SequenceMatcher. The system filters candidate events by ensuring kickoff is within a 24-hour window, selecting the closest start time.
   - *Direct JSON Extraction*: Authoritative match details (final score and non-cumulative period goals for 1st and 2nd half) are extracted directly from `/api/v1/event/{id}` JSON structure, eliminating fragile CSS scraping. It also automatically handles home/away team swaps.
2. **Scan Leagues**: Discovers +EV bets and logs them for tracking.
3. **Generate Report**: Updates `PERFORMANCE_SEGMENTATION.md` with the latest ROI data.

```bash
python3 run_session.py
```

### 2. Manual Scan (`main.py`)
Use this for a quick check of current odds without triggering the result checker or report generation.
_Note: Running this frequently will increase 'Volume' in the report for the same bets, which tracks Line Stability._

---

## Data & Match Tracking
All detailed information about matches and their corresponding bets is stored in **`bets.db`**.
- **Simulated Bets Table**: Contains `match_id`, `home_team`, `away_team`, `be_path`, `timestamp`, `category`, `selection`, `odds`, and results.
- **Querying**: You can use any SQLite viewer (like DB Browser for SQLite) to see exactly which bets were placed for each match.

---
