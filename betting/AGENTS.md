**Context**: High-frequency value detection for sports betting on JustBet, a messed up local casino odds that we can exploit
**Stack**: Python 3.14.4, Playwright, Scipy, NumPy, SQLite, BeautifulSoup.

## Output Protocol
- Zero conversational fluff, summaries, or checklists.
- Output only code or modifications.
- Begin response with exactly: "I'm completing the task."
- End response with exactly: "completed."

## Project State & Docs 
- **MkDocs Integration**: All documentation must reside in the `docs/` folder and be compatible with MkDocs.
- **Living Doc**: On every major logic change, update `docs/human.md` with a plain-language summary.
- **Architecture Logs**: Maintain the `[FOLDER]_DEBUG.md` files within `docs/` to map functions and logic of the src/ folder
- **Conciseness**: Keep documentation actionable and technical. Use the `docs/` structure to preserve original understanding of the file system.

## MAIN PIPELINE
Here is how the data pipeline works 
Resolve unsettled bets if matches finished -> Scrape JustBet for odds of upcoming matches -> scrape corresponding match odds from sharps -> calculate EV of bets using 7x7 grid-> output the bets with +EV

## SCRAPING SPECIFICS
- You are allowed and recommended to create small temporary python scripts to figure out where information is located on a website so that playwright or api calls can access the right information. 
- These scripts should NEVER write to the main database, or create any persistent storage. Simply read the output within the script, evaluate/iterate on the script until it gets the exact info we want to scrape
- These temporary scripts should always be deleted once theyve served their purpose

## TOOL CALLS
- For these tools: ls, find, grep, diff, wc, cat / head / tail <file>, use the rtk <command> prefix always instead of the default (eg: rtk grep instead of just grep)


## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

