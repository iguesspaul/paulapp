"""
Pinnacle harvester — uses guest.api.arcadia.pinnacle.com (no auth required).

Flow:
  1. Fetch all active soccer leagues  (/sports/29/leagues)
  2. Find best-matching league by comparing pin_path tokens against league names
  3. Fetch all matchups in that league  (/leagues/{leagueId}/matchups)
  4. Find best-matching matchup by fuzzy team-name scoring
  5. Fetch straight markets for that matchup  (/matchups/{id}/markets/straight)
  6. Extract 1x2 and Over/Under 2.5 (American to decimal conversion)
     (uses participant alignment/order from matchup participants)

Output format unchanged:  {"book": "Pinnacle Direct", "odds": {"1": ..., "X": ..., "2": ..., "Over2.5": ..., "Under2.5": ...}}
"""

import json
import time
import urllib.request

from .normalizer import (
    american_to_decimal,
    get_alias,
    make_slug,
    name_match_score,
    normalize,
    normalize_slug,
)

_BASE = "https://guest.api.arcadia.pinnacle.com/0.1"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Origin": "https://www.pinnacle.com",
    "Referer": "https://www.pinnacle.com/",
}


def _get_json(url: str):
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except Exception as e:
        print(f"[PINNACLE] API error {url}: {e}")
        return None


def _get_markets(matchup_id, league_id=None, participants=None) -> list | None:
    """
    Fetch markets for a matchup. Tries league-level endpoint first (bundles all
    matchup markets — avoids the per-matchup 401 issue), then falls back to
    per-matchup endpoints with retry.

    League-level: /leagues/{leagueId}/markets/straight (returns all matchups)
    Per-matchup: /matchups/{matchup_id}/markets/straight (often 401)

    Some matchups have a 2-way format (home/away) with full markets and a 3-way
    format (home/away/draw) with only moneyline. When participants are provided,
    searches for the 2-way counterpart to get O/U markets.
    """
    # Strategy 1: League-level endpoint (more reliable, no 401 issues)
    if league_id is not None:
        league_url = f"{_BASE}/leagues/{league_id}/markets/straight"
        try:
            req = urllib.request.Request(league_url, headers=_HEADERS)
            resp = urllib.request.urlopen(req, timeout=15)
            all_markets = json.loads(resp.read())
            if isinstance(all_markets, list):
                # Try our exact matchup_id first
                match_markets = [m for m in all_markets if m.get("matchupId") == matchup_id]

                # If we only got a moneyline market (no O/U), look for a 2-way
                # counterpart with the same teams that has full markets
                if len(match_markets) <= 1 and participants:
                    team_names = {
                        p.get("name", "").lower()
                        for p in participants
                        if p.get("alignment") not in ("draw",)
                        and p.get("name", "").lower() not in ("neither", "draw")
                    }
                    if team_names:
                        # Count markets per alternative matchup
                        market_counts = {}
                        for m in all_markets:
                            mid = m.get("matchupId")
                            if mid == matchup_id:
                                continue
                            market_counts[mid] = market_counts.get(mid, 0) + 1

                        # Get matchups to find team names for alternatives
                        alt_url = f"{_BASE}/leagues/{league_id}/matchups"
                        try:
                            alt_req = urllib.request.Request(alt_url, headers=_HEADERS)
                            alt_matchups = json.loads(
                                urllib.request.urlopen(alt_req, timeout=15).read()
                            )
                            best_alt_id = None
                            best_alt_count = 0
                            for am in alt_matchups:
                                amid = am["id"]
                                if amid == matchup_id:
                                    continue
                                if amid not in market_counts:
                                    continue
                                alt_names = {
                                    p.get("name", "").lower() for p in am.get("participants", [])
                                }
                                # Check if this alt has the same team names (minus draw/neither)
                                alt_teams = {n for n in alt_names if n not in ("neither", "draw")}
                                if alt_teams == team_names and market_counts[amid] > best_alt_count:
                                    best_alt_id = amid
                                    best_alt_count = market_counts[amid]

                            if best_alt_id and best_alt_count > len(match_markets):
                                alt_markets = [
                                    m for m in all_markets if m.get("matchupId") == best_alt_id
                                ]
                                print(
                                    f"[PINNACLE] Found 2-way counterpart matchup {best_alt_id} with {len(alt_markets)} markets (vs {len(match_markets)} for 3-way {matchup_id})"
                                )
                                return alt_markets
                        except Exception:
                            pass

                if match_markets:
                    return match_markets
        except Exception as e:
            print(f"[PINNACLE] League-level markets failed: {e}")

    # Strategy 2: Per-matchup endpoint with retry
    endpoints = [
        f"{_BASE}/matchups/{matchup_id}/markets/straight",
        f"{_BASE}/matchups/{matchup_id}/markets",
    ]

    for endpoint in endpoints:
        for attempt in range(3):
            try:
                req = urllib.request.Request(endpoint, headers=_HEADERS)
                resp = urllib.request.urlopen(req, timeout=15)
                markets = json.loads(resp.read())
                if isinstance(markets, list):
                    if attempt > 0:
                        print(
                            f"[PINNACLE] Markets recovered after {attempt} retries on {endpoint.split('/')[-1]}"
                        )
                    return markets
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    if attempt < 2:
                        wait = 0.5 * (2**attempt)
                        time.sleep(wait)
                        continue
                    print(f"[PINNACLE] Markets 401 on {endpoint.split('/')[-1]} after 3 attempts")
                else:
                    print(f"[PINNACLE] Markets HTTP {e.code} on {endpoint}")
                    break
            except Exception as e:
                print(f"[PINNACLE] Markets error on {endpoint}: {e}")
                break

    return None


def _find_league(leagues: list, pin_path: str, known_name: str = "") -> dict | None:
    """
    Match pin_path against Pinnacle league names.
    Uses exact match from alias first, then token-set intersection.
    """
    # Strategy 1: exact name match (from alias table)
    if known_name:
        for league in leagues:
            if league.get("name") == known_name:
                print(f"[PINNACLE] Exact match from alias: '{known_name}'")
                return league
        print(
            f"[PINNACLE] Alias exact match not found for '{known_name}', falling back to token scoring"
        )

    # Strategy 2: token-set intersection scoring
    slug_tokens = set(normalize_slug(pin_path).split())
    best_score = 0.0
    best_league = None

    for league in leagues:
        name_tokens = set(normalize(league.get("name", "")).split())
        if not name_tokens:
            continue
        intersection = len(slug_tokens & name_tokens)
        score = intersection / max(len(slug_tokens), len(name_tokens))
        if score > best_score:
            best_score = score
            best_league = league

    if best_score >= 0.5 and best_league:
        print(f"[PINNACLE] League match: '{best_league['name']}' (score={best_score:.2f})")
        return best_league

    print(f"[PINNACLE] No league match for pin_path='{pin_path}' (best score={best_score:.2f})")
    return None


def _find_matchup(matchups: list, team_a: str, team_b: str) -> dict | None:
    """Find the best matchup by word-set intersection on both team names."""
    best_score = 0.0
    best_matchup = None

    for m in matchups:
        participants = m.get("participants", [])
        # Filter to team participants only (exclude draws/neithers)
        teams = [p for p in participants if p.get("alignment") not in ("draw",)]
        if len(teams) < 2:
            continue

        home_name = teams[0].get("name", "")
        away_name = teams[1].get("name", "")

        score_direct = (
            name_match_score(team_a, home_name) + name_match_score(team_b, away_name)
        ) / 2
        score_swap = (name_match_score(team_a, away_name) + name_match_score(team_b, home_name)) / 2
        score = max(score_direct, score_swap)

        min_direct = min(name_match_score(team_a, home_name), name_match_score(team_b, away_name))
        min_swap = min(name_match_score(team_a, away_name), name_match_score(team_b, home_name))
        if max(min_direct, min_swap) < 0.3:
            continue

        if score > best_score:
            best_score = score
            best_matchup = m

    if best_score >= 0.4 and best_matchup:
        names = [p.get("name", "") for p in best_matchup.get("participants", [])]
        print(f"[PINNACLE] Matchup match: {names} (score={best_score:.2f})")
        return best_matchup

    print(f"[PINNACLE] No matchup match for {team_a} vs {team_b} (best={best_score:.2f})")
    return None


def _build_participant_map(participants: list) -> dict:
    """
    Build a mapping from participantId / position to label.
    Returns a dict: {participant_id: {"name": ..., "role": "home"|"away"|"draw"}}
    """
    pmap = {}
    for p in participants:
        pid = p.get("id")
        name = p.get("name", "")
        alignment = p.get("alignment", "neutral")
        if alignment == "home":
            role = "home"
        elif alignment == "away":
            role = "away"
        elif alignment == "draw" or name.lower() in ("draw", "neither", "tie"):
            role = "draw"
        else:
            # For neutral alignments (friendlies), first 2 are teams, rest may be draws
            role = "unknown"

        entry = {"name": name, "role": role}
        if pid is not None:
            pmap[pid] = entry
        # Also store by position order for fallback
        pmap.setdefault(order := p.get("order", len(pmap)), {}).update({"order": order, **entry})

    return pmap


def _resolve_price_role(price: dict, pmap: dict, key: str) -> str | None:
    """
    Given a price entry and participant map, determine the role (home/draw/away/over/under).
    Tries participantId lookup, then falls back to position heuristic.
    """
    # For O/U markets, check designation first
    if "ou" in key or "tt" in key:
        desig = price.get("designation", "")
        if desig:
            return desig

    # Try participantId mapping
    pid = price.get("participantId")
    if pid and pid in pmap:
        return pmap[pid]["role"]

    # Try position-based heuristic (fallback)
    points = price.get("points")
    if points == 2.5:
        # O/U market: first price is over, second is under
        return None  # caller handles by position

    # No mapping available — caller should use ordinal position
    return None


def _parse_markets(markets: list, participants: list | None = None) -> dict:
    """
    Extract 1x2 and Over/Under 2.5 decimal odds from market list.

    New API format: prices use participantId instead of designation.
    participantId maps to the matchup's participants array.
    If participants are unavailable, falls back to price position (ordinal).

    Market key structure:
      's;0;m'    — 1x2 (full match moneyline)
      's;1;m'    — 1x2 (first half moneyline — skipped)
      's;0;ou'   — Over/Under (total goals)
      's;0;tt'   — Team total (skipped)
    """
    pmap = _build_participant_map(participants) if participants else {}

    odds = {}

    for market in markets:
        key = market.get("key", "")
        prices = market.get("prices", [])
        if not prices:
            continue

        # --- 1x2 moneyline (full match only) ---
        if key == "s;0;m":
            # Try mapping via participantIds
            home_set = False
            away_set = False
            for price in prices:
                pval = price.get("price")
                if pval is None:
                    continue
                pid = price.get("participantId")
                if pid and pid in pmap:
                    role = pmap[pid]["role"]
                    if role == "home":
                        odds["1"] = american_to_decimal(pval)
                        home_set = True
                    elif role == "away":
                        odds["2"] = american_to_decimal(pval)
                        away_set = True
                    elif role == "draw":
                        odds["X"] = american_to_decimal(pval)

            # Fallback: use ordinal position (1st=home, 2nd=away, 3rd=draw)
            if not home_set and not away_set:
                if len(prices) >= 1:
                    odds["1"] = american_to_decimal(prices[0]["price"])
                if len(prices) >= 2:
                    odds["2"] = american_to_decimal(prices[1]["price"])
                if len(prices) >= 3:
                    draw_idx = 2 if len(prices) >= 3 else None
                    if draw_idx is not None:
                        odds["X"] = american_to_decimal(prices[draw_idx]["price"])

        # --- Over/Under total goals ---
        elif "ou" in key or "tt" in key:
            parts = key.split(";")
            # Skip team-specific totals (home/away suffix in key)
            if len(parts) >= 5 and parts[-1] in ("home", "away"):
                continue

            # Collect O/U prices for the 2.5 line
            over_val = None
            under_val = None
            for price in prices:
                pts = price.get("points")
                pval = price.get("price")
                if pts == 2.5 and pval is not None:
                    # Try designation first
                    desig = price.get("designation", "")
                    if desig == "over":
                        over_val = pval
                    elif desig == "under":
                        under_val = pval
                    # If no designation, use position: first=over, second=under
                    elif over_val is None:
                        over_val = pval
                    elif under_val is None:
                        under_val = pval

            if over_val is not None:
                odds["Over2.5"] = american_to_decimal(over_val)
            if under_val is not None:
                odds["Under2.5"] = american_to_decimal(under_val)

    return odds


async def harvest(
    pin_path: str, team_a: str, team_b: str, league_name: str = "", country_name: str = ""
) -> dict:
    """
    Fetch Pinnacle sharp odds via the public arcadia guest API.
    No Playwright or browser required — pure HTTP.
    Uses /markets/straight endpoint (old /related/straight is deprecated).

    Returns: {"book": "Pinnacle Direct", "odds": {"1": ..., "X": ..., "2": ..., "Over2.5": ..., "Under2.5": ...}}
    """
    result = {"book": "Pinnacle Direct", "odds": {}}

    try:
        print(f"[PINNACLE] Fetching league list for pin_path='{pin_path}'")
        leagues = _get_json(f"{_BASE}/sports/29/leagues?all=false")
        if not leagues:
            print("[PINNACLE] Failed to fetch leagues")
            return result

        # 2. Find matching league — check aliases first
        known_name = ""
        if league_name:
            slug = make_slug(league_name)
            country_slug = make_slug(country_name) if country_name else ""
            alias = get_alias(slug, country_slug)
            if alias and alias.get("pinnacle_name"):
                known_name = alias["pinnacle_name"]
                print(f"[PINNACLE] Using alias exact name: '{known_name}' (from '{league_name}')")

        league = _find_league(leagues, pin_path, known_name)
        if not league:
            return result

        league_id = league["id"]

        # 3. Fetch matchups in that league
        matchups = _get_json(f"{_BASE}/leagues/{league_id}/matchups")
        if not matchups:
            print(f"[PINNACLE] No matchups in league '{league['name']}' (id={league_id})")
            return result

        print(f"[PINNACLE] Found {len(matchups)} matchups in '{league['name']}'")

        # 4. Find the matching matchup
        matchup = _find_matchup(matchups, team_a, team_b)
        if not matchup:
            return result

        matchup_id = matchup["id"]
        participants = matchup.get("participants", [])

        # 5. Fetch markets — league-level (avoids 401) with 2-way fallback
        markets = _get_markets(matchup_id, league_id, participants)
        if not markets:
            print(f"[PINNACLE] No markets for matchup {matchup_id}")
            return result

        print(f"[PINNACLE] Fetched {len(markets)} markets for matchup {matchup_id}")

        # 6. Parse odds — pass participants for price-to-role mapping
        odds = _parse_markets(markets, participants)
        result["odds"] = odds

        if odds:
            print(f"[PINNACLE] Extracted odds: {odds}")
        else:
            print("[PINNACLE] No 1x2/O/U odds found in markets (check market keys)")

    except Exception as e:
        print(f"[PINNACLE] Harvest error: {e}")

    return result


async def find_match_url(page, pin_path, team_a, team_b):  # noqa: ARG001
    """Deprecated: Pinnacle now uses the arcadia API directly. Returns None."""
    return None
