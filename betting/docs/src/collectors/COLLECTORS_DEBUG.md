# Sentinel Quant Agent — `src/collectors/` (COLLECTORS_DEBUG) Documentation

This folder is the data ingestion, collection, and parsing layer. It handles downloading sharp odds, scraping casino fixtures, parsing complex market selections, and mapping them to our probability models.

## Folders

### `harvesters/`
Sub-package containing custom scraping adapters for elite sharp bookmakers (e.g. Pinnacle, BetExplorer) to build our consensus lambda models.

## Files

### `scraper.py`
Automates the discovery and fetching of upcoming matches and odds from target league sites.
- **`find_matches(champ_id)`**: Locates upcoming matches in the casino for a specific championship ID. Extracts event start times using timezone-aware UTC datetime formatting to enable accurate 48-hour filtering and result checking.
- **`discover_active_leagues()`**: Dynamically queries the Altenar sports menu API to discover all active soccer championships with prelive events, returning normalized paths.
- **`fetch_page_json(url, output_path)`**: Fetches underlying API JSON data or page contents.

### `casino_parser.py`
Extracts relevant betting markets from the raw Altenar JSON.
- **`extract_markets(file_path)`**: Filters raw Altenar data points for target markets (e.g. Correct Score, BTTS, and Totals).
  - *Inputs*: Path to a JSON file in `data/`.
  - *Outputs*: Structured list of markets and selections.
  - *Error Risk*: Medium. If the casino changes its JSON nesting structure, this will return empty lists.

### `market_resolver.py`
The bridge between human market names and the mathematical Poisson grids.
- **`resolve(market_name, selection_name)`**: Maps market strings (e.g., "1st half - 1:0") to coordinates in the Full Match, 1st Half, or 2nd Half Poisson grids.
  - *Inputs*: Market name string, Selection name string.
  - *Outputs*: Float (Fair Probability).
- **`_get_active_grid(market_name)`**: Identifies the correct grid (Full Match, 1H, or 2H) to evaluate.
