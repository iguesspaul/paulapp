import asyncio
import difflib
from playwright.async_api import async_playwright
try:
    from playwright_stealth import stealth_async
except ImportError:
    stealth_async = None

async def find_match_url(page, pin_path, team_a, team_b):
    """
    Finds a Pinnacle match URL by browsing the league matchups page.
    """
    search_url = f"https://www.pinnacle.com/en/soccer/{pin_path}/matchups/"
    
    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(5)
        
        links = await page.evaluate(f'''() => {{
            return Array.from(document.querySelectorAll('a'))
                .filter(a => a.href.includes('/soccer/{pin_path}/') && !a.href.endsWith('/matchups/'))
                .map(a => ({{href: a.href, text: a.innerText.replace(/\\n/g, ' ')}}));
        }}''')
        
        if not links:
            print(f"[PINNACLE] No links found on {search_url}")
            return None
            
        # simple match
        team_a_clean = "".join(c for c in team_a.lower() if c.isalnum())
        team_b_clean = "".join(c for c in team_b.lower() if c.isalnum())
        
        for l in links:
            l_text = "".join(c for c in l['text'].lower() if c.isalnum())
            l_href = l['href'].lower()
            if (team_a_clean in l_text or team_a_clean in l_href) and (team_b_clean in l_text or team_b_clean in l_href):
                return l['href']
        
        # Fallback to single match
        for l in links:
            l_text = "".join(c for c in l['text'].lower() if c.isalnum())
            l_href = l['href'].lower()
            if team_a_clean in l_text or team_a_clean in l_href or team_b_clean in l_text or team_b_clean in l_href:
                return l['href']
                
        return None
    except Exception as e:
        print(f"[PINNACLE] Match discovery failed: {e}")
        return None

async def harvest(pin_path, team_a, team_b):
    """
    Directly scrapes Pinnacle.com for sharp odds.
    """
    results = {"book": "Pinnacle Direct", "odds": {}}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        if stealth_async:
            await stealth_async(page)
            
        try:
            # 1. Discover Match URL
            match_url = await find_match_url(page, pin_path, team_a, team_b)
            if not match_url:
                # Fallback: Try a direct guess if search fails
                print(f"[PINNACLE] No URL found for {team_a} vs {team_b}")
                return results

            print(f"[PINNACLE] Scraping: {match_url}")
            await page.goto(match_url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(5)
            
            # Extract 1x2 and O/U from the Pinnacle DOM
            # Pinnacle uses complex classes, so we search by text and relative positioning
            data = await page.evaluate('''() => {
                const res = {};
                const buttons = Array.from(document.querySelectorAll('button'));
                
                // Helper to find odds near labels
                const findOdd = (label) => {
                    const btn = buttons.find(b => b.innerText.includes(label));
                    return btn ? parseFloat(btn.innerText.replace(/[^0-9.]/g, '')) : null;
                };

                // Logic to find 1x2 and O/U 2.5
                // Note: This is highly dependent on Pinnacle's current UI
                // We'll look for standard decimal formats
                const odds = Array.from(document.querySelectorAll('span'))
                    .map(s => s.innerText)
                    .filter(t => /^[0-9]\.[0-9]{2,3}$/.test(t))
                    .map(t => parseFloat(t));

                if (odds.length >= 5) {
                    res['1'] = odds[0];
                    res['X'] = odds[1];
                    res['2'] = odds[2];
                    res['Over2.5'] = odds[3];
                    res['Under2.5'] = odds[4];
                }
                return res;
            }''')
            
            if data:
                results['odds'] = data
                print(f"[PINNACLE] Successfully extracted: {data}")

        except Exception as e:
            print(f"[PINNACLE] Harvest error: {e}")
        finally:
            await browser.close()
            
    return results
