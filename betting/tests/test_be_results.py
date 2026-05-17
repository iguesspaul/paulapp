import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://www.betexplorer.com/soccer/england/premier-league/results/")
        await asyncio.sleep(4)
        
        matches = await page.evaluate('''() => {
            const rows = Array.from(document.querySelectorAll("tr"));
            return rows.map(row => {
                const nameEl  = row.querySelector("td.table-main__tt, td[class*='name']");
                const scoreEl = row.querySelector("td.table-main__result, td[class*='result']");
                if (!nameEl || !scoreEl) return null;
                return { name: nameEl.innerText.trim(), score: scoreEl.innerText.trim() };
            }).filter(Boolean);
        }''')
        
        print(f"Total matches found on results page: {len(matches)}")
        for m in matches[:15]:
            print(f"  Match: {m['name']} | Score: {m['score']}")
            
        await browser.close()

asyncio.run(main())
