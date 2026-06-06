# Results Checker Architecture

## Purpose
Automatically queries SofaScore's JSON endpoints to find the exact matching fixture, extracts final/period scores, and settles all unsettled bets in `simulated_bets`.

## Main Functions

### `clean_team_name(name)`
**Purpose**: Cleans team names for fuzzy matching by lowercasing, removing accents/diacritics, removing common soccer suffixes (FC, CF, United, Utd, City, Town, etc.), and removing non-alphanumeric characters.

---

### `check_name_match(t1, t2)`
**Purpose**: Determines if two team names refer to the same team.

**Logic Flow**:
1. Clean both names using `clean_team_name`.
2. Check if one cleaned name is a substring of the other.
3. Calculate similarity ratio using `difflib.SequenceMatcher` (threshold > 0.65).
4. Perform a word-level set intersection check (returns True if one set of words is a subset of the other).

---

### `fetch_sofascore_json(page, url)`
**Purpose**: Executes a `fetch` command inside the Playwright browser context to leverage cookies/headers and bypass Cloudflare anti-bot blocks.

---

### `resolve_results(db)`
**Purpose**: Main orchestration function called by `run_session.py` and `check_results.py`.

**Logic Flow**:
1. Gets all unsettled matches from the database.
2. For each match:
   - Skips if started less than 2.5 hours ago.
   - Computes UTC date and target timestamp from `start_time`.
   - Queries the scheduled events API (`/api/v1/sport/football/scheduled-events/{date}`) for the match date, the day before, and the day after (handles timezone drift).
   - Filters events by matching team names (fuzzy logic) and ensuring kickoff time is within a 24-hour window of the database's `start_time`.
   - If not found in scheduled events, fallback to the search API (`/api/v1/search/all?q=...`) to locate the event.
   - Identifies the best candidate (smallest timestamp difference).
   - Fetches authoritative details from `/api/v1/event/{event_id}`.
   - Extracts period scores (`period1`, `period2`) and handles potential home/away team swaps.
   - Resolves final/period scores and settles all associated unsettled bets in the database.

---

## Score Structure Mapping

SofaScore represents scores in a structured format:
- **First Half (1H)**: `homeScore.period1` and `awayScore.period1`
- **Second Half (2H)**: `homeScore.period2` and `awayScore.period2` (goals scored in 2nd half, not cumulative)
- **Full Time (FT)**: Derived as `h1 + h2` and `a1 + a2` respectively.

---

## Error Handling

- **Browser Context Initialization**: Resolves Cloudflare challenges by visiting `sofascore.com` homepage once at resolution startup.
- **Graceful Fallbacks**: Missing period scores on 0-0 draws default to 0-0.
- **Swapped Team Detection**: Swaps home and away scores if Sofascore listed the teams in the opposite order of our database.
