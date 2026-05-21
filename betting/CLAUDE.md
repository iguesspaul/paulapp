**Context**: High-frequency value detection for sports betting on JustBet, a messed up local casino odds that we can exploit
**Stack**: Python 3.14.4, Playwright, Scipy, NumPy, SQLite, BeautifulSoup.

## Operational Architecture

**1. Data Pipeline**
- **Harvesting**: Use async Playwright to intercept XHR `GetEventDetails` responses on JustBet. 
- **Persistence**: Store raw JSON payloads in `bets.db` (`raw_payloads` table).
- **Extraction**: Extract `{market_name, selection_name, price}` into flat lists. No business logic in parsers.

**2. Mathematical Engine (The Law)**
- **Poisson**: All pricing must derive from a 7x7 NumPy probability grid (0-6 goals).
- **Consensus**: Calculate `CONSENSUS_LAMBDA` by de-vigging sharp books (Pinnacle/Bet365). 
- **Bias Constants**: 
    - Home Advantage: 58% of $\lambda$ to Home, 42% to Away.
    - Match Timing: 1st Half = 45% of total goals; 2nd Half = 55%.
- **EV Calculation**: `(Fair_Prob * (Price - 1)) - (1 - Fair_Prob)`.

**3. The Resolver Pattern**
- **Mapping**: Implement a resolver that maps casino market strings to grid coordinate filters.
- **Aggregates**: Handle "Winning Margin" and "Multiscores" by summing specific probability coordinates in the 7x7 grid.

**4. Project State & Docs**
- **Reference**: Use the docs as a reference point if you need quick information on the purposes of certain tools/files/folders
- **MkDocs Integration**: All documentation must reside in the `docs/` folder and be compatible with MkDocs.
- **Living Doc**: On every major logic change, update `docs/human.md` with a plain-language summary.
- **Architecture Logs**: Maintain the `[FOLDER]_DEBUG.md` files within `docs/` to map functions and logic of the src/ folder
- **Conciseness**: Keep documentation actionable and technical. Use the `docs/` structure to preserve original understanding of the file system.

**5. Dynamic Lambda Scaling**
- **Do NOT hardcode 45/55 splits.**
- **Input Requirements**: The system should accept two primary inputs: `MATCH_LAMBDA` and `HT_LAMBDA`.
- **Derivation**: 
    - If `HT_LAMBDA` is provided (from Sharp 1st Half lines), use it for all 1st half markets.
    - If `HT_LAMBDA` is NOT provided, fallback to 45% of `MATCH_LAMBDA`, but log a "WARNING: HEURISTIC SPLIT" to console
- **2nd Half Logic**: `2H_LAMBDA` MUST always be `MATCH_LAMBDA - HT_LAMBDA`.


**MAIN PIPELINE**
Here is how the data pipeline works 
Resolve unsettled bets if matches finished -> Scrape JustBet for odds of upcoming matches -> scrape corresponding match odds from sharps -> calculate EV of bets using 7x7 grid-> output the bets with +EV

**SCRAPING SPECIFICs**
- You are allowed and recommended to create small temporary python tools to figure out where information is located on a website so that playwright can access the right information. 
- These tools should NEVER write to the main database, or create any persistent storage. Simply read the output within the tool, evaluate/iterate on the tool until it gets the exact info we want to scrape
- These temporary tools should always be deleted once theyve serve their purpose

## Output Protocol
- Zero conversational fluff, summaries, or checklists.
- Output only code or modifications.
- Begin response with exactly: "I'm completing the task."
- End response with exactly: "completed."