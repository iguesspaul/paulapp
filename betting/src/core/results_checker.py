"""
results_checker.py — Automatically fetches final scores and period scores from BetExplorer Match Pages
and settles all unsettled bets in simulated_bets.

Called automatically from run_session.py before each new scan.
"""

import asyncio
import difflib
import re
from datetime import UTC, datetime, timedelta

from playwright.async_api import async_playwright

try:
    from playwright_stealth import stealth_async
except ImportError:
    stealth_async = None


# ─── Score Evaluators ──────────────────────────────────────────────────────────


def evaluate_double_chance(
    dc_part: str, h: int, a: int, home_team: str | None = None, away_team: str | None = None
) -> bool | None:
    dc_part = dc_part.lower().strip()
    home = home_team.lower().strip() if home_team else None
    away = away_team.lower().strip() if away_team else None

    # Try matching by splitting by / or 'or' if it contains them
    choices = [c.strip() for c in re.split(r"/|\bor\b", dc_part)]
    if len(choices) == 2:
        c1, c2 = choices[0], choices[1]

        def is_h(c):
            if c in ("1", "home"):
                return True
            if not home:
                return False
            c_clean = re.sub(r"[^a-z0-9]", "", c)
            h_clean = re.sub(r"[^a-z0-9]", "", home)
            return c_clean and h_clean and (c_clean in h_clean or h_clean in c_clean)

        def is_a(c):
            if c in ("2", "away"):
                return True
            if not away:
                return False
            c_clean = re.sub(r"[^a-z0-9]", "", c)
            a_clean = re.sub(r"[^a-z0-9]", "", away)
            return c_clean and a_clean and (c_clean in a_clean or a_clean in c_clean)

        def is_x(c):
            return c in ("x", "draw")

        has_home = is_h(c1) or is_h(c2)
        has_away = is_a(c1) or is_a(c2)
        has_draw = is_x(c1) or is_x(c2)

        if has_home and has_draw:
            return h >= a
        if has_away and has_draw:
            return a >= h
        if has_home and has_away:
            return h != a

    # Fallback to standard symbolic strings
    if any(
        x in dc_part
        for x in ("1x", "x1", "home/x", "x/home", "home or draw", "draw or home", "1/x", "x/1")
    ):
        return h >= a
    if any(
        x in dc_part
        for x in ("x2", "2x", "x/away", "away/x", "draw or away", "away or draw", "x/2", "2/x")
    ):
        return a >= h
    if any(
        x in dc_part
        for x in (
            "12",
            "21",
            "home/away",
            "away/home",
            "home or away",
            "away or home",
            "1/2",
            "2/1",
        )
    ):
        return h != a

    return None


def evaluate_1x2(
    res_part: str, h: int, a: int, home_team: str | None = None, away_team: str | None = None
) -> bool | None:
    res_part = res_part.lower().strip()
    home = home_team.lower().strip() if home_team else None
    away = away_team.lower().strip() if away_team else None

    if res_part in ("1", "home") or (
        home and (res_part == home or res_part in home or home in res_part)
    ):
        return h > a
    if res_part in ("2", "away") or (
        away and (res_part == away or res_part in away or away in res_part)
    ):
        return a > h
    if res_part in ("x", "draw"):
        return h == a
    return None


def evaluate_total(total_part: str, total_goals: int) -> bool | None:
    total_part = total_part.lower().strip()
    over_m = re.search(r"over\s*(\d+\.?\d*)", total_part)
    under_m = re.search(r"under\s*(\d+\.?\d*)", total_part)
    if over_m:
        return total_goals > float(over_m.group(1))
    if under_m:
        return total_goals < float(under_m.group(1))
    return None


def evaluate_btts(btts_part: str, h: int, a: int) -> bool | None:
    btts_part = btts_part.lower().strip()
    btts = h > 0 and a > 0
    if "yes" in btts_part or btts_part == "gg":
        return btts
    if "no" in btts_part or btts_part == "ng":
        return not btts
    return None


def evaluate_selection(
    category: str,
    selection: str,
    h1: int,
    a1: int,
    h2: int,
    a2: int,
    home_team: str | None = None,
    away_team: str | None = None,
) -> bool | None:
    """
    Given period scores (h1, a1) for 1st half and (h2, a2) for 2nd half,
    determines if a tracked selection won.
    Returns True/False, or None if it cannot be evaluated.
    """
    sel = selection.lower().strip()
    cat = category.lower().strip()

    # Cumulative full-time goals
    hg = h1 + h2
    ag = a1 + a2
    ft_total = hg + ag

    # 1st half goals
    ht_total = h1 + a1

    # 2nd half goals
    h2_total = h2 + a2

    # 1X2 & Total (Full-Time compound)
    if (
        "1x2" in cat
        and "total" in cat
        and "&" in sel
        and "1h" not in cat
        and "2h" not in cat
        and "1st half" not in cat
        and "2nd half" not in cat
        and "btts" not in cat
        and "both teams to score" not in cat
    ):
        parts = sel.split("&")
        if len(parts) == 2:
            p1, p2 = parts[0].strip(), parts[1].strip()
            res_win = evaluate_1x2(p1, hg, ag, home_team, away_team)
            total_win = evaluate_total(p2, ft_total)
            if res_win is not None and total_win is not None:
                return res_win and total_win

    # 1X2 / Match Result (guarded — must not contain &, total, btts, or double chance)
    if (
        ("1x2" in cat or "match result" in cat)
        and "1h" not in cat
        and "2h" not in cat
        and "1st half" not in cat
        and "2nd half" not in cat
        and "&" not in sel
    ):
        return evaluate_1x2(sel, hg, ag, home_team, away_team)

    # Correct Score (Match)
    if (
        "correct score" in cat
        and "1h" not in cat
        and "2h" not in cat
        and "1st half" not in cat
        and "2nd half" not in cat
        and "ht/ft" not in cat
        and "halftime/fulltime" not in cat
    ):
        m = re.search(r"(\d+)\s*[:\-]\s*(\d+)", sel)
        if m:
            return int(m.group(1)) == hg and int(m.group(2)) == ag

    # 1H Correct Score
    if "1h correct score" in cat or "1st half - correct score" in cat:
        m = re.search(r"(\d+)\s*[:\-]\s*(\d+)", sel)
        if m:
            return int(m.group(1)) == h1 and int(m.group(2)) == a1

    # 2H Correct Score
    if "2h correct score" in cat or "2nd half - correct score" in cat:
        m = re.search(r"(\d+)\s*[:\-]\s*(\d+)", sel)
        if m:
            return int(m.group(1)) == h2 and int(m.group(2)) == a2

    # Total Goals (Match)
    if (
        (
            ("total goals" in cat or "total" in cat)
            and "double chance" not in cat
            and "1x2" not in cat
            and "result" not in cat
            and "halftime/fulltime" not in cat
            and "ht/ft" not in cat
        )
        and "1h" not in cat
        and "2h" not in cat
        and "1st half" not in cat
        and "2nd half" not in cat
    ):
        # Check if selection contains '&' representing 1X2 & Total or Total Goals & BTTS
        if "&" in sel:
            parts = sel.split("&")
            if len(parts) == 2:
                p1, p2 = parts[0].strip(), parts[1].strip()
                # Total Goals & BTTS
                total_win1 = evaluate_total(p1, ft_total)
                btts_win2 = evaluate_btts(p2, hg, ag)
                if total_win1 is not None and btts_win2 is not None:
                    return total_win1 and btts_win2
                # 1X2 & Total
                res_win1 = evaluate_1x2(p1, hg, ag, home_team, away_team)
                total_win2 = evaluate_total(p2, ft_total)
                if res_win1 is not None and total_win2 is not None:
                    return res_win1 and total_win2
        else:
            return evaluate_total(sel, ft_total)

    # 1H Total Goals
    if "1h total goals" in cat or "1st half - total" in cat or "1st half - match total" in cat:
        if "&" in sel:
            parts = sel.split("&")
            if len(parts) == 2:
                p1, p2 = parts[0].strip(), parts[1].strip()
                # Total Goals & BTTS
                total_win1 = evaluate_total(p1, ht_total)
                btts_win2 = evaluate_btts(p2, h1, a1)
                if total_win1 is not None and btts_win2 is not None:
                    return total_win1 and btts_win2
                # 1X2 & Total
                res_win1 = evaluate_1x2(p1, h1, a1, home_team, away_team)
                total_win2 = evaluate_total(p2, ht_total)
                if res_win1 is not None and total_win2 is not None:
                    return res_win1 and total_win2
        else:
            return evaluate_total(sel, ht_total)

    # 2H Total Goals
    if "2h total goals" in cat or "2nd half - total" in cat or "2nd half - match total" in cat:
        if "&" in sel:
            parts = sel.split("&")
            if len(parts) == 2:
                p1, p2 = parts[0].strip(), parts[1].strip()
                # Total Goals & BTTS
                total_win1 = evaluate_total(p1, h2_total)
                btts_win2 = evaluate_btts(p2, h2, a2)
                if total_win1 is not None and btts_win2 is not None:
                    return total_win1 and btts_win2
                # 1X2 & Total
                res_win1 = evaluate_1x2(p1, h2, a2, home_team, away_team)
                total_win2 = evaluate_total(p2, h2_total)
                if res_win1 is not None and total_win2 is not None:
                    return res_win1 and total_win2
        else:
            return evaluate_total(sel, h2_total)

    # BTTS
    if (
        (
            ("btts" in cat or "both teams to score" in cat)
            and "double chance" not in cat
            and "1x2" not in cat
            and "draw" not in cat
            and "win" not in cat
        )
        and "1h" not in cat
        and "2h" not in cat
        and "1st half" not in cat
        and "2nd half" not in cat
    ):
        return evaluate_btts(sel, hg, ag)

    # 1H BTTS
    if "1h btts" in cat or "1st half - both teams to score" in cat:
        return evaluate_btts(sel, h1, a1)

    # 2H BTTS
    if "2h btts" in cat or "2nd half - both teams to score" in cat:
        return evaluate_btts(sel, h2, a2)

    # HT/FT Result / HT/FT & Total
    if "ht/ft" in cat or "halftime/fulltime" in cat:
        # Check for HT/FT Correct Score format: "0:1 0:2" (HT score, FT score)
        htft_cs = re.findall(r"(\d+)[:-](\d+)\s+(\d+)[:-](\d+)", sel)
        if htft_cs:
            h1_match, a1_match = int(htft_cs[0][0]), int(htft_cs[0][1])
            hf_match, af_match = int(htft_cs[0][2]), int(htft_cs[0][3])
            return h1_match == h1 and a1_match == a1 and hf_match == hg and af_match == ag
        sub_parts = sel.split("&")
        ht_ft_part = sub_parts[0].strip()
        parts = ht_ft_part.split("/")
        if len(parts) == 2:
            ht_won = evaluate_1x2(parts[0], h1, a1, home_team, away_team)
            ft_won = evaluate_1x2(parts[1], hg, ag, home_team, away_team)
            if ht_won is not None and ft_won is not None:
                if len(sub_parts) == 2:
                    extra_part = sub_parts[1].strip()
                    extra_win = evaluate_total(extra_part, ft_total)
                    if extra_win is None:
                        extra_win = evaluate_btts(extra_part, hg, ag)
                    if extra_win is not None:
                        return ht_won and ft_won and extra_win
                else:
                    return ht_won and ft_won

    # 1H 1x2 & Total / 2H 1x2 & Total
    if (
        ("1h" in cat or "1st half" in cat)
        and ("1x2" in cat or "match result" in cat)
        and "total" in cat
    ):
        parts = sel.split("&")
        if len(parts) == 2:
            p1, p2 = parts[0].strip(), parts[1].strip()
            res_win = evaluate_1x2(p1, h1, a1, home_team, away_team)
            total_win = evaluate_total(p2, ht_total)
            if res_win is not None and total_win is not None:
                return res_win and total_win
    if (
        ("2h" in cat or "2nd half" in cat)
        and ("1x2" in cat or "match result" in cat)
        and "total" in cat
    ):
        parts = sel.split("&")
        if len(parts) == 2:
            p1, p2 = parts[0].strip(), parts[1].strip()
            res_win = evaluate_1x2(p1, h2, a2, home_team, away_team)
            total_win = evaluate_total(p2, h2_total)
            if res_win is not None and total_win is not None:
                return res_win and total_win

    # Double Chance & Total
    if (
        "double chance & total" in cat
        and "1h" not in cat
        and "2h" not in cat
        and "1st half" not in cat
        and "2nd half" not in cat
    ):
        parts = sel.split("&")
        if len(parts) == 2:
            dc_win = evaluate_double_chance(parts[0], hg, ag, home_team, away_team)
            total_win = evaluate_total(parts[1], ft_total)
            if dc_win is not None and total_win is not None:
                return dc_win and total_win

    # Double Chance & BTTS
    if (
        "double chance & btts" in cat
        and "1h" not in cat
        and "2h" not in cat
        and "1st half" not in cat
        and "2nd half" not in cat
    ):
        parts = sel.split("&")
        if len(parts) == 2:
            dc_win = evaluate_double_chance(parts[0], hg, ag, home_team, away_team)
            btts_win = evaluate_btts(parts[1], hg, ag)
            if dc_win is not None and btts_win is not None:
                return dc_win and btts_win

    # Draw or BTTS
    if "draw or btts" in cat:
        btts = hg > 0 and ag > 0
        draw = hg == ag
        return btts or draw

    # Team Win or BTTS
    if "team win or btts" in cat:
        btts = hg > 0 and ag > 0
        win = hg != ag
        return btts or win

    # 1H Double Chance & BTTS
    if "1h double chance & btts" in cat or "1st half - double chance & both teams to score" in cat:
        parts = sel.split("&")
        if len(parts) == 2:
            dc_win = evaluate_double_chance(parts[0], h1, a1, home_team, away_team)
            btts_win = evaluate_btts(parts[1], h1, a1)
            if dc_win is not None and btts_win is not None:
                return dc_win and btts_win

    # 2H Double Chance & BTTS
    if "2h double chance & btts" in cat or "2nd half - double chance & both teams to score" in cat:
        parts = sel.split("&")
        if len(parts) == 2:
            dc_win = evaluate_double_chance(parts[0], h2, a2, home_team, away_team)
            btts_win = evaluate_btts(parts[1], h2, a2)
            if dc_win is not None and btts_win is not None:
                return dc_win and btts_win

    # 1H 1x2 & BTTS
    if "1h 1x2 & btts" in cat or "1st half - 1x2 & both teams to score" in cat:
        parts = sel.split("&")
        if len(parts) == 2:
            res_win = evaluate_1x2(parts[0], h1, a1, home_team, away_team)
            btts_win = evaluate_btts(parts[1], h1, a1)
            if res_win is not None and btts_win is not None:
                return res_win and btts_win

    # 2H 1x2 & BTTS
    if "2h 1x2 & btts" in cat or "2nd half - 1x2 & both teams to score" in cat:
        parts = sel.split("&")
        if len(parts) == 2:
            res_win = evaluate_1x2(parts[0], h2, a2, home_team, away_team)
            btts_win = evaluate_btts(parts[1], h2, a2)
            if res_win is not None and btts_win is not None:
                return res_win and btts_win

    # 1X2 & BTTS (Full-Time fallback)
    if (
        "1x2 & btts" in cat
        and "1h" not in cat
        and "2h" not in cat
        and "1st half" not in cat
        and "2nd half" not in cat
    ):
        parts = sel.split("&")
        if len(parts) == 2:
            res_win = evaluate_1x2(parts[0], hg, ag, home_team, away_team)
            btts_win = evaluate_btts(parts[1], hg, ag)
            if res_win is not None and btts_win is not None:
                return res_win and btts_win

    # Multiscores
    if "multiscores" in cat:
        if "draw" in sel:
            return hg == ag
        scores = re.findall(r"(\d+)\s*[:\-]\s*(\d+)", sel)
        if scores:
            return any(int(s[0]) == hg and int(s[1]) == ag for s in scores)

    return None


# ─── SofaScore Results Scraper ──────────────────────────────────────────────────


def clean_team_name(name: str) -> str:
    """Clean team name for fuzzy matching by removing common suffixes and accents."""
    name = name.lower()
    import unicodedata

    name = "".join(c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn")
    for word in [
        "fc",
        "cf",
        "united",
        "utd",
        "city",
        "town",
        "rovers",
        "athletic",
        "afc",
        "montevideo",
        "club",
    ]:
        name = name.replace(f" {word}", "").replace(f"{word} ", "")
    name = re.sub(r"[^a-z0-9\s]", "", name)
    return " ".join(name.split())


def check_name_match(t1: str, t2: str) -> bool:
    """Check if two team names are a match using substring and similarity ratio."""
    t1_c = clean_team_name(t1)
    t2_c = clean_team_name(t2)
    if not t1_c or not t2_c:
        return False
    if t1_c in t2_c or t2_c in t1_c:
        return True
    sim = difflib.SequenceMatcher(None, t1_c, t2_c).ratio()
    if sim > 0.65:
        return True
    # Word intersection subset check
    w1 = set(t1_c.split())
    w2 = set(t2_c.split())
    return bool(w1 and w2 and (w1.issubset(w2) or w2.issubset(w1)))


async def fetch_sofascore_json(page, url: str) -> dict | None:
    """Fetch URL within page context to leverage session cookies/headers and bypass Cloudflare."""
    try:
        response_json = await page.evaluate(f"""
            async () => {{
                const res = await fetch('{url}');
                if (!res.ok) throw new Error('HTTP ' + res.status);
                return await res.json();
            }}
        """)
        return response_json
    except Exception as e:
        print(f"[RESULTS] Error fetching {url}: {e}")
        return None


# ─── Main Resolver ─────────────────────────────────────────────────────────────


async def resolve_results(db):
    """
    Finds all unsettled matches, queries SofaScore's JSON endpoints to find
    the exact matching fixture, extracts final/period scores, and settles each bet.
    """
    unsettled = db.get_unsettled_matches()
    if not unsettled:
        print("[RESULTS] No unsettled bets found.")
        return 0

    print(f"[RESULTS] Resolving {len(unsettled)} unsettled match(es)...")
    settled_count = 0
    skip_count = 0
    total_pnl = 0.0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        if stealth_async:
            await stealth_async(page)

        # Open SofaScore session to set cookies/headers
        print("[RESULTS] Opening Sofascore session...")
        try:
            await page.goto(
                "https://www.sofascore.com/", wait_until="domcontentloaded", timeout=30000
            )
            await asyncio.sleep(3)
        except Exception as e:
            print(f"[RESULTS] Warning: SofaScore home page visit failed: {e}")

        for row in unsettled:
            match_id, home_team, away_team, _be_path, start_time = row
            result = await _resolve_one_match(db, page, match_id, home_team, away_team, start_time)
            if result is None:
                continue
            sc, sk, pnl = result
            settled_count += sc
            skip_count += sk
            total_pnl += pnl
            await asyncio.sleep(1)

        await browser.close()

    print(
        f"[RESULTS] Done — {settled_count} bets settled, {skip_count} skipped, P&L: ${total_pnl:+.2f}."
    )
    return {
        "settled": settled_count,
        "skipped": skip_count,
        "total_pnl": round(total_pnl, 2),
    }


async def _resolve_one_match(
    db, page, match_id: str, home_team: str, away_team: str, start_time: str | None
):
    """Resolve a single unsettled match: lookup → match → fetch → settle.

    Returns (settled_count, skip_count, total_pnl) or None if the match
    can't be resolved yet.
    """
    if not start_time:
        print(f"[RESULTS] Skipping {home_team} vs {away_team} — start_time is missing.")
        return None

    try:
        dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        if datetime.now(UTC) < dt + timedelta(hours=2.5):
            print(
                f"[RESULTS] Skipping {home_team} vs {away_team} — match has not finished yet (started at {start_time})"
            )
            return None
    except (ValueError, TypeError) as e:
        print(
            f"[RESULTS] Warning: Could not parse start_time '{start_time}' for {home_team} vs {away_team}: {e}"
        )
        return None

    print(f"[RESULTS] Looking up: {home_team} vs {away_team} (started {start_time})")

    match_data = await _find_match_on_sofascore(page, home_team, away_team, dt)
    if match_data is None:
        return None

    _, _, h1, a1, h2, a2, is_swapped = match_data

    if is_swapped:
        print("[RESULTS] Swapping home/away scores to match database ordering.")
        h1, a1 = a1, h1
        h2, a2 = a2, h2

    print(
        f"[RESULTS] Resolved score: {home_team} {h1 + h2} - {a1 + a2} {away_team} (HT {h1}:{a1}, 2H {h2}:{a2})"
    )

    return _settle_match_bets(db, match_id, h1, a1, h2, a2, home_team, away_team)


async def _find_match_on_sofascore(page, home_team, away_team, dt):
    """Look up a match on SofaScore by checking daily schedules, then search fallback.

    Returns (event_id, ev_detail, h1, a1, h2, a2, is_swapped) or None.
    """
    target_timestamp = int(dt.timestamp())
    utc_date_str = dt.strftime("%Y-%m-%d")
    dates_to_check = [
        utc_date_str,
        (dt - timedelta(days=1)).strftime("%Y-%m-%d"),
        (dt + timedelta(days=1)).strftime("%Y-%m-%d"),
    ]

    candidates = []
    events = []

    for date_str in dates_to_check:
        url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}"
        data = await fetch_sofascore_json(page, url)
        if data and "events" in data:
            events.extend(data["events"])
        await asyncio.sleep(0.5)

    for ev in events:
        ev_home = ev.get("homeTeam", {}).get("name", "")
        ev_away = ev.get("awayTeam", {}).get("name", "")
        ev_timestamp = ev.get("startTimestamp")
        if (
            (check_name_match(home_team, ev_home) and check_name_match(away_team, ev_away))
            or (check_name_match(home_team, ev_away) and check_name_match(away_team, ev_home))
        ) and ev_timestamp:
            time_diff = abs(ev_timestamp - target_timestamp)
            if time_diff <= 86400:
                candidates.append((ev, time_diff))

    if not candidates:
        print(
            "[RESULTS] Match not found in daily schedules, attempting SofaScore search fallback..."
        )
        import urllib.parse

        query = f"{home_team} {away_team}"
        search_url = f"https://api.sofascore.com/api/v1/search/all?q={urllib.parse.quote(query)}"
        search_data = await fetch_sofascore_json(page, search_url)
        search_events = []
        if search_data and "results" in search_data:
            for item in search_data["results"]:
                if item.get("type") == "event" and "entity" in item:
                    search_events.append(item["entity"])
        for ev in search_events:
            ev_home = ev.get("homeTeam", {}).get("name", "")
            ev_away = ev.get("awayTeam", {}).get("name", "")
            ev_timestamp = ev.get("startTimestamp")
            if (
                (check_name_match(home_team, ev_home) and check_name_match(away_team, ev_away))
                or (check_name_match(home_team, ev_away) and check_name_match(away_team, ev_home))
            ) and ev_timestamp:
                time_diff = abs(ev_timestamp - target_timestamp)
                if time_diff <= 86400:
                    candidates.append((ev, time_diff))

    if not candidates:
        print(
            f"[RESULTS] WARNING: No SofaScore match candidate found for {home_team} vs {away_team}."
        )
        return None

    candidates.sort(key=lambda x: x[1])
    best_event = candidates[0][0]
    event_id = best_event.get("id")

    detail_url = f"https://api.sofascore.com/api/v1/event/{event_id}"
    detail_data = await fetch_sofascore_json(page, detail_url)
    if not detail_data or "event" not in detail_data:
        print(f"[RESULTS] Failed to fetch details for event ID {event_id}.")
        return None

    ev_detail = detail_data["event"]
    status = ev_detail.get("status", {})
    status_type = status.get("type")
    is_finished = (status_type == "finished") or (status.get("code") == 100)

    if not is_finished:
        print(
            f"[RESULTS] Match is not finished yet. Status: {status_type} ({status.get('description', '')})"
        )
        return None

    home_score = ev_detail.get("homeScore", {})
    away_score = ev_detail.get("awayScore", {})

    h1 = home_score.get("period1")
    a1 = away_score.get("period1")
    h2 = home_score.get("period2")
    a2 = away_score.get("period2")

    if h1 is None or a1 is None or h2 is None or a2 is None:
        ft_h = home_score.get("current")
        ft_a = away_score.get("current")
        if ft_h == 0 and ft_a == 0:
            h1, a1, h2, a2 = 0, 0, 0, 0
        else:
            print(
                f"[RESULTS] Missing period scores for non-zero result. HomeScore: {home_score}, AwayScore: {away_score}"
            )
            return None

    is_swapped = check_name_match(home_team, ev_detail.get("awayTeam", {}).get("name", ""))
    return event_id, ev_detail, h1, a1, h2, a2, is_swapped


def _settle_match_bets(db, match_id, h1, a1, h2, a2, home_team, away_team):
    """Settle all unsettled bets for a single match given the resolved scores.

    Returns (settled_count, skip_count, total_pnl).
    """
    settled_count = 0
    skip_count = 0
    total_pnl = 0.0

    bets = db.get_unsettled_bets_for_match(match_id)
    for bet in bets:
        bet_id, category, selection, odds, stake = bet
        won = evaluate_selection(category, selection, h1, a1, h2, a2, home_team, away_team)

        if won is None:
            skip_count += 1
            print(f"  [SKIP] Category: '{category}', Selection: '{selection}' (unevaluable market)")
            continue

        db.settle_bet(bet_id, is_win=won, odds=odds, stake=stake)
        settled_count += 1
        profit = (odds - 1) * stake if won else -stake
        total_pnl += profit
        status_str = "WON" if won else "LOST"
        print(
            f"  [SETTLED] {category} -> {selection}: {status_str} (Odds: {odds}, Stake: {stake}, P&L: ${profit:+.2f})"
        )

    return settled_count, skip_count, total_pnl
