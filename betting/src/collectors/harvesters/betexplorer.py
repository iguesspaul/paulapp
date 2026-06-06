"""
BetExplorer harvester — Playwright-based with search API fallback and JSON odds endpoints.

Flow:
  1. Try league page navigation via be_path (fast path when URL guess is correct)
  2. Fall back to BetExplorer search API to find the correct league URL by name+country
  3. Find the match row using data-id attribute from table rows
  4. Fall back to anchor link scanning if data attributes not found
  5. Fetch 1x2 and O/U odds via JSON endpoint: /match-odds/{match_id}/1/{market}/
  6. Fall back to DOM extraction on the match page if JSON fails

The be_path param (e.g. 'soccer/england/premier-league') is still accepted for backwards
compatibility. Optional league_name and country_name parameters enable the search API
fallback, which bypasses be_path guessing entirely.

Output format unchanged:
  [{"book": "Pinnacle", "odds": {...}}, {"book": "bet365", "odds": {...}}, ...]
"""

import asyncio
import json
import re
import urllib.request
import urllib.parse
from playwright.async_api import async_playwright

try:
    from playwright_stealth import stealth_async
except ImportError:
    stealth_async = None

from .normalizer import name_match_score, normalize, get_alias

_TARGET_BOOKS = ["Pinnacle", "bet365", "SBOBET", "188BET", "Betfair"]
_ODDS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.betexplorer.com/",
}

# BetExplorer uses /football/ internally; /soccer/ redirects there
_BE_BASE = "https://www.betexplorer.com"


def _be_path_to_url(be_path: str) -> str:
    """
    Convert 'soccer/england/premier-league' or 'football/england/premier-league'
    to https://www.betexplorer.com/football/england/premier-league/
    """
    path = re.sub(r"^(soccer|football)/", "", be_path.strip("/"))
    return f"{_BE_BASE}/football/{path}/"


def _search_league_url(league_name: str, country_name: str = "", all_matches: bool = False) -> str | None | list:
    """
    Use BetExplorer's internal search API to find the correct league page URL.
    Searches by league name, then filters results by country name.

    If all_matches=True, returns a list of all (url, score) pairs above threshold
    (useful for leagues split into multiple groups, like FNL 2 groups).
    Otherwise returns the single best URL or None.

    This bypasses the brittle be_path slug guessing entirely.
    """
    query = urllib.parse.quote(league_name)
    url = f"{_BE_BASE}/gres/ajax/search.php?text={query}&sid=0&lang=en"
    headers = {
        "User-Agent": _ODDS_HEADERS["User-Agent"],
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[BETEXPLORER] Search API request failed: {e}")
        return None

    # Find the Competitions section in the returned HTML
    comp_idx = html.find("Competitions")
    if comp_idx < 0:
        print(f"[BETEXPLORER] No competitions in search results for '{league_name}'")
        return None

    comp_html = html[comp_idx:]

    # Parse all competition links (two formats: with and without <b> tags)
    # Format A: <a ...>Country: <b>League</b></a>  (search term matched league)
    # Format B: <a ...>Country: League</a>          (no bold, but still a valid result)
    bold_pattern = re.compile(
        r'<a\s+class="list-events__item__title"\s+href="(/football/[^"]+/)">'
        r'([^<]+):\s*<b>([^<]+)</b>'
    )
    plain_pattern = re.compile(
        r'<a\s+class="list-events__item__title"\s+href="(/football/[^"]+/)">'
        r'([^<]+):\s*([^<]+)</a>'
    )

    # Collect both, deduplicate by URL (plain entries can duplicate <b> entries)
    seen = set()
    raw_matches = []
    for href, country, league in bold_pattern.findall(comp_html):
        if href not in seen:
            seen.add(href)
            raw_matches.append((href, country, league))
    for href, country, league in plain_pattern.findall(comp_html):
        if href not in seen:
            seen.add(href)
            raw_matches.append((href, country, league))

    if not raw_matches:
        print(f"[BETEXPLORER] No competition links parsed from search")
        return None

    matches = raw_matches

    country_norm = normalize(country_name) if country_name else ""
    league_norm = normalize(league_name)

    # Score all matches
    scored = []
    for href, result_country, result_league in matches:
        r_country_norm = normalize(result_country)
        r_league_norm = normalize(result_league)

        # League name score (primary)
        score = name_match_score(league_norm, r_league_norm) * 0.7
        # Country bonus (if provided)
        if country_norm and r_country_norm:
            country_score = name_match_score(country_norm, r_country_norm)
            score += country_score * 0.3

        scored.append((score, f"{_BE_BASE}{href}"))

    # Filter by threshold and sort descending
    above = [(s, u) for s, u in scored if s >= 0.4]
    above.sort(key=lambda x: -x[0])

    if not above:
        best = max([s for s, _ in scored], default=0.0)
        print(f"[BETEXPLORER] Search could not match league '{league_name}' (best={best:.2f})")
        return None

    if all_matches:
        print(f"[BETEXPLORER] Search returned {len(above)} league URLs for '{league_name}'")
        for s, u in above:
            print(f"  [{s:.2f}] {u}")
        return above  # list of (score, url)

    # Single result: return best URL
    best_url = above[0][1]
    print(f"[BETEXPLORER] Search resolved league URL: {best_url} (score={above[0][0]:.2f})")
    return best_url


def _fetch_json_odds(match_id: str, market: str) -> dict | None:
    """Fetch odds JSON from BetExplorer's internal endpoint."""
    url = f"{_BE_BASE}/match-odds/{match_id}/1/{market}/"
    try:
        req = urllib.request.Request(url, headers=_ODDS_HEADERS)
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        print(f"[BETEXPLORER] JSON odds fetch failed ({market}): {e}")
        return None


def _parse_json_1x2(data: dict) -> dict:
    """Parse 1x2 odds from BetExplorer JSON response."""
    result = {}
    if not data:
        return result

    rows = None
    for key in ("odds", "data", "rows", "bets"):
        if key in data and isinstance(data[key], list):
            rows = data[key]
            break

    if rows is None:
        return result

    for row in rows:
        book_name = row.get("n", row.get("name", row.get("bookmaker", "")))
        book_match = None
        for tb in _TARGET_BOOKS:
            if tb.lower() in book_name.lower():
                book_match = tb
                break
        if not book_match:
            continue

        raw_odds = row.get("odds", row.get("o", []))
        if isinstance(raw_odds, list) and len(raw_odds) >= 3:
            try:
                result[book_match] = {
                    "1": float(raw_odds[0]),
                    "X": float(raw_odds[1]),
                    "2": float(raw_odds[2]),
                }
            except (ValueError, TypeError):
                pass
        elif isinstance(raw_odds, dict):
            try:
                result[book_match] = {
                    "1": float(raw_odds.get("1", raw_odds.get("home", 0))),
                    "X": float(raw_odds.get("X", raw_odds.get("draw", 0))),
                    "2": float(raw_odds.get("2", raw_odds.get("away", 0))),
                }
            except (ValueError, TypeError):
                pass

    return result


def _parse_json_ou(data: dict) -> dict:
    """Parse Over/Under 2.5 from BetExplorer JSON response."""
    result = {}
    if not data:
        return result

    rows = None
    for key in ("odds", "data", "rows", "bets"):
        if key in data and isinstance(data[key], list):
            rows = data[key]
            break

    if rows is None:
        return result

    for row in rows:
        book_name = row.get("n", row.get("name", row.get("bookmaker", "")))
        book_match = None
        for tb in _TARGET_BOOKS:
            if tb.lower() in book_name.lower():
                book_match = tb
                break
        if not book_match:
            continue

        handicap = str(row.get("handicap", row.get("points", row.get("line", ""))))
        if "2.5" not in handicap:
            continue

        raw_odds = row.get("odds", row.get("o", []))
        if isinstance(raw_odds, list) and len(raw_odds) >= 2:
            try:
                result[book_match] = {
                    "Over2.5": float(raw_odds[0]),
                    "Under2.5": float(raw_odds[1]),
                }
            except (ValueError, TypeError):
                pass

    return result


async def _find_match_id(page, league_url: str, team_a: str, team_b: str) -> tuple:
    """
    Navigate to the BetExplorer league page and find the match ID and odds for team_a vs team_b.

    Strategy: scan all table rows for team-name links and button odds.
    BetExplorer's current structure uses plain <tr> rows (no data-id/data-eventid attributes)
    with <button> elements holding decimal odds next to team-name links.

    Returns: (match_id: str | None, inline_odds: list[float])
    """
    print(f"[BETEXPLORER] Navigating to {league_url}")
    try:
        await page.goto(league_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
    except Exception as e:
        print(f"[BETEXPLORER] Page load failed: {e}")
        return None, []

    # Scan all table rows for match candidates (team names + odds)
    rows = await page.evaluate('''() => {
        return Array.from(document.querySelectorAll('tr'))
            .map(row => {
                // Extract team-link text (e.g. "Vanuatu - Fiji" or "Haiti - Peru")
                const links = Array.from(row.querySelectorAll('a'));
                const teamLink = links.find(a => a.href.includes('/football/') && a.innerText.includes(' - '));
                const text = teamLink ? teamLink.innerText.trim() : '';
                
                // Extract odds from <button> elements (decimal odds)
                const odds = Array.from(row.querySelectorAll('button'))
                    .map(b => parseFloat(b.innerText))
                    .filter(v => !isNaN(v) && v > 1.0);
                
                // Extract matchId from deep URL for JSON fallback
                let matchId = '';
                if (teamLink) {
                    const parts = teamLink.href.replace(/\\/+$/, '').split('/');
                    const last = parts[parts.length - 1];
                    if (parts.length >= 8 && /^[a-zA-Z0-9]{6,12}$/.test(last)) {
                        matchId = last;
                    }
                }
                
                return { text: text, odds: odds, matchId: matchId };
            })
            .filter(r => r.text.includes(' - '));
    }''')

    if not rows:
        print(f"[BETEXPLORER] No match rows found on page")
        return None, []

    # Score and find best match
    best_result = None
    best_score = 0.0
    for row in rows:
        text = row.get("text", "")
        parts = text.split(" - ")
        if len(parts) < 2:
            continue

        score = (name_match_score(team_a, parts[0]) +
                 name_match_score(team_b, parts[1])) / 2

        if score > best_score:
            best_score = score
            best_result = row

    if best_score >= 0.35 and best_result:
        mid = best_result.get("matchId", "")
        odds = best_result.get("odds", [])
        print(f"[BETEXPLORER] Found match via row scan (score={best_score:.2f}): {best_result['text']}")
        if mid:
            print(f"  matchId={mid}")
        if odds:
            print(f"  inline odds (H/D/A): {odds[0] if len(odds) > 0 else '-'} / {odds[1] if len(odds) > 1 else '-'} / {odds[2] if len(odds) > 2 else '-'}")
        return mid, odds

    print(f"[BETEXPLORER] Could not find match for {team_a} vs {team_b} (best={best_score:.2f})")
    return None, []


async def _dom_fallback_odds(page, match_id: str, books: list) -> dict:
    """Fallback: extract odds via DOM when JSON endpoints fail."""
    match_url = f"{_BE_BASE}/match/{match_id}/"
    print(f"[BETEXPLORER] DOM fallback: {match_url}")
    try:
        await page.goto(match_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)

        data = await page.evaluate('''(books) => {
            const res = {};
            books.forEach(b => res[b] = {});
            const rows = Array.from(document.querySelectorAll('tr'));
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                const bookMatch = books.find(b => text.includes(b.toLowerCase()));
                if (bookMatch) {
                    const oddsCells = Array.from(row.querySelectorAll('td')).filter(
                        c => c.getAttribute('data-odd') || /^\\d+\\.\\d+$/.test(c.innerText.trim())
                    );
                    if (oddsCells.length >= 3) {
                        res[bookMatch]['1'] = parseFloat(oddsCells[0].getAttribute('data-odd') || oddsCells[0].innerText);
                        res[bookMatch]['X'] = parseFloat(oddsCells[1].getAttribute('data-odd') || oddsCells[1].innerText);
                        res[bookMatch]['2'] = parseFloat(oddsCells[2].getAttribute('data-odd') || oddsCells[2].innerText);
                    }
                }
            });
            return res;
        }''', books)
        return data
    except Exception as e:
        print(f"[BETEXPLORER] DOM fallback failed: {e}")
        return {}


async def harvest_sharp_odds(be_path: str, team_a: str, team_b: str,
                              league_name: str = "", country_name: str = "") -> list:
    """
    Harvests sharp book odds from BetExplorer.

    New search API fallback: if league_name is provided and the be_path-derived
    league page fails to find a match, uses BetExplorer's internal search API
    to find the correct league URL (bypassing be_path slug guessing entirely).

    Returns: [{"book": bookname, "odds": {...}}, ...]
    """
    results = [{"book": b, "odds": {}} for b in _TARGET_BOOKS]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=_ODDS_HEADERS["User-Agent"]
        )
        page = await context.new_page()
        if stealth_async:
            await stealth_async(page)

        try:
            # --- Resolve league URL ---
            # Check for league name aliases (to fix name mismatches)
            resolved_url = None
            search_term = league_name
            slug = be_path.rstrip("/").split("/")[-1] if be_path else ""
            country_slug = be_path.rstrip("/").split("/")[-2] if be_path and "/" in be_path else ""
            alias = get_alias(slug, country_slug) if slug else None
            if alias and alias.get("betexplorer_search"):
                search_term = alias["betexplorer_search"]

            match_id = None
            inline_odds = []

            # Try search API first (with aliased search term if available)
            if search_term:
                print(f"[BETEXPLORER] Searching with term: '{search_term}'" + (f" (alias from '{league_name}')" if search_term != league_name else ""))
                # Check if this league has multiple groups (like FNL 2)
                league_urls = _search_league_url(search_term, country_name, all_matches=True)
                if isinstance(league_urls, list):
                    # Multi-group league: try each URL until we find the match
                    for score, url in league_urls:
                        print(f"[BETEXPLORER] Trying league URL (score={score:.2f}): {url}")
                        match_id, inline_odds = await _find_match_id(page, url, team_a, team_b)
                        if match_id:
                            resolved_url = url
                            print(f"[BETEXPLORER] Found match in: {url}")
                            break
                elif isinstance(league_urls, str):
                    resolved_url = league_urls

            # Fall back to be_path-derived URL if search didn't find anything
            if not match_id:
                league_url = _be_path_to_url(be_path)
                if not resolved_url:
                    resolved_url = league_url
                    print(f"[BETEXPLORER] Search failed, falling back to be_path URL: {league_url}")
                elif resolved_url != league_url:
                    print(f"[BETEXPLORER] Using resolved URL (differs from be_path): {resolved_url}")
                match_id, inline_odds = await _find_match_id(page, resolved_url, team_a, team_b)

            if not match_id:
                print(f"[BETEXPLORER] No match found for {team_a} vs {team_b}")
                return results

            print(f"[BETEXPLORER] Fetching odds for match_id={match_id}")

            # Strategy A: Try JSON endpoints first (work for some leagues)
            raw_1x2 = _fetch_json_odds(match_id, "1x2")
            raw_ou = _fetch_json_odds(match_id, "ou")

            print(f"[BETEXPLORER] 1x2 raw: {str(raw_1x2)[:200]}")
            print(f"[BETEXPLORER] O/U raw: {str(raw_ou)[:200]}")

            parsed_1x2 = _parse_json_1x2(raw_1x2) if raw_1x2 else {}
            parsed_ou = _parse_json_ou(raw_ou) if raw_ou else {}

            # Strategy B: If JSON returned nothing, use inline odds from table row
            if not parsed_1x2 and inline_odds:
                print(f"[BETEXPLORER] JSON endpoints failed, using inline odds from table: {inline_odds}")
                # Inline odds are decimal, typically [home, draw, away]
                # We map these by position — assumes all target books share the same market price
                if len(inline_odds) >= 3:
                    for i, book in enumerate(_TARGET_BOOKS):
                        # Pinnacle and bet365 likely set the market price
                        results[i]["odds"]["1"] = inline_odds[0]
                        results[i]["odds"]["X"] = inline_odds[1]
                        results[i]["odds"]["2"] = inline_odds[2]
                        print(f"[BETEXPLORER] Set {book} 1x2 from inline odds: {inline_odds[0]}, {inline_odds[1]}, {inline_odds[2]}")

            # Strategy C: If both failed, try DOM fallback on the match page
            if not parsed_1x2 and not inline_odds:
                print("[BETEXPLORER] JSON and inline odds both empty -- trying DOM fallback")
                dom_data = await _dom_fallback_odds(page, match_id, _TARGET_BOOKS)
                for book in _TARGET_BOOKS:
                    if book in dom_data and dom_data[book]:
                        parsed_1x2[book] = dom_data[book]

            # Merge JSON/DOM results into results
            for i, book in enumerate(_TARGET_BOOKS):
                if book in parsed_1x2:
                    results[i]["odds"].update(parsed_1x2[book])
                if book in parsed_ou:
                    results[i]["odds"].update(parsed_ou[book])

            has_any = any(r["odds"] for r in results)
            if has_any:
                print(f"[BETEXPLORER] Successfully extracted odds for {team_a} vs {team_b}")
            else:
                print(f"[BETEXPLORER] No odds extracted for {team_a} vs {team_b}")

        except Exception as e:
            print(f"[BETEXPLORER] Harvest error: {e}")
        finally:
            await browser.close()

    return results


async def find_match_url(page, be_path, team_a, team_b):
    """Deprecated: use harvest_sharp_odds directly."""
    league_url = _be_path_to_url(be_path)
    match_id, _ = await _find_match_id(page, league_url, team_a, team_b)
    return f"{_BE_BASE}/match/{match_id}/" if match_id else None
