import asyncio
from scraper.playwright_scraper import scrape

async def main():
    text = await scrape("https://revenuecat.com/careers")
    print(f"Total chars: {len(text)}")
    print("--- First 2000 chars ---")
    print(text[:2000])
    print("--- Last 1000 chars ---")
    print(text[-1000:])

asyncio.run(main())