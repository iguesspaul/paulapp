"""
results_checker.py — Automatically fetches final scores and period scores from BetExplorer Match Pages
and settles all unsettled bets in simulated_bets.

Called automatically from run_session.py before each new scan.
"""
import asyncio
import re
import difflib
from typing import Optional
from playwright.async_api import async_playwright
try:
    from playwright_stealth import stealth_async
except ImportError:
    stealth_async = None


# ─── Score Evaluators ──────────────────────────────────────────────────────────

def evaluate_selection(category: str, selection: str, h1: int, a1: int, h2: int, a2: int) -> Optional[bool]:
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

    # 1X2 / Match Result
    if "1x2" in cat or "match result" in cat:
        if "1h" not in cat and "2h" not in cat and "1st half" not in cat and "2nd half" not in cat:
            if sel in ("1", "home") or sel.endswith("(home)"): return hg > ag
            if sel in ("x", "draw"):                           return hg == ag
            if sel in ("2", "away") or sel.endswith("(away)"): return ag > hg

    # Correct Score (Match)
    if "correct score" in cat and "1h" not in cat and "2h" not in cat and "1st half" not in cat and "2nd half" not in cat and "ht/ft" not in cat and "halftime/fulltime" not in cat:
        m = re.search(r'(\d+)\s*[:\-]\s*(\d+)', sel)
        if m:
            return int(m.group(1)) == hg and int(m.group(2)) == ag

    # 1H Correct Score
    if "1h correct score" in cat or "1st half - correct score" in cat:
        m = re.search(r'(\d+)\s*[:\-]\s*(\d+)', sel)
        if m:
            return int(m.group(1)) == h1 and int(m.group(2)) == a1

    # 2H Correct Score
    if "2h correct score" in cat or "2nd half - correct score" in cat:
        m = re.search(r'(\d+)\s*[:\-]\s*(\d+)', sel)
        if m:
            return int(m.group(1)) == h2 and int(m.group(2)) == a2

    # Total Goals (Match)
    if ("total goals" in cat or "total" in cat) and "double chance" not in cat and "1x2" not in cat and "result" not in cat and "halftime/fulltime" not in cat and "ht/ft" not in cat:
        if "1h" not in cat and "2h" not in cat and "1st half" not in cat and "2nd half" not in cat:
            over_m = re.search(r'over\s*(\d+\.?\d*)', sel)
            under_m = re.search(r'under\s*(\d+\.?\d*)', sel)
            if over_m:  return ft_total > float(over_m.group(1))
            if under_m: return ft_total < float(under_m.group(1))

    # 1H Total Goals
    if "1h total goals" in cat or "1st half - total" in cat or "1st half - match total" in cat:
        over_m = re.search(r'over\s*(\d+\.?\d*)', sel)
        under_m = re.search(r'under\s*(\d+\.?\d*)', sel)
        if over_m:  return ht_total > float(over_m.group(1))
        if under_m: return ht_total < float(under_m.group(1))

    # 2H Total Goals
    if "2h total goals" in cat or "2nd half - total" in cat or "2nd half - match total" in cat:
        over_m = re.search(r'over\s*(\d+\.?\d*)', sel)
        under_m = re.search(r'under\s*(\d+\.?\d*)', sel)
        if over_m:  return h2_total > float(over_m.group(1))
        if under_m: return h2_total < float(under_m.group(1))

    # BTTS
    if ("btts" in cat or "both teams to score" in cat) and "double chance" not in cat and "1x2" not in cat and "draw" not in cat and "win" not in cat:
        if "1h" not in cat and "2h" not in cat and "1st half" not in cat and "2nd half" not in cat:
            btts = hg > 0 and ag > 0
            if "yes" in sel: return btts
            if "no" in sel:  return not btts

    # 1H BTTS
    if "1h btts" in cat or "1st half - both teams to score" in cat:
        btts = h1 > 0 and a1 > 0
        if "yes" in sel: return btts
        if "no" in sel:  return not btts

    # 2H BTTS
    if "2h btts" in cat or "2nd half - both teams to score" in cat:
        btts = h2 > 0 and a2 > 0
        if "yes" in sel: return btts
        if "no" in sel:  return not btts

    # HT/FT Result
    if "ht/ft result" in cat or "halftime/fulltime" in cat:
        ht_res = "home" if h1 > a1 else ("draw" if h1 == a1 else "away")
        ft_res = "home" if hg > ag else ("draw" if hg == ag else "away")
        parts = sel.split('/')
        if len(parts) == 2:
            return parts[0].strip() == ht_res and parts[1].strip() == ft_res

    # HT/FT Correct Score
    if "ht/ft correct score" in cat or "halftime/fulltime correct score" in cat:
        scores = sel.split()
        if len(scores) == 2:
            ht_score_match = re.search(r'(\d+)\s*[:\-]\s*(\d+)', scores[0])
            ft_score_match = re.search(r'(\d+)\s*[:\-]\s*(\d+)', scores[1])
            if ht_score_match and ft_score_match:
                return (int(ht_score_match.group(1)) == h1 and int(ht_score_match.group(2)) == a1 and
                        int(ft_score_match.group(1)) == hg and int(ft_score_match.group(2)) == ag)

    # Double Chance & Total
    if "double chance & total" in cat and "1h" not in cat and "2h" not in cat and "1st half" not in cat and "2nd half" not in cat:
        parts = sel.split('&')
        if len(parts) == 2:
            dc_part = parts[0].strip()
            total_part = parts[1].strip()
            
            dc_win = False
            if "1x" in dc_part or "home/x" in dc_part or "home or draw" in dc_part or "/" in dc_part and "2" not in dc_part:
                dc_win = hg >= ag
            elif "x2" in dc_part or "x/away" in dc_part or "draw or away" in dc_part or "/" in dc_part and "1" not in dc_part:
                dc_win = ag >= hg
            elif "12" in dc_part or "home/away" in dc_part or "home or away" in dc_part:
                dc_win = hg != ag
                
            over_m = re.search(r'over\s*(\d+\.?\d*)', total_part)
            under_m = re.search(r'under\s*(\d+\.?\d*)', total_part)
            total_win = False
            if over_m:    total_win = ft_total > float(over_m.group(1))
            elif under_m: total_win = ft_total < float(under_m.group(1))
            
            return dc_win and total_win

    # Double Chance & BTTS
    if "double chance & btts" in cat and "1h" not in cat and "2h" not in cat and "1st half" not in cat and "2nd half" not in cat:
        parts = sel.split('&')
        if len(parts) == 2:
            dc_part = parts[0].strip()
            btts_part = parts[1].strip()
            
            dc_win = False
            if "1x" in dc_part or "home/x" in dc_part or "/" in dc_part and "2" not in dc_part:
                dc_win = hg >= ag
            elif "x2" in dc_part or "x/away" in dc_part or "/" in dc_part and "1" not in dc_part:
                dc_win = ag >= hg
            elif "12" in dc_part or "home/away" in dc_part:
                dc_win = hg != ag
                
            btts = hg > 0 and ag > 0
            btts_win = ("yes" in btts_part) == btts
            
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
        parts = sel.split('&')
        if len(parts) == 2:
            dc_part = parts[0].strip()
            btts_part = parts[1].strip()
            
            dc_win = False
            if "1x" in dc_part or "home/x" in dc_part or "/" in dc_part and "2" not in dc_part:
                dc_win = h1 >= a1
            elif "x2" in dc_part or "x/away" in dc_part or "/" in dc_part and "1" not in dc_part:
                dc_win = a1 >= h1
            elif "12" in dc_part or "home/away" in dc_part:
                dc_win = h1 != a1
                
            btts = h1 > 0 and a1 > 0
            btts_win = ("yes" in btts_part) == btts
            return dc_win and btts_win

    # 2H Double Chance & BTTS
    if "2h double chance & btts" in cat or "2nd half - double chance & both teams to score" in cat:
        parts = sel.split('&')
        if len(parts) == 2:
            dc_part = parts[0].strip()
            btts_part = parts[1].strip()
            
            dc_win = False
            if "1x" in dc_part or "home/x" in dc_part or "/" in dc_part and "2" not in dc_part:
                dc_win = h2 >= a2
            elif "x2" in dc_part or "x/away" in dc_part or "/" in dc_part and "1" not in dc_part:
                dc_win = a2 >= h2
            elif "12" in dc_part or "home/away" in dc_part:
                dc_win = h2 != a2
                
            btts = h2 > 0 and a2 > 0
            btts_win = ("yes" in btts_part) == btts
            return dc_win and btts_win

    # 1H 1x2 & BTTS
    if "1h 1x2 & btts" in cat or "1st half - 1x2 & both teams to score" in cat:
        parts = sel.split('&')
        if len(parts) == 2:
            res_part = parts[0].strip()
            btts_part = parts[1].strip()
            
            res_win = False
            if "home" in res_part or "1" in res_part or "/" in res_part and "2" not in res_part:
                res_win = h1 > a1
            elif "away" in res_part or "2" in res_part or "/" in res_part and "1" not in res_part:
                res_win = a1 > h1
            elif "draw" in res_part or "x" in res_part:
                res_win = h1 == a1
                
            btts = h1 > 0 and a1 > 0
            btts_win = ("yes" in btts_part) == btts
            return res_win and btts_win

    # 2H 1x2 & BTTS
    if "2h 1x2 & btts" in cat or "2nd half - 1x2 & both teams to score" in cat:
        parts = sel.split('&')
        if len(parts) == 2:
            res_part = parts[0].strip()
            btts_part = parts[1].strip()
            
            res_win = False
            if "home" in res_part or "1" in res_part or "/" in res_part and "2" not in res_part:
                res_win = h2 > a2
            elif "away" in res_part or "2" in res_part or "/" in res_part and "1" not in res_part:
                res_win = a2 > h2
            elif "draw" in res_part or "x" in res_part:
                res_win = h2 == a2
                
            btts = h2 > 0 and a2 > 0
            btts_win = ("yes" in btts_part) == btts
            return res_win and btts_win

    # Multiscores
    if "multiscores" in cat:
        if "draw" in sel:
            return hg == ag
        scores = re.findall(r'(\d+)\s*[:\-]\s*(\d+)', sel)
        if scores:
            return any(int(s[0]) == hg and int(s[1]) == ag for s in scores)

    return None


# ─── BetExplorer Results Scraper ───────────────────────────────────────────────

async def find_match_page_url(page, be_path: str, home_team: str, away_team: str) -> Optional[str]:
    """
    Looks for the match on both the main league page and the results page
    to find its match detail page URL.
    """
    urls_to_check = [
        f"https://www.betexplorer.com/{be_path}/",
        f"https://www.betexplorer.com/{be_path}/results/"
    ]
    
    # Pre-clean team names for better matching
    home_clean = home_team.lower().strip()
    away_clean = away_team.lower().strip()
    
    for url in urls_to_check:
        try:
            print(f"[RESULTS] Searching for match link on: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            
            # Find all links that look like matches
            matches = await page.evaluate('''() => {
                const rows = Array.from(document.querySelectorAll("tr"));
                return rows.map(row => {
                    const nameEl = row.querySelector("td.h-text-left, td.table-main__tt, td[class*='name']");
                    if (!nameEl) return null;
                    const a = nameEl.querySelector("a");
                    if (!a) return null;
                    return {
                        name: nameEl.innerText.trim(),
                        href: a.getAttribute("href")
                    };
                }).filter(Boolean);
            }''')
            
            # Find matching match
            for m in matches:
                name_low = m['name'].lower()
                href = m['href']
                
                # Ignore team page links
                if "/team/" in href:
                    continue
                
                # Check for direct inclusion of both teams
                if home_clean in name_low and away_clean in name_low:
                    return f"https://www.betexplorer.com{href}"
                    
                # Strict word-based checking to handle abbreviations / suffixes
                home_words = [w for w in home_clean.replace("fc", "").replace("cf", "").replace("ud", "").split() if len(w) > 2]
                away_words = [w for w in away_clean.replace("fc", "").replace("cf", "").replace("ud", "").split() if len(w) > 2]
                
                if not home_words: home_words = [home_clean]
                if not away_words: away_words = [away_clean]
                
                home_matched = False
                for w in home_words:
                    if w in name_low or (w == "united" and "utd" in name_low) or (w == "utd" and "united" in name_low):
                        home_matched = True
                        break
                        
                away_matched = False
                for w in away_words:
                    if w in name_low or (w == "united" and "utd" in name_low) or (w == "utd" and "united" in name_low):
                        away_matched = True
                        break
                        
                if home_matched and away_matched:
                    return f"https://www.betexplorer.com{href}"
                    
        except Exception as e:
            print(f"[RESULTS] Error searching page {url}: {e}")
            
    return None


async def fetch_score_and_partial_from_match_page(page, match_url: str):
    """
    Navigates to the match page and extracts the final score and partial period scores.
    """
    try:
        print(f"[RESULTS] Scraping match details from: {match_url}")
        await page.goto(match_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        
        info = await page.evaluate('''() => {
            const scoreEl = document.querySelector('#js-score');
            const partialEl = document.querySelector('#js-partial');
            const isFinishedEl = document.querySelector('#isFinished');
            
            return {
                score: scoreEl ? scoreEl.innerText.trim() : null,
                partial: partialEl ? partialEl.innerText.trim() : null,
                isFinished: isFinishedEl ? isFinishedEl.value : null
            };
        }''')
        
        # Verify it is finished
        if info['isFinished'] == "1" or (info['score'] and ":" in info['score'] and not info['isFinished']):
            return info['score'], info['partial']
            
    except Exception as e:
        print(f"[RESULTS] Error scraping match page {match_url}: {e}")
        
    return None, None


def parse_period_scores(score_str, partial_str):
    """
    Parses score_str (e.g., "3:2") and partial_str (e.g., "(1:0, 2:2)")
    Returns (h1, a1, h2, a2) or None if parsing fails.
    """
    try:
        # Default fallback from score if partial is missing
        score_m = re.search(r'(\d+)\s*[:\-]\s*(\d+)', score_str)
        if not score_m:
            return None
        ft_h, ft_a = int(score_m.group(1)), int(score_m.group(2))
        
        if partial_str:
            # Parse "(1:0, 2:2)"
            m = re.search(r'\(\s*(\d+)\s*[:\-]\s*(\d+)\s*,\s*(\d+)\s*[:\-]\s*(\d+)\s*\)', partial_str)
            if m:
                return int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            
            # Sometimes it's just one half if abandoned, or formatted differently, e.g., "(1:0)"
            m_single = re.search(r'\(\s*(\d+)\s*[:\-]\s*(\d+)\s*\)', partial_str)
            if m_single:
                h1, a1 = int(m_single.group(1)), int(m_single.group(2))
                return h1, a1, ft_h - h1, ft_a - a1
                
        # If no partial was provided/found, but we have 0-0, we know h1=0, a1=0, h2=0, a2=0
        if ft_h == 0 and ft_a == 0:
            return 0, 0, 0, 0
            
    except Exception as e:
        print(f"[RESULTS] Error parsing scores: {e}")
        
    return None


# ─── Main Resolver ─────────────────────────────────────────────────────────────

async def resolve_results(db):
    """
    Finds all unsettled matches, scrapes their results, and settles each bet.
    """
    unsettled = db.get_unsettled_matches()
    if not unsettled:
        print("[RESULTS] No unsettled bets found.")
        return 0

    print(f"[RESULTS] Resolving {len(unsettled)} unsettled match(es)...")
    settled_count = 0
    skip_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        if stealth_async:
            await stealth_async(page)

        for row in unsettled:
            match_id, home_team, away_team, be_path = row

            if not be_path or not home_team or not away_team:
                continue

            print(f"[RESULTS] Looking up: {home_team} vs {away_team} ({be_path})")
            
            # Step 1: Find match page url
            match_url = await find_match_page_url(page, be_path, home_team, away_team)
            if not match_url:
                print(f"[RESULTS] Match URL not found — match may be postponed or name mismatch.")
                continue
                
            # Step 2: Fetch score and partial
            score_str, partial_str = await fetch_score_and_partial_from_match_page(page, match_url)
            if not score_str:
                print(f"[RESULTS] No score found yet — match may not have finished.")
                continue
                
            # Step 3: Parse period scores
            parsed = parse_period_scores(score_str, partial_str)
            if not parsed:
                print(f"[RESULTS] Failed to parse scores: Score={score_str}, Partial={partial_str}")
                continue
                
            h1, a1, h2, a2 = parsed
            print(f"[RESULTS] Final score: {home_team} {h1+h2} – {a1+a2} {away_team} (HT {h1}:{a1}, 2H {h2}:{a2})")

            # Step 4: Settle all unsettled bets for this match
            bets = db.get_unsettled_bets_for_match(match_id)
            for bet in bets:
                bet_id, category, selection, odds, stake = bet
                won = evaluate_selection(category, selection, h1, a1, h2, a2)

                if won is None:
                    skip_count += 1
                    print(f"  [SKIP] Category: '{category}', Selection: '{selection}' (unevaluable market)")
                    continue

                db.settle_bet(bet_id, is_win=won, odds=odds, stake=stake)
                settled_count += 1
                status = "WON" if won else "LOST"
                print(f"  [SETTLED] {category} -> {selection}: {status} (Odds: {odds}, Stake: {stake})")

            await asyncio.sleep(1)  # polite delay between requests

        await browser.close()

    print(f"[RESULTS] Done — {settled_count} bets settled, {skip_count} skipped.")
    return settled_count
