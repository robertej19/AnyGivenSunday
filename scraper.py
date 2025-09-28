import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright
from html_parser import parse_dk_standings

AUTH_STATE_FILE = "auth_state.json"



class DraftKingsScraper:
    """Scraper class that maintains browser state across multiple runs."""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.target_url = None
        
    async def initialize(self):
        """Initialize browser and navigate to the contest page."""
        if self.browser is None:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            
            if os.path.exists(AUTH_STATE_FILE):
                print("Authentication state found, loading from file.")
                self.context = await self.browser.new_context(storage_state=AUTH_STATE_FILE)
            else:
                print("No authentication state found, please log in.")
                self.context = await self.browser.new_context()

            self.page = await self.context.new_page()
            await self.page.goto("https://www.draftkings.com")

            if not os.path.exists(AUTH_STATE_FILE):
                print("Please log in to your DraftKings account in the browser window.")
                input("Once you are logged in, press Enter in this console to continue...")
                await self.context.storage_state(path=AUTH_STATE_FILE)
                print("Authentication state saved.")

            print("Logged in successfully!")

            # Read the target URL from the first line of example_contests.txt
            try:
                with open('example_contests.txt', 'r') as f:
                    self.target_url = f.readline().strip()
                if not self.target_url:
                    print("Error: example_contests.txt is empty or first line is blank.")
                    return False
            except FileNotFoundError:
                print("Error: example_contests.txt not found.")
                return False

            print(f"Navigating to {self.target_url}")
            await self.page.goto(self.target_url, wait_until="domcontentloaded")
            
            # Wait for the page to load
            print("Waiting 10 seconds for page to load...")
            await self.page.wait_for_timeout(10000)
            
            # Wait for the standings table to be present
            await self.page.wait_for_selector('.ReactVirtualized__Table.ContestStandings_contest-standings-table', timeout=30000)
            print("Standings table found!")
            
        return True
    
    async def refresh_and_scrape(self):
        """Refresh the page and scrape the current standings."""
        if not self.page:
            print("Browser not initialized. Call initialize() first.")
            return None
            
        print("Refreshing page...")
        await self.page.reload(wait_until="domcontentloaded")
        
        # Wait for the page to load
        print("Waiting 10 seconds for page to load...")
        await self.page.wait_for_timeout(10000)
        
        # Wait for the standings table to be present
        await self.page.wait_for_selector('.ReactVirtualized__Table.ContestStandings_contest-standings-table', timeout=30000)
        print("Standings table found!")
        
        # Scroll through all rows to ensure they're loaded (React Virtualized only renders visible rows)
        print("Loading all standings data by scrolling...")
        rows_locator = self.page.locator('.ReactVirtualized__Table__row.ContestStandings_row')
        previous_count = 0
        
        while True:
            current_count = await rows_locator.count()
            if current_count == previous_count:
                break
            previous_count = current_count
            
            # Scroll to load more rows
            await rows_locator.last.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(500)
        
        print(f"Loaded {previous_count} rows of standings data")

        # Get the entire page HTML content
        print("Getting page HTML content...")
        html_content = await self.page.content()
        
        # Parse the HTML content
        standings_df = parse_dk_standings(html_content)
        
        # Create data_downloads directory if it doesn't exist
        os.makedirs("data_downloads", exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_downloads/standings_{timestamp}.csv"
        
        # Save to CSV
        standings_df.to_csv(filename, index=False)
        
        print("\n--- Standings Summary ---")
        print(f"Total contestants found: {len(standings_df)}")
        print(f"Data saved to: {filename}")
        print("\nTop 5 entries:")
        print(standings_df.head())
        print("-------------------------\n")
        
        return standings_df
    
    async def close(self):
        """Close the browser and cleanup resources."""
        if self.browser:
            await self.browser.close()
            await self.playwright.stop()
            print("Browser closed and resources cleaned up.")

# Legacy function for backward compatibility
async def scrape_standings():
    """Legacy function - creates a new scraper instance for single use."""
    scraper = DraftKingsScraper()
    try:
        if await scraper.initialize():
            return await scraper.refresh_and_scrape()
    finally:
        await scraper.close()

async def main():
    """Main function for standalone execution."""
    try:
        await scrape_standings()
    except Exception as e:
        print(f"Error during scraping: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
