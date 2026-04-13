from __future__ import annotations

import asyncio
import logging
from typing import Dict, List

from playwright.async_api import async_playwright


logger = logging.getLogger(__name__)


async def _scrape_one(browser, url: str) -> str:
    page = await browser.new_page()
    try:
        await page.goto(url, timeout=30_000, wait_until="networkidle")
        text = await page.inner_text("body")
        return text
    except Exception as exc:  # catch per-URL errors
        logger.exception("Failed to scrape %s", url)
        return ""
    finally:
        try:
            await page.close()
        except Exception:
            pass


async def scrape(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            return await _scrape_one(browser, url)
        finally:
            await browser.close()


async def scrape_all(urls: List[str]) -> Dict[str, str]:
    results: Dict[str, str] = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            # create tasks for concurrent scraping
            tasks = [asyncio.create_task(_scrape_one(browser, u)) for u in urls]
            texts = await asyncio.gather(*tasks)
            for u, t in zip(urls, texts):
                results[u] = t
            return results
        finally:
            await browser.close()


if __name__ == "__main__":
    import sys

    async def _main():
        url = "https://revenuecat.com/careers"
        text = await scrape(url)
        print((text or "")[:500])

    asyncio.run(_main())
