
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Use a browser with a real user agent to minimize detection
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print("Navigating to livescore.com...")
            # Wait until network is idle to ensure JS has rendered content
            await page.goto("https://www.livescore.com", timeout=60000, wait_until="networkidle")

            # Save home page screenshot and HTML
            await page.screenshot(path="livescore_home.png")
            home_content = await page.content()
            with open("livescore_home.html", "w", encoding="utf-8") as f:
                f.write(home_content)
            print("Captured home page.")

            # Try to find a match link
            # Look for <a> tags containing '/match/'
            links = await page.query_selector_all("a")
            match_links = []
            for link in links:
                href = await link.get_attribute("href")
                if href and "/match/" in href:
                    match_links.append(href)

            if match_links:
                # Take the first available match link
                match_url = match_links[0]
                if not match_url.startswith("http"):
                    match_url = "https://www.livescore.com" + match_url

                print(f"Found match link: {match_url}. Navigating...")
                await page.goto(match_url, timeout=60000, wait_until="networkidle")

                # Save match page screenshot and HTML
                await page.screenshot(path="livescore_match.png")
                match_content = await page.content()
                with open("livescore_match.html", "w", encoding="utf-8") as f:
                    f.write(match_content)
                print("Captured match page.")
            else:
                print("No match links found on the home page.")

        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="livescore_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
