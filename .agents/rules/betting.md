---
trigger: model_decision
description: When working in /betting
---

**Context**: High-frequency value detection for sports betting on JustBet, a messed up local casino odds that we can exploit
**Stack**: Python 3.14.4, Playwright, Scipy, NumPy, SQLite, BeautifulSoup.

## Operational Architecture

**1. Data Pipeline**
- **Harvesting**: Use async Playwright to intercept XHR `GetEventDetails` responses on JustBet. "Agent, the market_resolver.py is failing. It is returning the same Fair Price (1.39) for different markets like '1st half BTTS' and 'Full Match BTTS'.
You must ensure the resolver uses the Half-Time Lambda (45% of total) for all 1st Half markets.
You must ensure that '1x2 & BTTS' calculates the probability of BOTH occurring (Win * BTTS), not just one.
Recalculate the Poisson grid and re-run. We are looking for realistic EVs between 5% and 25%."
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
- **MkDocs Integration**: All documentation must reside in the `docs/` folder and be compatible with MkDocs.
- **Living Doc**: On every major logic change, update `docs/human.md` with a plain-language summary.
- **Architecture Logs**: Maintain the `[FOLDER]_DEBUG.md` files within `docs/` to map functions and logic.

**5. Dynamic Lambda Scaling**
- **Do NOT hardcode 45/55 splits.**
- **Input Requirements**: The system should accept two primary inputs: `MATCH_LAMBDA` and `HT_LAMBDA`.
- **Derivation**: 
    - If `HT_LAMBDA` is provided (from Sharp 1st Half lines), use it for all 1st half markets.
    - If `HT_LAMBDA` is NOT provided, fallback to 45% of `MATCH_LAMBDA`, but log a "WARNING: HEURISTIC SPLIT" in `docs/index.md`.
- **2nd Half Logic**: `2H_LAMBDA` MUST always be `MATCH_LAMBDA - HT_LAMBDA`.

**6. Documentation**
- **Code-Doc Sync**: Anytime a change is made to a Python file, or a new file is added, you MUST update the corresponding `_DEBUG.md` file in `docs/` to reflect function changes, new inputs/outputs, or structural shifts.
- **Conciseness**: Keep documentation actionable and technical. Use the `docs/` structure to preserve original understanding of the file system.


**MAIN INSTRUCTION**
Here is how the data pipeline works 
Scrape JustBet for future odds -> scrape other bets to compare and calculate all logic -> calculate +EV bets -> scrape JustBet for passed matches and check results -> Check profits

## Output Protocol
- Zero conversational fluff, summaries, or checklists.
- Output only code or modifications.
- Begin response with exactly: "I'm completing the task."
- End response with exactly: "completed."