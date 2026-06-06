# Sentinel Quant Agent — `src/collectors/harvesters/` (HARVESTERS_DEBUG) Documentation

## Architecture Overview

Both harvesters fetch sharp (vig-free) odds from market-making bookmakers.
The orchestrator merges results and passes them to the consensus solver.

## Files

### `pinnacle.py`
Direct harvester for Pinnacle via their public arcadia REST API. No browser automation needed.

- **`harvest(pin_path, team_a, team_b, league_name, country_name)`**: Main entry point.
  - *Flow*:
    1. Fetch all soccer leagues from `/sports/29/leagues?all=false`
    2. Find matching league via alias exact match or token-set intersection
    3. Fetch matchups from `/leagues/{leagueId}/matchups`
    4. Find best matchup by `name_match_score` on team names (with home/away swap detection)
    5. Fetch markets: tries league-level `/leagues/{leagueId}/markets/straight` first (bundles all
       matchups — never 401s), then per-matchup `/matchups/{id}/markets/straight` with 3-retry
       exponential backoff and alternate `/markets` fallback
    6. Auto-detects 2-way market counterpart when only 1 market (moneyline) is found: searches
       league for a matchup with the same team names but more markets (including O/U 2.5)
    7. Parse prices: maps `participantId → name/role` via matchup participants array, falls back
       to ordinal position when participants have no IDs (national club leagues)
  - *Inputs*: `pin_path` (e.g. `"england-premier-league"`), team_a, team_b, optional league/country
  - *Outputs*: `{"book": "Pinnacle Direct", "odds": {"1": ..., "X": ..., "2": ..., "Over2.5": ..., "Under2.5": ...}}`
  - *Key functions*:
    - `_find_league(leagues, pin_path, known_name)` — exact alias match, then token-set intersection
    - `_find_matchup(matchups, team_a, team_b)` — fuzzy name matching with swap handling
    - `_get_markets(matchup_id, league_id, participants)` — league-level → per-matchup → 2-way fallback
    - `_parse_markets(markets, participants)` — extracts 1x2 and O/U 2.5 from market list
    - `_build_participant_map(participants)` — maps participantIds to home/draw/away roles

### `betexplorer.py`
Aggregator that extracts odds from BetExplorer league pages via Playwright.

- **`harvest_sharp_odds(be_path, team_a, team_b, league_name, country_name)`**: Main entry point.
  - *Flow*:
    1. Resolve league URL via search API (with alias-augmented search terms) or be_path fallback
    2. For multi-group leagues (FNL 2 groups), cascades through all matching URLs
    3. Scan all `<tr>` rows for team-name links (containing " - ") and extract decimal odds
       from `<button>` elements (filter: value > 1.0)
    4. Try JSON odds endpoints first (`/match-odds/{id}/1/1x2/`), fall back to inline odds from
       table row, fall back to DOM extraction on match page
  - *Inputs*: `be_path` (e.g. `"soccer/england/premier-league"`), team_a, team_b, league_name, country_name
  - *Outputs*: `[{"book": "Pinnacle", "odds": {...}}, {"book": "bet365", ...}, ...]`
  - *Key functions*:
    - `_search_league_url(name, country, all_matches)` — BetExplorer search API with alias
    - `_find_match_id(page, url, team_a, team_b)` — scans tr rows for names + inline odds
    - `_fetch_json_odds(match_id, market)` — JSON endpoint (mostly deprecated)
    - `_parse_json_1x2(data)` / `_parse_json_ou(data)` — JSON response parsers
    - `_dom_fallback_odds(page, match_id, books)` — last-resort DOM extraction

### `normalizer.py`
Shared utilities used by both harvesters.

- **`LEAGUE_ALIASES`**: Mapping of Altenar (casino) league names → sharp platform equivalents.
  Key format: `(be_path_league_slug, country_slug)`. Fields: `betexplorer_search`, `pinnacle_name`.
- **`normalize(name)`**: Unicode-stripping, punctuation removal, club suffix stripping.
- **`name_match_score(a, b)`**: Word-set intersection ratio (|A∩B| / max(|A|,|B|)).
- **`american_to_decimal(american)`**: Convert American odds to decimal odds.
- **`get_alias(slug, country)`**: Lookup wrapper for LEAGUE_ALIASES dict.
- **`make_slug(s)`**: URL-safe slug from any string.

## Key Scraping Risks

1. **Pinnacle 401 on per-matchup markets**: ~20% of matchups return 401 on the direct endpoint.
   Mitigated by using the league-level endpoint which bundles all matchup markets without auth.
2. **BetExplorer JSON odds 404**: The `/match-odds/{id}/1/x/` endpoint is deprecated.
   Mitigated by inline odds extraction from the league page table.
3. **Platform gaps**: Many leagues (Russian lower divisions, New Zealand, U20) aren't offered
   by either sharp source. The system falls through to the fallback lambda chain.
4. **Rate limiting**: Both platforms may rate-limit. BetExplorer uses Playwright with stealth.js.
