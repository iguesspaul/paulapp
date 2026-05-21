import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a common user agent to avoid detection
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        url = "https://www.betexplorer.com/soccer/spain/laliga/13365468/"
        print(f"Loading {url}...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5) # Give it some time to render
            
            links = await page.query_selector_all("a")
            print(f"\nFound {len(links)} links on page:")
            for link in links:
                text = await link.inner_text()
                href = await link.get_attribute("href")
                if text and text.strip():
                    print(f"{text.strip()} -> {href}")
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

asyncio.run(main())
