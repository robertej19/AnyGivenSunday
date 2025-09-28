import asyncio
import os
from playwright.async_api import async_playwright

AUTH_STATE_FILE = "auth_state.json"

async def scrape_standings(page):
    # React Virtualized only renders visible rows — scroll to collect all
    rows_locator = page.locator('.ReactVirtualized__Table__row.ContestStandings_row')
    
    seen_users = set()
    standings_data = []
    previous_results_count = -1

    print("Scraping standings... This may take a moment as we scroll through all entries.")

    while True:
        current_rows_count = await rows_locator.count()
        for i in range(current_rows_count):
            row = rows_locator.nth(i)
            
            # Use a more reliable way to get the username from the aria-label
            aria_label = await row.get_attribute('aria-label')
            if not aria_label or "view standings for" not in aria_label:
                continue
                
            username = aria_label.replace("view standings for ", "").strip()
            
            if username not in seen_users:
                seen_users.add(username)
                
                rank_text = await row.locator('.ContestStandings_rank-cell').inner_text()
                points_text = await row.locator('.ContestStandings_fantasy-points-cell').inner_text()

                standings_data.append({
                    "username": username,
                    "rank": int(rank_text.strip()),
                    "points": float(points_text.strip())
                })

        # If the number of results hasn't changed after scrolling, we're done
        if len(standings_data) == previous_results_count:
            break
        
        previous_results_count = len(standings_data)

        # Scroll the last visible row into view to load more
        await rows_locator.last.scroll_into_view_if_needed()
        # Add a small delay to allow new rows to render
        await page.wait_for_timeout(500)

    return standings_data


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        if os.path.exists(AUTH_STATE_FILE):
            print("Authentication state found, loading from file.")
            context = await browser.new_context(storage_state=AUTH_STATE_FILE)
        else:
            print("No authentication state found, please log in.")
            context = await browser.new_context()

        page = await context.new_page()

        await page.goto("https://www.draftkings.com")

        if not os.path.exists(AUTH_STATE_FILE):
            print("Please log in to your DraftKings account in the browser window.")
            input("Once you are logged in, press Enter in this console to continue...")
            await context.storage_state(path=AUTH_STATE_FILE)
            print("Authentication state saved.")

        print("Logged in successfully!")

        # Read the target URL from the first line of example_contests.txt
        try:
            with open('example_contests.txt', 'r') as f:
                target_url = f.readline().strip()
            if not target_url:
                print("Error: example_contests.txt is empty or first line is blank.")
                return
        except FileNotFoundError:
            print("Error: example_contests.txt not found.")
            return

        print(f"Navigating to {target_url}")
        await page.goto(target_url, wait_until="domcontentloaded")
        
        # Wait for the user to manually click the table
        print("\n--- WAITING FOR USER ACTION ---")
        print("Please manually click on the FIRST ROW of the standings table in the browser.")
        input("After you have clicked the row, press Enter here to continue...")
        print("---------------------------------\n")

        # Wait for the table header to ensure the component is ready
        await page.wait_for_selector('.ReactVirtualized__Table__headerRow', timeout=30000)

        standings = await scrape_standings(page)
        
        print("\n--- Standings Summary ---")
        print(f"Total contestants found: {len(standings)}")
        print("Top 5 entries:")
        for person in standings[:5]:
            print(person)
        print("-------------------------\n")
        
        print("The browser will remain open. To exit, close the browser window.")
        await page.wait_for_event('close')

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
