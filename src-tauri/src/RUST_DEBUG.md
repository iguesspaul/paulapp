# Rust Backend Documentation

This document provides debugging and development guidance for the Rust backend (`src-tauri/src/`) excluding `lib.rs` and `main.rs`.

## Database Module (db.rs)

### Purpose
Handles all SQLite database operations including schema initialization, TOML migration, and data persistence for todos and habits.

### Schema

**habits table**
```sql
CREATE TABLE habits (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
```

**habit_entries table**
```sql
CREATE TABLE habit_entries (
    habit_id TEXT NOT NULL,
    date TEXT NOT NULL,
    completed BOOLEAN NOT NULL,
    PRIMARY KEY (habit_id, date),
    FOREIGN KEY(habit_id) REFERENCES habits(id)
);
```

**todos table**
```sql
CREATE TABLE todos (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    urgency INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);
```

**habit_monthly_snapshots table**
```sql
CREATE TABLE habit_monthly_snapshots (
    id TEXT PRIMARY KEY,
    habit_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    habit_name TEXT NOT NULL,
    days_in_month INTEGER NOT NULL,
    days_completed INTEGER NOT NULL,
    completion_rate REAL NOT NULL,
    created_at INTEGER NOT NULL,
    UNIQUE(habit_id, year, month),
    FOREIGN KEY(habit_id) REFERENCES habits(id)
);
```

### Database Location
`~/Library/Application Support/paulapp/paulapp.db` (on macOS) OR `~/.config/paulapp/paulapp.db` depending on OS.

### Key Functions

#### `get_db_path() -> Result<PathBuf, String>`
**Purpose:** Helper function to construct the path to the SQLite database.
**Returns:** PathBuf pointing to `{config_dir}/paulapp/paulapp.db`.

#### `get_connection() -> Result<Connection, String>`
**Purpose:** Helper function to open a connection to the SQLite database.
**Returns:** A `rusqlite::Connection` or an error string if opening fails.

#### `init_db() -> Result<(), String>`
**Purpose:** Initialize database and create tables on first run.

**Called from:** `lib.rs::run()` at application startup.

**Behavior:**
- Creates config directory if needed
- Opens/creates SQLite database
- Creates tables if they don't exist (idempotent)

**Debugging:** Check stderr for `[db] Database initialized successfully`

---

#### `load_todos_from_db() -> Result<TodosResponse, String>`
**Purpose:** Load all todos from database.

**Returns:** `TodosResponse { todos: Vec<Todo> }` ordered by creation date (newest first).

**Error cases:**
- DB connection failed: "Failed to open database connection"
- Query preparation failed: "Failed to prepare query"
- Row parsing failed: "Failed to query todos" or "Failed to collect todos"

---

#### `save_todos_to_db(todos: Vec<Todo>) -> Result<(), String>`
**Purpose:** Persist all todos to database.

**Parameters:**
- `todos: Vec<Todo>` - The complete vector of Todos to save.

**Behavior:**
- Clears existing todos table
- Inserts all todos in provided vector

**Error cases:**
- DB connection failed: "Failed to open database connection"
- Clear failed: "Failed to clear todos"
- Insert failed: "Failed to insert todo"

---

#### `update_todo_status(id: &str, status: u8) -> Result<TodosResponse, String>`
**Purpose:** Updates the `status` of a specific todo item.

**Parameters:**
- `id: &str` - The ID string of the todo.
- `status: u8` - The new status integer (e.g. 1=Not Started, 2=In Progress, 3=Completed).

**Returns:** `TodosResponse` with the updated list of all todos.
**Error cases:**
- "Failed to update todo status" if the SQLite UPDATE statement fails.

---

#### `load_habits_from_db() -> Result<HabitsResponse, String>`
**Purpose:** Load all habits and entries from database.

**Returns:** `HabitsResponse { habits: Vec<Habit>, entries: Vec<HabitEntry> }`

**Error cases:** Same pattern as `load_todos_from_db`

---

#### `save_habits_to_db(habits: Vec<Habit>, entries: Vec<HabitEntry>) -> Result<(), String>`
**Purpose:** Persist habits and entries to database.

**Behavior:**
- Clears entries table
- Queries existing habit IDs to find removed habits
- Deletes `habit_monthly_snapshots` and `habits` rows for habits that are no longer in the provided list to prevent FOREIGN KEY constraint violations
- Upserts (`INSERT OR REPLACE`) all provided habits
- Inserts all provided entries

**Error cases:** 
- "Failed to delete snapshots for removed habit"
- "Failed to delete removed habit"
- Standard DB insert/delete failures

---

## habits.rs

### Purpose
Manages habit tracking functionality including loading, saving, adding, removing, and toggling habit entries. Acts as a business logic layer that delegates persistence to the database module.

### Key Functions

#### `load_habits() -> Result<HabitsResponse, String>`
**Purpose:** Load all habits and entries from the database.

**Called from:** Frontend via `load_habits` Tauri command (invoked via TypeScript API).

**Returns:** `HabitsResponse { habits: Vec<Habit>, entries: Vec<HabitEntry> }`

**Flow:**
1. Calls `db::load_habits_from_db()` to fetch database data
2. Returns response containing all habits and their entries

**Error cases:**
- Database connection failed
- Query preparation failed
- Row parsing failed

**Debugging:**
- Check stderr for `[habits] Loading habits from database`
- Verify habits and entries tables exist in SQLite database

---

#### `save_habits(habits: Vec<Habit>, entries: Vec<HabitEntry>) -> Result<(), String>`
**Purpose:** Persist all habits and entries to the database.

**Called from:** `add_habit()`, `remove_habit()`, `toggle_entry()` functions.

**Behavior:**
- Clears all existing habits and entries
- Inserts fresh data
- Delegates to `db::save_habits_to_db()`

**Error cases:** Same as database save failures

**Debugging:**
- Check stderr for `[habits] Saving habits to database`

---

#### `add_habit(habit: Habit) -> Result<HabitsResponse, String>`
**Purpose:** Add a new habit and return updated state.

**Called from:** Frontend via `add_habit` Tauri command.

**Flow:**
1. Loads current habits via `load_habits()`
2. Appends new habit to the list
3. Saves updated list via `save_habits()`
4. Returns updated `HabitsResponse`

**Note:** Frontend generates the habit ID and the Tauri command handler in `lib.rs` sets `created_at` to current timestamp.

---

#### `remove_habit(id: String) -> Result<HabitsResponse, String>`
**Purpose:** Remove a habit and all its entries, return updated state.

**Called from:** Frontend via `remove_habit` Tauri command.

**Flow:**
1. Loads current habits and entries
2. Filters out habit with matching ID
3. Filters out all entries for that habit
4. Saves updated lists
5. Returns updated response

**Details:** Uses `retain!` to keep only items that don't match the removed habit ID.

---

#### `toggle_entry(habit_id: String, date: String) -> Result<HabitsResponse, String>`
**Purpose:** Toggle completion status of a habit for a specific date.

**Called from:** Frontend via `toggle_habit_entry` Tauri command.

**Flow:**
1. Loads current entries
2. Finds entry matching both `habit_id` and `date`
3. If found: toggles `completed` boolean
4. If not found: creates new entry with `completed = true`
5. Saves updated entries
6. Returns updated response

**Behavior Notes:**
- Toggle is idempotent: clicking same day twice turns off
- Clicking a new day creates the entry automatically
- All entries stored as date strings in format `YYYY-MM-DD`

**Debugging:**
- Check stderr logs from `[habits]` module
- Verify entries table has rows with correct habit_id/date combinations

---

## Habit Backup & Analytics (db.rs functions)

### Purpose
Creates monthly snapshots and provides historical analysis of habit completion rates for visualization and tracking long-term progress.

### Key Functions

#### `create_monthly_snapshot(year: i32, month: i32) -> Result<(), String>`
**Purpose:** Create a monthly backup capturing completion statistics for all habits.

**Called from:** Frontend via `create_habit_backup` Tauri command (can be manual or automatic).

**What it does:**
1. Iterates through all habits
2. Counts days completed in the specified month
3. Calculates completion rate (days_completed / days_in_month)
4. Inserts row into `habit_monthly_snapshots` table with statistics
5. If snapshot already exists for that month, updates it (INSERT OR REPLACE)

**Data captured:**
- `habit_id` - Reference to the habit
- `habit_name` - Snapshot of habit name (in case habit is renamed/deleted later)
- `year`, `month` - Month identifier
- `days_in_month` - Total days in that month (28-31)
- `days_completed` - Count of days with completed = true
- `completion_rate` - Float between 0 and 1 (0.75 = 75% completion)
- `created_at` - Timestamp when snapshot was created

**Error cases:**
- Invalid month (not 1-12): "Invalid date"
- Database insert failed: "Failed to insert snapshot"
- Query failed: "Failed to prepare/count"

**Debugging:**
- Check stderr for `[db] Created monthly snapshot for YYYY-MM`
- Query `habit_monthly_snapshots` table to verify data was stored
- Run with specific year/month to test manually

**Use cases:**
- Called automatically at month-end (not yet implemented - add to scheduler)
- Called manually when user wants to capture current progress
- Provides historical data for graphs/visualizations

---

#### `get_habit_history(habit_id: &str) -> Result<Vec<(i32, i32, i32, i32, f64)>, String>`
**Purpose:** Retrieve all monthly snapshots for a specific habit (time series data).

**Returns:** Vector of tuples `(year, month, days_in_month, days_completed, completion_rate)` ordered chronologically.

**Use:** Frontend uses this to plot completion trends over time. Returned data is ready for graphing libraries.

**Example:** 
```
Habit: "Workout"
[ (2025, 1, 31, 28, 0.90),   // 90% completion in January 2025
  (2025, 2, 28, 22, 0.79),   // 79% completion in February 2025
  (2025, 3, 31, 29, 0.94) ]  // 94% completion in March 2025
```

**Error cases:** "Failed to query history", "Failed to collect history"

---

#### `get_monthly_summary(year: i32, month: i32) -> Result<Vec<(String, i32, i32, f64)>, String>`
**Purpose:** Get statistics for all habits in a specific month (cross-sectional view).

**Returns:** Vector of tuples `(habit_name, days_in_month, days_completed, completion_rate)`.

**Use:** Shows how all habits performed in a given month. Useful for monthly review dashboard.

**Example:**
```
Month: March 2025
[ ("Workout", 31, 29, 0.94),
  ("Read books", 31, 18, 0.58),
  ("Meditate", 31, 25, 0.81) ]
```

**Error cases:** "Failed to query summary", "Failed to collect summary"

---

#### `get_habit_name(habit_id: &str) -> Result<String, String>`
**Purpose:** Retrieve the current name of a habit (helper function).

**Called from:** `get_habit_history()` to attach habit name to response.

**Returns:** Current habit name from habits table.

**Error cases:** "Habit not found" (if habit_id doesn't exist)

### Models Used
- `HabitMonthlySnapshot`: Contains year, month, days_in_month, days_completed, completion_rate
- `HabitHistoryResponse`: Contains habit_id, habit_name, snapshots array
- `HabitMonthlySummary`: Contains habit_name, days_in_month, days_completed, completion_rate
- `MonthlySummary`: Contains year, month, habits array

---

## sports.rs

### Purpose
Fetches sports league standings from the SofaScore API and parses them into a structured response.

### Key Functions

#### `build_client() -> Client`
**Purpose:** Creates an HTTP client with proper headers to mimic a browser request.

**Headers used:**
- `User-Agent`: Chrome on macOS
- `Accept`: application/json
- `Accept-Language`: en-US,en;q=0.9
- `Referer`: https://www.sofascore.com/
- `Origin`: https://www.sofascore.com

**Why?** SofaScore may reject requests without proper browser headers.

**Debugging:** If requests fail with 403/401 errors, check if headers are outdated.

---

#### `get_season_id(client: &Client, tournament_id: &str) -> Result<u32, String>`
**Purpose:** Fetches the current season ID for a given tournament.

**API Call:**
```
GET {SOFASCORE_BASE}/unique-tournament/{tournament_id}/seasons
```

**Expected Response Structure:**
```json
{
  "seasons": [
    { "id": <season_id> },
    ...
  ]
}
```

**Error Cases:**
- Network error: Returns "season request failed: {error}"
- JSON parse error: Returns "season json parse failed: {error}\nraw: {first_200_chars}"
- Missing season ID: Returns "no season id in response: {first_200_chars}"

**Debugging Tips:**
- Check `[sports] season raw:` in stderr for actual API response
- If "no season id", API structure may have changed
- Verify `tournament_id` is valid

---

#### `fetch_standings(league_id: &str) -> Result<StandingsResponse, String>`
**Purpose:** Main function that fetches and parses league standings.

**Flow:**
1. Creates HTTP client via `build_client()`
2. Fetches season ID via `get_season_id()`
3. Fetches standings data from standings/total endpoint
4. Parses JSON and converts to `TeamStanding` objects
5. Returns `StandingsResponse`

**API Call:**
```
GET {SOFASCORE_BASE}/unique-tournament/{league_id}/season/{season_id}/standings/total
```

**Expected Response Structure:**
```json
{
  "standings": [
    {
      "rows": [
        {
          "position": <number>,
          "team": {
            "id": <number>,
            "name": <string>,
            "shortName": <string>
          },
          "matches": <number>,
          "wins": <number>,
          "draws": <number>,
          "losses": <number>,
          "scoresFor": <number>,
          "scoresAgainst": <number>,
          "points": <number>
        },
        ...
      ]
    }
  ]
}
```

**Error Cases:**
- Network error: "standings request failed: {error}"
- JSON parse error: "standings json parse failed: {error}\nraw: {first_200_chars}"
- Missing standings rows: "no standings rows in response: {first_200_chars}"

**Data Transformation:**
- `scoresFor` → `goals_for`
- `scoresAgainst` → `goals_against`
- Calculates `goal_difference` = goals_for - goals_against

**Debugging Tips:**
- Check `[sports] GET {url}` in stderr to see exact API endpoint
- Check `[sports] standings raw:` to inspect API response
- Check `[sports] parsed {} rows` to verify parsing succeeded
- All numeric fields use `.unwrap_or(0)` so missing fields default to 0

---

#### `fetch_upcoming_matches(league_id: &str) -> Result<UpcomingMatchesResponse, String>`
**Purpose:** Fetches the next upcoming matches for a league.

**Flow:**
1. Creates HTTP client via `build_client()`
2. Fetches season ID via `get_season_id()`
3. Fetches upcoming matches data from events/next endpoint
4. Takes the first 4 matches from the events array
5. Parses JSON and converts to `UpcomingMatch` objects
6. Returns `UpcomingMatchesResponse`

**API Call:**
```
GET {SOFASCORE_BASE}/unique-tournament/{league_id}/season/{season_id}/events/next/0
```

**Expected Response Structure:**
```json
{
  "events": [
    {
      "id": <number>,
      "slug": <string>,
      "roundInfo": {
        "round": <number>
      },
      "startTimestamp": <number>,
      "status": {
        "type": <string>
      },
      "homeTeam": {
        "id": <number>,
        "name": <string>
      },
      "awayTeam": {
        "id": <number>,
        "name": <string>
      }
    },
    ...
  ]
}
```

**Data Extracted:**
- `event_id`: Event ID from API
- `slug`: URL slug (e.g., "bournemouth-manchester-united")
- `round`: Match round number
- `start_timestamp`: Unix timestamp of match start
- `status`: Match status (e.g., "notstarted", "postponed")
- `home_team_id`, `home_team_name`: Home team details
- `away_team_id`, `away_team_name`: Away team details

**Error Cases:**
- Network error: "matches request failed: {error}"
- JSON parse error: "matches json parse failed: {error}\nraw: {first_200_chars}"
- Missing events array: "no events in response: {first_200_chars}"

**Debugging Tips:**
- Check `[sports] GET {url}` to verify endpoint
- Check `[sports] matches raw:` to inspect API response
- Check `[sports] parsed {} matches` to verify parsing succeeded (should be 4 or less)
- All numeric fields use `.unwrap_or(0)` so missing fields default to 0
- Empty strings are used for missing team names/slugs

---

### Known League IDs
- `"1"` - Premier League (EPL)
- `"39"` - Eredivisie

---

### Common Issues

**Issue:** "TypeError: null is not an object" in frontend
**Solution:** Check if `standings` array is null in response. Add null check in component.

**Issue:** Empty standings array
**Solution:** Verify the `standings[0]["rows"]` path exists. API structure may have changed.

**Issue:** No upcoming matches returned
**Solution:** League may not have scheduled matches. Check `[sports] parsed {} matches` in logs. Events endpoint may not have data.

**Issue:** 403/401 API errors
**Solution:** Check browser headers in `build_client()`. Headers may need updating.

**Issue:** Season ID not found
**Solution:** Verify tournament ID is correct. Check SofaScore API for valid IDs.

---

### Logging
All debug output goes to `stderr` with `[sports]` prefix for easy filtering:
```bash
# View only sports logs
cargo run 2>&1 | grep "\[sports\]"
```

### Models Used
- `StandingsResponse`: Contains league_id, season_id, standings array, cached_at
- `TeamStanding`: Contains position, team_id, team_name, short_name, played, won, drawn, lost, goals_for, goals_against, goal_difference, points
- `UpcomingMatchesResponse`: Contains league_id, season_id, matches array
- `UpcomingMatch`: Contains event_id, slug, round, start_timestamp, status, home/away team info

---

## todos.rs

### Purpose
Manages todo functionality including loading, saving, adding, and removing todos. Acts as a business logic layer that delegates persistence to the SQLite database module (`db.rs`), replacing the old TOML-based implementation.

### Key Functions

#### `load_todos() -> Result<TodosResponse, String>`
**Purpose:** Loads all todos from the database.

**Returns:** `TodosResponse` containing a vector of todos.

**Behavior:**
1. Logs loading action.
2. Calls `db::load_todos_from_db()`.
3. Returns the db response.

---

#### `save_todos(todos: Vec<Todo>) -> Result<(), String>`
**Purpose:** Saves the entire generic list of todos to the database.

**Parameters:**
- `todos: Vec<Todo>`: Vector of `Todo` structs to persist.

**Behavior:**
1. Logs saving action.
2. Calls `db::save_todos_to_db(todos)`.

---

#### `add_todo(todo: Todo) -> Result<TodosResponse, String>`
**Purpose:** Adds a new todo to the store and returns all todos.

**Parameters:** 
- `todo: Todo` - Struct with id, name, status, urgency, and created_at.

**Behavior:**
1. Loads existing todos via `load_todos()`
2. Appends new todo to the list
3. Saves all todos via `save_todos()`
4. Returns the updated `TodosResponse`

---

#### `remove_todo(id: String) -> Result<TodosResponse, String>`
**Purpose:** Removes a todo by ID and returns all remaining todos.

**Parameters:**
- `id: String` - The ID of the todo to remove.

**Behavior:**
1. Loads existing todos via `load_todos()`
2. Filters out the todo with the matching ID
3. Saves remaining todos via `save_todos()`
4. Returns the updated `TodosResponse`

### Models Used
- `Todo`: Contains id (String), name (String), status (u8), urgency (u8), created_at (i64 timestamp)
- `TodosResponse`: Contains todos vector

---

## ai.rs

### Purpose
Fetches top headlines from global public RSS feeds (BBC, NYT) and uses a local Ollama instance to generate a single-paragraph summary of the major events.

### Key Functions

#### `generate_news_summary() -> Result<String, String>`
**Purpose:** Scrapes news headlines, checks local Ollama available models (`/api/tags`), and prompts an available model via `/api/generate` for a summarization.

**Flow:**
1. Calls basic public RSS feeds with `reqwest`.
2. Hacky manual parsing of XML `<title>` tags to avoid `quick-xml` or regex dependencies, retaining up to 5 headlines per news source.
3. Requests available local models from `http://localhost:11434/api/tags`. Chooses the first available model, falling back to `"llama3.2"`.
4. Sends the request to the `/api/generate` endpoint, instructing it to make a single paragraph summary.

**Error Cases:**
- Local Ollama not running: Returns `"Failed to connect to local Ollama API: {error}"`
- Client config error: Returns `"Client build error: {error}"`

**Debugging Tips:**
- Check `[ai] Scraped headlines...` in stderr.
- Check `[ai] Using model...` to log the dynamically chosen model.
- If Ollama timeout happens, consider increasing `Duration::from_secs(60)`.

## whoop.rs

### Purpose
Handles OAuth 2.0 flow and API calls to the WHOOP developer API (`v2`) for retrieving user sleep metrics. It manages token exchange, local persistence, and auto-refreshing.

### Configuration & Credentials
Relies on two environment variables placed in a `.env` file at the root:
- `WHOOP_API_PUBLIC` - OAuth Client ID
- `WHOOP_API_SECRET` - OAuth Client Secret

The module uses the `dotenvy` crate to dynamically load these variables at runtime.

### Data Persistence
OAuth credentials (access token, refresh token, and timestamps) are saved locally as standard JSON inside the system's config directory:
- **Location:** `~/.config/paulapp/whoop_token.json` (or `~/Library/Application Support/paulapp/whoop_token.json` on macOS).

### Key Functions

#### `get_auth_url() -> Result<String, String>`
**Purpose:** Constructs the WHOOP OAuth 2.0 authorization URL to kick off authentication.
**Scopes Requested:** `offline read:sleep read:recovery read:cycles read:workout read:profile`
**Redirect URI:** `http://localhost:1420/callback`
**Returns:** URL string for the user to visit in their browser.

#### `exchange_token(code: String) -> Result<(), String>`
**Purpose:** Exchanges a short-lived authorization code for an Access Token and Refresh Token.
**Flow:**
1. Constructs POST request to `WHOOP_TOKEN_URL`.
2. Sends the authorization code along with credentials.
3. Calculates expiration timestamp (`expires_at`).
4. Persists the `WhoopToken` object to disk via `save_token()`.

**Error Cases:**
- `WHOOP_API_PUBLIC missing` / `WHOOP_API_SECRET missing` - Secrets absent from `.env`.
- `Token request failed: {error}` - Network error.
- `Failed to exchange token: {status} - {text}` - Non-200 HTTP response.

#### `refresh_token_if_needed() -> Result<WhoopToken, String>`
**Purpose:** Internal helper to auto-refresh the OAuth token without requiring user interaction if it expires in less than 5 minutes.
**Flow:**
1. Loads cached/file token. Returns error if not authenticated.
2. If token is valid, returns immediately.
3. If expiring in < 300s, uses the refresh token to hit `WHOOP_TOKEN_URL` and get a new access token.
4. Updates cache and saves updated `WhoopToken` to disk.

#### `get_sleep_score() -> Result<SleepScore, String>`
**Purpose:** Fetches the most recent sleep's score using the V2 WHOOP API.
**API URL:** `https://api.prod.whoop.com/developer/v2/activity/sleep?limit=1`
**Flow:**
1. Ensures token is valid (calls `refresh_token_if_needed()`).
2. Sends GET request to WHOOP API with Bearer token authentication.
3. Parses JSON response and constructs the `SleepScore` struct.

**Data Extracted:**
- `sleep_performance_percentage`
- `sleep_consistency_percentage`
- `sleep_efficiency_percentage`

**Error Cases:**
- `Failed to get sleep data: {status}` - API returns error (e.g. 401 Unauthorized if scope missing).
- `No sleep records found` - Valid request but user lacks recent sleep data.

### Models Used
- `WhoopToken` (Internal): Auth response containing `access_token`, `refresh_token`, `expires_in`, and UNIX `expires_at`.
- `SleepScore` (Returned to TS): Exposes metrics. Marked with `#[serde(rename_all = "camelCase")]` so it maps to native JS conventions on the Svelte side.

### Logging
All debug output goes to `stderr` with `[whoop]` prefix for easy filtering:
```bash
cargo run 2>&1 | grep "\[whoop\]"
```

## countdowns.rs

### Purpose
Manages countdown tracking functionality including loading, saving, adding, and removing countdowns. Acts as a business logic layer that delegates persistence to the SQLite database module (`db.rs`).

### Key Functions

#### `load_countdowns() -> Result<CountdownsResponse, String>`
**Purpose:** Loads all countdowns from the database and automatically filters out any that have passed their target timestamp.
**Behavior:**
1. Loads all countdowns from the database.
2. Compares the `target_timestamp` of each countdown to the current time (`Utc::now().timestamp()`).
3. Retains only countdowns that are strictly in the future (`target_timestamp > now`).
4. If any expired countdowns were removed, automatically saves the updated list back to the database.
**Returns:** `CountdownsResponse` containing a vector of active countdowns.

#### `save_countdowns(countdowns: Vec<Countdown>) -> Result<(), String>`
**Purpose:** Saves the entire generic list of countdowns to the database.

#### `add_countdown(countdown: Countdown) -> Result<CountdownsResponse, String>`
**Purpose:** Adds a new countdown to the store and returns all countdowns.

#### `remove_countdown(id: String) -> Result<CountdownsResponse, String>`
**Purpose:** Removes a countdown by ID and returns all remaining countdowns.

### Models Used
- `Countdown`: Contains id (String), name (String), target_timestamp (i64), created_at (i64 timestamp)
- `CountdownsResponse`: Contains countdowns vector

---

## weather.rs

### Purpose
Fetches weather and UV index data from the Google Weather API. It identifies the peak UV index for the current calendar day by combining historical data and forecast data.

### Key Functions

#### `get_max_uv_index() -> Result<UVIndexResponse, String>`
**Purpose:** Calculates the peak UV index and its time for the current calendar day.

**Flow:**
1. Fetches the last 24 hours of data from `v1/history/hours:lookup`.
2. Fetches the next 24 hours of data from `v1/forecast/hours:lookup`.
3. Identifies the "current day" at the location by looking at the timestamps of the results.
4. Aggregates all segments for that specific calendar day.
5. Finds the maximum `uvIndex` value and its corresponding `displayDateTime` (hours:minutes).
6. Returns a `UVIndexResponse`.

**API Parameters:**
- `key`: Google API Key (Hardcoded in weather.rs)
- `location.latitude`: 18.033237
- `location.longitude`: -76.763064
- `hours`: 24 (for both history and forecast)

**Error Cases:**
- Network failure or API error.
- No UV data found in the response segments.
- Failed to parse JSON response.

### Models Used
- `UVIndexResponse`: Contains `max_uv_index` (f64) and `max_uv_time` (String in "HH:MM" format).

### Debugging
- All debug output goes to `stderr`.
- Check for `Weather request failed` or `Failed to parse weather response` if the dashboard shows `--`.

