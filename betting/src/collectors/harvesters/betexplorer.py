import asyncio
import json
import os
import difflib
import re
from playwright.async_api import async_playwright
try:
    from playwright_stealth import stealth_async
except ImportError:
    stealth_async = None

async def find_match_url(page, be_path, team_a, team_b):
    """
    Intelligently finds the match URL on BetExplorer for a given league and team pair.
    """
    league_url = f"https://www.betexplorer.com/{be_path}/"
    print(f"[HARVESTER] Discovering match on: {league_url}")
    
    try:
        await page.goto(league_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        
        # Get all links that look like match links
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a'))
                .map(a => ({ text: a.innerText, href: a.href }))
                .filter(a => a.href.includes('/') && a.text.includes(' - '));
        }''')
        
        # Search for the best match
        target = f"{team_a} - {team_b}".lower()
        best_match = None
        highest_score = 0
        
        for link in links:
            link_text = link['text'].lower()
            # Simple fuzzy matching score
            score = difflib.SequenceMatcher(None, target, link_text).ratio()
            # Also check for individual team names
            if team_a.lower() in link_text or team_b.lower() in link_text:
                score += 0.3
            
            if score > highest_score and score > 0.6:
                highest_score = score
                best_match = link['href']
                
        return best_match
    except Exception as e:
        print(f"[HARVESTER] URL discovery failed: {e}")
        return None

async def harvest_sharp_odds(be_path, team_a, team_b):
    """
    Discovers and harvests Pinnacle and Bet365 odds from BetExplorer.
    """
    target_books = ["Pinnacle", "bet365", "SBOBET", "188BET", "Betfair"]
    results = [{"book": b, "odds": {}} for b in target_books]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        if stealth_async:
            await stealth_async(page)
            
        try:
            # 1. Discover the match URL
            match_url = await find_match_url(page, be_path, team_a, team_b)
            if not match_url:
                print(f"[HARVESTER] Could not find match URL for {team_a} vs {team_b}")
                return results # Return empty but valid structure
            
            print(f"[HARVESTER] Scraping match page: {match_url}")
            await page.goto(match_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            
            # Extract 1x2 odds
            data = await page.evaluate('''(books) => {
                const res = {};
                books.forEach(b => res[b] = {});
                const rows = Array.from(document.querySelectorAll('tr'));
                
                rows.forEach(row => {
                    const text = row.innerText.toLowerCase();
                    const bookMatch = books.find(b => text.includes(b.toLowerCase()));
                    if (bookMatch) {
                        const oddsCells = Array.from(row.querySelectorAll('td')).filter(c => c.getAttribute('data-odd') || c.innerText.match(/^[0-9.]+$/));
                        
                        if (oddsCells.length >= 3) {
                            res[bookMatch]['1'] = parseFloat(oddsCells[0].innerText) || parseFloat(oddsCells[0].getAttribute('data-odd'));
                            res[bookMatch]['X'] = parseFloat(oddsCells[1].innerText) || parseFloat(oddsCells[1].getAttribute('data-odd'));
                            res[bookMatch]['2'] = parseFloat(oddsCells[2].innerText) || parseFloat(oddsCells[2].getAttribute('data-odd'));
                        }
                    }
                });
                return res;
            }''', target_books)
            
            # Extract O/U 2.5 odds
            try:
                await page.evaluate('''() => {
                    const tabs = Array.from(document.querySelectorAll('a'));
                    const ouTab = tabs.find(a => a.innerText.includes('O/U'));
                    if (ouTab) ouTab.click();
                }''')
                await asyncio.sleep(2)
                
                ou_data = await page.evaluate('''(books) => {
                    const ou_res = {};
                    books.forEach(b => ou_res[b] = {});
                    const rows = Array.from(document.querySelectorAll('tr'));
                    
                    rows.forEach(row => {
                        const text = row.innerText.toLowerCase();
                        const bookMatch = books.find(b => text.includes(b.toLowerCase()));
                        
                        if (bookMatch) {
                            const cells = Array.from(row.querySelectorAll('td'));
                            // Specifically ensure this row is for the '2.5' line
                            const isLine25 = cells.some(c => c.innerText.trim() === '2.5');
                            
                            if (isLine25) {
                                // Only select cells with the 'data-odd' attribute to get exact odds
                                const oddsCells = cells.filter(c => c.getAttribute('data-odd'));
                                if (oddsCells.length >= 2) {
                                    ou_res[bookMatch]['Over'] = parseFloat(oddsCells[0].getAttribute('data-odd')) || parseFloat(oddsCells[0].innerText);
                                    ou_res[bookMatch]['Under'] = parseFloat(oddsCells[1].getAttribute('data-odd')) || parseFloat(oddsCells[1].innerText);
                                }
                            }
                        }
                    });
                    return ou_res;
                }''', target_books)
                
                for book in target_books:
                    if 'Over' in ou_data[book]: data[book]['Over2.5'] = ou_data[book]['Over']
                    if 'Under' in ou_data[book]: data[book]['Under2.5'] = ou_data[book]['Under']
            except: pass

            # Format results
            for i, bname in enumerate(target_books):
                ext = data.get(bname, {})
                for k in ['1', 'X', '2', 'Over2.5', 'Under2.5']:
                    if k in ext: results[i]['odds'][k] = ext[k]

        except Exception as e:
            print(f"[HARVESTER] Scraper error: {e}")
        finally:
            await browser.close()
            
    return results
