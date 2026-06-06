# Graph Report - .  (2026-06-06)

## Corpus Check
- Corpus is ~21,191 words - fits in a single context window. You may not need a graph.

## Summary
- 261 nodes · 419 edges · 23 communities (20 shown, 3 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.85)
- Token cost: 589,891 input · 20,945 output

## Community Hubs (Navigation)
- [[_COMMUNITY_BetExplorer Sharp Odds|BetExplorer Sharp Odds]]
- [[_COMMUNITY_Database & Results Management|Database & Results Management]]
- [[_COMMUNITY_Casino Odds Parsing|Casino Odds Parsing]]
- [[_COMMUNITY_Documentation & Concepts|Documentation & Concepts]]
- [[_COMMUNITY_Result Settlement|Result Settlement]]
- [[_COMMUNITY_Mathematical Engine|Mathematical Engine]]
- [[_COMMUNITY_Quant Engine Tests|Quant Engine Tests]]
- [[_COMMUNITY_Sharp Source Alignment|Sharp Source Alignment]]
- [[_COMMUNITY_Sharp Consensus Solver|Sharp Consensus Solver]]
- [[_COMMUNITY_Market Resolver|Market Resolver]]
- [[_COMMUNITY_Poisson Probability Grid|Poisson Probability Grid]]
- [[_COMMUNITY_Community 21|Community 21]]

## God Nodes (most connected - your core abstractions)
1. `BettingDatabase` - 25 edges
2. `evaluate_selection()` - 14 edges
3. `Orchestrator — end-to-end scan: harvest → solve → resolve → EV → persist` - 14 edges
4. `process_match()` - 12 edges
5. `run_full_scan()` - 11 edges
6. `run()` - 10 edges
7. `harvest_sharp_odds()` - 10 edges
8. `docs/human.md` - 10 edges
9. `harvest()` - 9 edges
10. `resolve_results()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Session Pipeline (Settle→Scan→Report)` --semantically_similar_to--> `Result Settlement via SofaScore`  [INFERRED] [semantically similar]
  run_session.py → docs/RESULTS_DEBUG.md
- `docs/human.md` --references--> `Session Pipeline (Settle→Scan→Report)`  [EXTRACTED]
  docs/human.md → run_session.py
- `Dynamic Lambda Scaling (45/55 Fallback)` --rationale_for--> `7x7 Poisson Probability Grid`  [INFERRED]
  CLAUDE.md → docs/human.md
- `Test BEResults — scrapes BetExplorer results page for match scores` --conceptually_related_to--> `BetExplorer harvester — Playwright-based sharp odds with search API fallback`  [INFERRED]
  tests/test_be_results.py → src/collectors/harvesters/betexplorer.py
- `clear_all_bets()` --calls--> `generate_report()`  [EXTRACTED]
  clear_bets.py → src/core/reporter.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Full Scan Pipeline** — main, run_session, concept_session_pipeline, concept_ev_detection, concept_performance_attribution [INFERRED 0.95]
- **Mathematical Engine Core** — concept_poisson_grid, concept_sharp_consensus, rationale_dixon_coles, concept_ev_detection, rationale_dynamic_lambda_scaling [INFERRED 0.95]
- **Data Pipeline (Harvest→Resolve→Track)** — docs_harvesters_debug, docs_collectors_debug, concept_market_resolver, rationale_harvester_architecture, concept_performance_attribution [INFERRED 0.85]
- **Sharp odds pipeline — BetExplorer + Pinnacle + Normalizer** — src_collectors_harvesters_betexplorer, src_collectors_harvesters_pinnacle, src_collectors_harvesters_normalizer, concept_sharp_odds_pipeline [EXTRACTED 1.00]
- **Market pricing pipeline — consensus lambdas → Poisson grids → market resolution** — src_math_sharpconsensus, src_math_probabilitygrid, src_collectors_marketresolver, concept_dixon_coles_model [EXTRACTED 1.00]
- **Complete bet lifecycle — discovery through EV calculation to settlement and reporting** — src_core_orchestrator, src_core_database, src_core_tracker, src_core_resultschecker, src_core_reporter [INFERRED 0.85]

## Communities (23 total, 3 thin omitted)

### Community 0 - "BetExplorer Sharp Odds"
Cohesion: 0.06
Nodes (52): _be_path_to_url(), _dom_fallback_odds(), _fetch_json_odds(), _find_match_id(), find_match_url(), harvest_sharp_odds(), _parse_json_1x2(), _parse_json_ou() (+44 more)

### Community 1 - "Database & Results Management"
Cohesion: 0.07
Nodes (25): main(), clear_all_bets(), BettingDatabase, Returns distinct (match_id, home_team, away_team, be_path, start_time) for all u, Marks a single bet as settled and calculates actual_profit., Returns all unsettled bet rows for a given match_id., Returns the current bankroll balance. Initializes to DEFAULT if empty., Overwrites the current bankroll balance. (+17 more)

### Community 2 - "Casino Odds Parsing"
Cohesion: 0.08
Nodes (28): CasinoParser, Parses the JSON file from the Altenar API and returns a structured list of marke, discover_active_leagues(), fetch_json(), fetch_page_json(), find_matches(), make_slug(), # NOTE: Legacy — Pinnacle harvester now uses the arcadia API directly (league na (+20 more)

### Community 3 - "Documentation & Concepts"
Cohesion: 0.15
Nodes (22): Expected Value Detection, Kelly Criterion Staking, Market Resolver, Performance Attribution & Category Tracking, 7x7 Poisson Probability Grid, Result Settlement via SofaScore, Session Pipeline (Settle→Scan→Report), Sharp Consensus (+14 more)

### Community 4 - "Result Settlement"
Cohesion: 0.12
Nodes (15): check_name_match(), clean_team_name(), evaluate_1x2(), evaluate_btts(), evaluate_double_chance(), evaluate_selection(), evaluate_total(), fetch_sofascore_json() (+7 more)

### Community 5 - "Mathematical Engine"
Cohesion: 0.18
Nodes (17): Consensus lambda aggregation with Pinnacle anchor and >15% outlier filtering, Dixon-Coles tau adjustment for low-scoring Poisson dependency correction, Fallback lambda cascade: consensus → global_lambda.json → USER_TARGET_LAMBDA → 2.65, Fractional Kelly (20%) — conservative volatility reduction on Kelly stake, Implied lambda solver — fits home/away lambdas to 1x2 + O/U with Dixon-Coles loss, CATEGORY_MAP — regex-driven market categorization, order-dependent for specificity, PIN_PATH_OVERRIDES — maps org-based prefixes (UEFA, CONMEBOL) for Pinnacle URL paths, CasinoParser — Altenar JSON market parser (+9 more)

### Community 6 - "Quant Engine Tests"
Cohesion: 0.15
Nodes (7): TEST 1: The 'Pinnacle 1.93/1.95' Benchmark.         If Over 2.5 is 1.934 and Und, TEST 2: The 'Coin Flip' EV Check.         If true probability is 50% (0.5), and, TEST 3: The 'House Edge' EV Check.         If true prob is 50% (0.5), and casino, TEST 4: The 'Bankroll Protection' Check.         Bankroll = $40. Prob = 0.5. Odd, TEST 5: The 'Half-Time Independence' Check.         If Match Lambda is 3.0, 1st, TEST 6: Top-Down Market Implied Constraint Solver.         Test that we can perf, TestQuantEngine

### Community 7 - "Sharp Source Alignment"
Cohesion: 0.25
Nodes (11): LEAGUE_ALIASES — bridges name mismatches between Altenar, BetExplorer, and Pinnacle, Multi-group league resolution — tries each URL for split-group leagues like FNL 2, Pinnacle two-way counterpart fallback — separate 3-way and 2-way matchups share teams, Sharp odds pipeline — BetExplorer + Pinnacle as dual sharp sources, SofaScore results settlement — fuzzy team matching, home/away swap detection, period scores, BetExplorer harvester — Playwright-based sharp odds with search API fallback, Normalizer — shared team name normalization, LEAGUE_ALIASES, name_match_score, Pinnacle harvester — arcadia guest API, pure HTTP, no browser (+3 more)

### Community 8 - "Sharp Consensus Solver"
Cohesion: 0.24
Nodes (5): get_consensus_lambda(), Fits home_lambda and away_lambda using a local optimization loop.      If Pu is, SharpConsensus, solve_implied_lambdas(), solve_lambda_from_odds()

## Knowledge Gaps
- **6 isolated node(s):** `docs/RESULTS_DEBUG.md`, `src/__init__.py`, `DiagnoseLambda — diagnostic tool testing lambda solver against real sharps.json`, `Test BEResults — scrapes BetExplorer results page for match scores`, `TestResultsChecker — unit tests for evaluate_selection on all market types` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BettingDatabase` connect `Database & Results Management` to `Casino Odds Parsing`?**
  _High betweenness centrality (0.273) - this node is a cross-community bridge._
- **Why does `resolve_results()` connect `Database & Results Management` to `Result Settlement`?**
  _High betweenness centrality (0.167) - this node is a cross-community bridge._
- **Why does `run_full_scan()` connect `Casino Odds Parsing` to `Database & Results Management`, `Documentation & Concepts`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **What connects `Count how many simulated_bets were inserted in this session.`, `Pull the most recent scan session summary row for display.`, `Parses the JSON file from the Altenar API and returns a structured list of marke` to the rest of the system?**
  _77 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `BetExplorer Sharp Odds` be split into smaller, more focused modules?**
  _Cohesion score 0.06127946127946128 - nodes in this community are weakly interconnected._
- **Should `Database & Results Management` be split into smaller, more focused modules?**
  _Cohesion score 0.06765327695560254 - nodes in this community are weakly interconnected._
- **Should `Casino Odds Parsing` be split into smaller, more focused modules?**
  _Cohesion score 0.08367071524966262 - nodes in this community are weakly interconnected._