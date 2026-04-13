import asyncio
import json
from scraper.playwright_scraper import scrape
from tools.extract_jobs import extract_jobs

async def main():
    url = "https://revenuecat.com/careers"
    print(f"Scraping {url}...")
    text = await scrape(url)
    print(f"Got {len(text)} chars")
    
    print("Extracting jobs...")
    jobs = extract_jobs(text, url)
    print(f"\nFound {len(jobs)} jobs:")
    print(json.dumps(jobs, indent=2))

asyncio.run(main())