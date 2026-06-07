import asyncio
import os

from src.collectors.casino_parser import CasinoParser
from src.collectors.harvesters import betexplorer, pinnacle
from src.collectors.market_resolver import MarketResolver
from src.collectors.scraper import discover_active_leagues, fetch_page_json, find_matches
from src.core.config import KELLY_MULTIPLIER
from src.core.database import BettingDatabase
from src.core.tracker import BetTracker
from src.math.bankroll_manager import calculate_kelly_stake
from src.math.ev import calculate_ev, calculate_fair_odds
from src.math.probability_grid import ProbabilityGrid
from src.math.sharp_consensus import get_consensus_lambda, solve_implied_lambdas_from_consensus

# Session accumulator — tracks totals across all matches processed in one scan run
_session_stake_total = 0.0
_session_ev_total = 0.0
_session_bets_logged = 0


async def process_match(
    match,
    league_config,
    db,
    tracker,
    parser,
    consensus_engine,  # noqa: ARG001
    is_session=True,
):
    """
    Processes a single match: harvests sharps, calculates EV, and saves.
    Uses the current bankroll from the DB for Kelly sizing.
    """
    global _session_stake_total, _session_ev_total, _session_bets_logged

    teams = match["name"].split(" vs. ")
    if len(teams) != 2:
        return

    team_a, team_b = teams[0], teams[1]
    print(f"\n[ORCHESTRATOR] Processing: {team_a} vs {team_b}")

    # 1. Harvest Sharp Odds in Parallel
    results = await asyncio.gather(
        betexplorer.harvest_sharp_odds(
            league_config["be_path"],
            team_a,
            team_b,
            league_name=league_config.get("name", ""),
            country_name=league_config.get("country", ""),
        ),
        pinnacle.harvest(
            league_config["pin_path"],
            team_a,
            team_b,
            league_name=league_config.get("name", ""),
            country_name=league_config.get("country", ""),
        ),
    )

    # Flatten results into a single list of book results
    sharp_results = []
    betexp_results, pin_result = results[0], results[1]
    if isinstance(betexp_results, list):
        sharp_results.extend(betexp_results)
    else:
        sharp_results.append(betexp_results)
    sharp_results.append(pin_result)

    # Log per-harvester status
    pin_odds = pin_result.get("odds", {}) if isinstance(pin_result, dict) else {}
    betexp_odds = any(
        r.get("odds")
        for r in (betexp_results if isinstance(betexp_results, list) else [betexp_results])
    )
    if pin_odds:
        print(f"[PINNACLE] Found odds for {team_a} vs {team_b}: {len(pin_odds)} markets")
    else:
        print(f"[PINNACLE] No odds found for {team_a} vs {team_b}")
    if betexp_odds:
        print(f"[BETEXPLORER] Found consensus odds for {team_a} vs {team_b}")
    else:
        print(f"[BETEXPLORER] No odds found for {team_a} vs {team_b}")

    has_odds = any(entry.get("odds") for entry in sharp_results)
    import json

    if has_odds:
        with open("data/sharps.json", "w") as f:
            json.dump(sharp_results, f, indent=2)
    else:
        print(f"[SKIP] No sharp odds found for {match['name']}, keeping old sharps.json")

    # 2. Resolve lambdas (consensus solver → fallback cascade)
    prob_grid, using_fallback = _resolve_lambdas(sharp_results, has_odds)
    if prob_grid is None:
        return

    resolver = MarketResolver(prob_grid)

    # 3. Fetch Casino Match Details
    os.makedirs("data", exist_ok=True)
    json_file = f"data/match_{match['id']}.json"
    success = await fetch_page_json(match["details_url"], json_file)
    if not success:
        return

    # 4. Parse, Resolve, and Track Markets
    raw_markets = parser.extract_markets(json_file)
    match_id = str(match["id"])
    current_bankroll = db.get_bankroll_balance()

    await _price_and_track_markets(
        raw_markets=raw_markets,
        resolver=resolver,
        db=db,
        match_id=match_id,
        match=match,
        team_a=team_a,
        team_b=team_b,
        league_config=league_config,
        tracker=tracker,
        parser=parser,
        is_session=is_session,
        using_fallback=using_fallback,
        current_bankroll=current_bankroll,
    )


def _resolve_lambdas(sharp_results: list, has_odds: bool):
    """Resolve probability lambdas: consensus solver → fallback cascade.

    Returns (ProbabilityGrid | None, using_fallback: bool).
    """
    home_lambda, away_lambda = None, None
    if has_odds:
        home_lambda, away_lambda = solve_implied_lambdas_from_consensus(sharp_results)

    if home_lambda is not None and away_lambda is not None:
        print(
            f"[SHARP] Solver Succeeded: Home Lambda = {home_lambda:.4f}, Away Lambda = {away_lambda:.4f}"
        )
        return ProbabilityGrid(home_lambda=home_lambda, away_lambda=away_lambda), False

    # Enter fallback cascade
    import json
    import os

    match_lambda = None
    if has_odds:
        match_lambda = get_consensus_lambda(sharp_results)
    else:
        print("[FALLBACK] Attempting to use global_lambda.json")
        if os.path.exists("data/global_lambda.json"):
            with open("data/global_lambda.json") as f:
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
        return None, True

    print(f"[SHARP] Consensus Match Lambda (Fallback): {match_lambda:.4f}")
    return ProbabilityGrid(match_lambda=match_lambda), True


async def _price_and_track_markets(
    raw_markets,
    resolver,
    db,
    match_id,
    match,
    team_a,
    team_b,
    league_config,
    tracker,
    parser,  # noqa: ARG001
    is_session,
    using_fallback,
    current_bankroll,
):
    """Price all casino markets against the probability grid and track +EV bets."""
    global _session_stake_total, _session_ev_total, _session_bets_logged
    seen_bets = set()

    for market in raw_markets:
        m_name = market["name"]
        for selection in market["selections"]:
            name = selection["name"]
            odds = selection["price"]

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
                db.insert_bet(match["details_url"], m_name, name, odds, fair_odds, ev)

                # Log if in realistic EV range (5% to 25%)
                if 0.05 < ev < 0.25:
                    # Kelly stake sized against current bankroll
                    stake = calculate_kelly_stake(
                        odds, fair_prob, current_bankroll, KELLY_MULTIPLIER
                    )

                    # Simulation Mode: skip bets calculated with fallback lambdas
                    # (no real sharp odds backing them — would distort performance tracking)
                    if is_session and using_fallback:
                        tag = "[FALLBACK BET (SKIPPED)]"
                        print(
                            f"{tag} [{m_name}] {name} @ {odds} | EV: {ev:+.2%} (no sharp odds, fallback lambda)"
                        )
                        continue

                    category = "Other"
                    if is_session:
                        start_time = match.get("start_time")
                        category, _ = tracker.log(
                            match_id=match_id,
                            market_name=m_name,
                            selection=name,
                            odds=odds,
                            fair_odds=fair_odds,
                            ev=ev,
                            stake=stake,
                            home_team=team_a,
                            away_team=team_b,
                            be_path=league_config["be_path"],
                            start_time=start_time,
                        )
                        # Accumulate totals for session summary
                        _session_stake_total += stake
                        _session_ev_total += stake * (fair_odds - 1) * fair_prob - stake * (
                            1 - fair_prob
                        )
                        _session_bets_logged += 1
                    else:
                        from src.core.tracker import categorize

                        category = categorize(m_name)

                    tag = "[+EV FOUND]"
                    print(
                        f"{tag} [{category}] {m_name} | {name} @ {odds} | Fair: {fair_odds:.2f} | EV: {ev:+.2%} | STAKE: ${stake:.2f}"
                    )


async def run_full_scan(is_session=True):
    """Runs a full scan across dynamically discovered active leagues."""
    global _session_stake_total, _session_ev_total, _session_bets_logged
    _session_stake_total = 0.0
    _session_ev_total = 0.0
    _session_bets_logged = 0

    print("--- Sentinel Multi-League Quant Agent Scan Started (Dynamic Mode) ---")

    db = BettingDatabase()
    tracker = BetTracker(db)
    parser = CasinoParser()

    print("Discovering active soccer leagues dynamically...")
    active_leagues = await discover_active_leagues()
    print(f"Discovered {len(active_leagues)} active leagues with prelive events.")

    total_scanned_matches = 0
    MATCH_LIMIT = 100

    for league in active_leagues:
        if total_scanned_matches >= MATCH_LIMIT:
            print(f"\n[SCAN] Reached total limit of {MATCH_LIMIT} scanned matches. Stopping scan.")
            break

        print(f"\n{'=' * 20}")
        print(
            f"DYNAMIC LEAGUE: {league['name']} ({league['country']}) - active events: {league['events_count']}"
        )
        print(f"{'=' * 20}")

        matches = await find_matches(league["champ_id"])
        print(f"Found {len(matches)} upcoming matches in casino.")

        for match in matches[:5]:
            if total_scanned_matches >= MATCH_LIMIT:
                break
            await process_match(match, league, db, tracker, parser, None, is_session=is_session)
            total_scanned_matches += 1
            await asyncio.sleep(2)

    # Deduct committed stakes from bankroll and log session summary
    if is_session and _session_bets_logged > 0:
        balance_before = db.get_bankroll_balance()
        balance_after = balance_before - _session_stake_total
        db.set_bankroll_balance(balance_after)
        db.record_session_summary(
            session_type="scan",
            total_stake_committed=round(_session_stake_total, 2),
            theoretical_ev_profit=round(_session_ev_total, 2),
            bets_logged=_session_bets_logged,
            balance_before=round(balance_before, 2),
            balance_after=round(balance_after, 2),
        )
        print("\n[BANKROLL] Session scan complete:")
        print(f"  Bets logged    : {_session_bets_logged}")
        print(f"  Total stake    : ${_session_stake_total:.2f}")
        print(f"  Theoretical EV : ${_session_ev_total:+.2f}")
        print(f"  Balance        : ${balance_before:.2f} -> ${balance_after:.2f}")
