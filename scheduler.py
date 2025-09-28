import asyncio
import logging
from datetime import datetime
from scraper import DraftKingsScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def scheduler():
    """Run the scraper every minute with persistent browser."""
    logger.info("Starting scheduler - will run every 60 seconds")
    
    # Initialize the scraper once
    scraper = DraftKingsScraper()
    try:
        logger.info("Initializing browser and logging in...")
        if not await scraper.initialize():
            logger.error("Failed to initialize scraper. Exiting.")
            return
        
        logger.info("Browser initialized successfully. Starting periodic scraping...")
        
        while True:
            try:
                logger.info("Starting scheduled scrape...")
                await scraper.refresh_and_scrape()
                logger.info("Scheduled scrape completed successfully")
            except Exception as e:
                logger.error(f"Error during scheduled scrape: {e}", exc_info=True)
            
            # Wait 45 seconds, then refresh 15 seconds before next scrape
            logger.info("Waiting 45 seconds until next scrape...")
            await asyncio.sleep(45)
            
            # Refresh the page 15 seconds before the next data pull
            logger.info("Refreshing page 15 seconds before next scrape...")
            try:
                await scraper.page.reload(wait_until="domcontentloaded")
                await asyncio.sleep(15)  # Wait for page to fully load
            except Exception as e:
                logger.error(f"Error refreshing page: {e}", exc_info=True)
                
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {e}", exc_info=True)
    finally:
        # Clean up browser resources
        await scraper.close()
        logger.info("Scheduler shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(scheduler())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {e}", exc_info=True)
