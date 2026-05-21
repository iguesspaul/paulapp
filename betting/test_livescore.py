
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        print("Navigating to LiveScore...")
        try:
            await page.goto("https://www.livescore.com/en/", wait_until="networkidle")

            # Find a match link. Match links usually have a specific pattern.
            # We'll look for elements that look like match links.
            # Often they are anchors with href containing /football/match/
            match_link_selector = 'a[href*="/football/match/"]'
            await page.wait_for_selector(match_link_selector, timeout=10000)

            match_links = await page.query_selector_all(match_link_selector)
            if not match_links:
                print("No match links found.")
                await browser.close()
                return

            # Click the first match
            first_match = match_links[0]
            url = await first_match.get_attribute("href")
            full_url = f"https://www.livescore.com{url}" if url.startswith('/') else url
            print(f"Navigating to match: {full_url}")

            await page.goto(full_url, wait_until="networkidle")

            # Now we want to find the goal events.
            # We'll dump the HTML of the body to analyze it.
            content = await page.content()
            with open("livescore_dump.html", "w", encoding="utf-8") as f:
                f.write(content)

            print("HTML dumped to livescore_dump.html. Analyze this to find selectors.")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
