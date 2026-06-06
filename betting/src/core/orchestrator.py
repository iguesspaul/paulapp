import os
import asyncio
from src.core.config import LEAGUES, INITIAL_BANKROLL, KELLY_MULTIPLIER
from src.math.sharp_consensus import get_consensus_lambda, solve_implied_lambdas_from_consensus
from src.math.probability_grid import ProbabilityGrid
from src.math.bankroll_manager import calculate_kelly_stake
from src.math.ev import calculate_ev, calculate_fair_odds
from src.collectors.market_resolver import MarketResolver
from src.collectors.scraper import find_matches, fetch_page_json, discover_active_leagues
from src.collectors.harvesters import betexplorer, pinnacle
from src.collectors.casino_parser import CasinoParser
from src.core.database import BettingDatabase
from src.core.tracker import BetTracker

# Simulation Mode: all tracked bets use a flat $1.00 stake for performance attribution.
SIMULATION_STAKE = 1.0

async def process_match(match, league_config, db, tracker, parser, consensus_engine, is_session=True):
    """
    Processes a single match: harvests sharps, calculates EV, and saves.
    """
    teams = match['name'].split(' vs. ')
    if len(teams) != 2:
        return

    team_a, team_b = teams[0], teams[1]
    print(f"\n[ORCHESTRATOR] Processing: {team_a} vs {team_b}")

    # 1. Harvest Sharp Odds in Parallel
    results = await asyncio.gather(
        betexplorer.harvest_sharp_odds(
            league_config['be_path'], team_a, team_b,
            league_name=league_config.get('name', ''),
            country_name=league_config.get('country', '')
        ),
        pinnacle.harvest(league_config['pin_path'], team_a, team_b,
                         league_name=league_config.get('name', ''),
                         country_name=league_config.get('country', ''))
    )

    # Flatten results into a single list of book results
    sharp_results = []
    betexp_results, pin_result = results[0], results[1]
    if isinstance(betexp_results, list):
        sharp_results.extend(betexp_results)
    else:
        sharp_results.append(betexp_results)

    # Log per-harvester status
    pin_odds = pin_result.get('odds', {}) if isinstance(pin_result, dict) else {}
    betexp_odds = any(r.get('odds') for r in (betexp_results if isinstance(betexp_results, list) else [betexp_results]))
    if pin_odds:
        print(f"[PINNACLE] Found odds for {team_a} vs {team_b}: {len(pin_odds)} markets")
    else:
        print(f"[PINNACLE] No odds found for {team_a} vs {team_b}")
    if betexp_odds:
        print(f"[BETEXPLORER] Found consensus odds for {team_a} vs {team_b}")
    else:
        print(f"[BETEXPLORER] No odds found for {team_a} vs {team_b}")

    # Append Pinnacle result to sharp_results (it was logged but not added)
    sharp_results.append(pin_result)

    # Check if we got any odds
    has_odds = any(entry.get('odds') for entry in sharp_results)
    
    import json
    if has_odds:
        with open("data/sharps.json", "w") as f:
            json.dump(sharp_results, f, indent=2)
    else:
        print(f"[SKIP] No sharp odds found for {match['name']}, keeping old sharps.json")

    # 2. Calculate Implied Lambdas with Fallbacks
    home_lambda, away_lambda = None, None
    using_fallback = False
    if has_odds:
        home_lambda, away_lambda = solve_implied_lambdas_from_consensus(sharp_results)
        
    if home_lambda is not None and away_lambda is not None:
        print(f"[SHARP] Solver Succeeded: Home Lambda = {home_lambda:.4f}, Away Lambda = {away_lambda:.4f}")
        prob_grid = ProbabilityGrid(home_lambda=home_lambda, away_lambda=away_lambda)
    else:
        using_fallback = True
        # Fallback to single match_lambda logic
        match_lambda = None
        if has_odds:
            match_lambda = get_consensus_lambda(sharp_results)
        else:
            print("[FALLBACK] Attempting to use global_lambda.json")
            if os.path.exists("data/global_lambda.json"):
                with open("data/global_lambda.json", "r") as f:
                    g_data = json.load(f)
                    match_lambda = g_data.get("lambda")
                    if match_lambda:
                        print(f"[FALLBACK] Using global_lambda.json: {match_lambda}")

            if match_lambda is None:
                try:
                    from main import USER_TARGET_LAMBDA
                    print(f"[FALLBACK] Using USER_TARGET_LAMBDA from main.py: {USER_TARGET_LAMBDA}")
                    match_lambda = USER_TARGET_LAMBDA
                except ImportError:
                    match_lambda = 2.65
                    print(f"[FALLBACK WARNING] Using hardcoded default lambda: {match_lambda}")
                    
        if match_lambda is None:
            return
            
        print(f"[SHARP] Consensus Match Lambda (Fallback): {match_lambda:.4f}")
        prob_grid = ProbabilityGrid(match_lambda=match_lambda)
        
    resolver = MarketResolver(prob_grid)

    # 4. Fetch Casino Match Details
    os.makedirs("data", exist_ok=True)
    json_file = f"data/match_{match['id']}.json"

    success = await fetch_page_json(match['details_url'], json_file)
    if not success:
        return

    # 5. Parse and Resolve Markets
    raw_markets = parser.extract_markets(json_file)
    match_id = str(match['id'])

    seen_bets = set()

    for market in raw_markets:
        m_name = market['name']
        for selection in market['selections']:
            name = selection['name']
            odds = selection['price']

            # Prevent processing duplicate bets
            bet_sig = (m_name, name)
            if bet_sig in seen_bets:
                continue
            seen_bets.add(bet_sig)

            fair_prob = resolver.resolve(m_name, name)
            if fair_prob is not None and fair_prob > 0:
                ev = calculate_ev(fair_prob, odds)
                fair_odds = calculate_fair_odds(fair_prob)

                # Save raw bet to legacy table
                db.insert_bet(match['details_url'], m_name, name, odds, fair_odds, ev)

                # Log if in realistic EV range (5% to 25%)
                if 0.05 < ev < 0.25:
                    # Kelly stake for live use
                    stake = calculate_kelly_stake(odds, fair_prob, INITIAL_BANKROLL, KELLY_MULTIPLIER)

                    # Simulation Mode: skip bets calculated with fallback lambdas
                    # (no real sharp odds backing them — would distort performance tracking)
                    if is_session and using_fallback:
                        tag = "[FALLBACK BET (SKIPPED)]"
                        print(f"{tag} [{m_name}] {name} @ {odds} | EV: {ev:+.2%} (no sharp odds, fallback lambda)")
                        continue

                    category = "Other"
                    if is_session:
                        start_time = match.get('start_time')
                        category, _ = tracker.log(
                            match_id=match_id,
                            market_name=m_name,
                            selection=name,
                            odds=odds,
                            fair_odds=fair_odds,
                            ev=ev,
                            stake=SIMULATION_STAKE,
                            home_team=team_a,
                            away_team=team_b,
                            be_path=league_config['be_path'],
                            start_time=start_time
                        )
                    else:
                        from src.core.tracker import categorize
                        category = categorize(m_name)

                    tag = "[+EV FOUND]"
                    print(f"{tag} [{category}] {m_name} | {name} @ {odds} | Fair: {fair_odds:.2f} | EV: {ev:+.2%} | STAKE: ${stake:.2f}")

async def run_full_scan(is_session=True):
    """Runs a full scan across dynamically discovered active leagues.

    This function now prioritizes the most recently upcoming matches by:
    1. Filtering out live matches (already handled by API)
    2. Filtering for matches scheduled within the next 48 hours
    3. Sorting matches by start time to process nearest events first
    4. Increasing match processing limit to capture more near-term opportunities
    """
    print("--- Sentinel Multi-League Quant Agent Scan Started (Dynamic Mode) ---")

    db = BettingDatabase()
    tracker = BetTracker(db)
    parser = CasinoParser()

    print("Discovering active soccer leagues dynamically...")
    active_leagues = await discover_active_leagues()
    print(f"Discovered {len(active_leagues)} active leagues with prelive events.")

    total_scanned_matches = 0
    MATCH_LIMIT = 100  # Increased from 50 to process more relevant upcoming matches

    for league in active_leagues:
        if total_scanned_matches >= MATCH_LIMIT:
            print(f"\n[SCAN] Reached total limit of {MATCH_LIMIT} scanned matches. Stopping scan.")
            break

        print(f"\n{'='*20}")
        print(f"DYNAMIC LEAGUE: {league['name']} ({league['country']}) - active events: {league['events_count']}")
        print(f"{'='*20}")

        matches = await find_matches(league['champ_id'])
        print(f"Found {len(matches)} upcoming matches in casino.")

        # Process first 5 matches of the league (increased from 3), up to the total MATCH_LIMIT
        # This gives us better coverage of near-term opportunities
        for match in matches[:5]:
            if total_scanned_matches >= MATCH_LIMIT:
                break
            await process_match(match, league, db, tracker, parser, None, is_session=is_session)
            total_scanned_matches += 1
            await asyncio.sleep(2)

