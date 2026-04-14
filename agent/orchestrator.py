from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from observability import create_trace, create_span, end_span, langfuse_client
from scraper.playwright_scraper import scrape_all
from scraper.redis_cache import get_cached, set_cache
from tools.extract_jobs import extract_jobs
from tools.match_score import score_all
from tools.compose_digest import compose_digest


load_dotenv()

logger = logging.getLogger(__name__)


def _get_trace_id(trace: object | None) -> str | None:
    if trace is None:
        return None
    return getattr(trace, "trace_id", None) or getattr(trace, "id", None)


async def run(job_urls: List[str], experience: str, candidate_name: str = "there") -> Dict[str, Any]:
    trace = None
    try:
        trace = create_trace("job-scout-run", {"url_count": len(job_urls)})

        # STEP 2 — Scrape all career pages (with Redis cache)
        span_scrape = create_span(trace, "scraping", {"urls": job_urls})

        pages: Dict[str, str] = {}
        to_scrape: List[str] = []
        cached_count = 0

        for url in job_urls:
            cached = None
            try:
                cached = get_cached(url)
            except Exception:
                cached = None

            if cached:
                pages[url] = cached
                cached_count += 1
            else:
                to_scrape.append(url)

        scraped_results: Dict[str, str] = {}
        if to_scrape:
            scraped_results = await scrape_all(to_scrape)
            for u, text in scraped_results.items():
                pages[u] = text
                try:
                    set_cache(u, text)
                except Exception:
                    logger.exception("Failed to set cache for %s", u)

        end_span(span_scrape, {"pages_scraped": len(to_scrape)})
        logger.info("Pages: %d total, %d served from cache, %d freshly scraped", len(job_urls), cached_count, len(to_scrape))

        # STEP 3 — Extract jobs
        span_extract = create_span(trace, "extract-jobs", {"pages": list(pages.keys())})
        all_jobs: List[Dict[str, Any]] = []
        for url, text in pages.items():
            try:
                jobs = extract_jobs(text or "", url)
                all_jobs.extend(jobs)
            except Exception:
                logger.exception("Failed to extract jobs from %s", url)

        end_span(span_extract, {"total_jobs_found": len(all_jobs)})

        if not all_jobs:
            if langfuse_client is not None:
                try:
                    langfuse_client.flush()
                except Exception:
                    pass
            return {"status": "no_jobs_found", "pages_scraped": len(to_scrape), "jobs_found": 0, "trace_id": _get_trace_id(trace)}

        # STEP 3.5 — Filter jobs before scoring
        span_filter = create_span(trace, "filter-jobs", {"total": len(all_jobs)})
        keywords = ["engineering", "backend", "agent", "software", 
                    "developer", "platform", "infrastructure", "data"]
        filtered_jobs = [
            job for job in all_jobs
            if any(kw in job.get("description", "").lower() for kw in keywords)
        ]
        if not filtered_jobs:
            filtered_jobs = all_jobs[:10]
        logging.info(f"Filtered to {len(filtered_jobs)} relevant jobs from {len(all_jobs)} total")
        end_span(span_filter, {"filtered_jobs": len(filtered_jobs)})

        # STEP 4 — Score filtered jobs
        span_score = create_span(trace, "match-scoring", {"jobs": len(filtered_jobs)})
        scored_jobs = score_all(filtered_jobs, experience)
        high = len([j for j in scored_jobs if j.get("score") == "high"])
        medium = len([j for j in scored_jobs if j.get("score") == "medium"])
        low = len([j for j in scored_jobs if j.get("score") == "low"])
        end_span(span_score, {"high": high, "medium": medium, "low": low})    
        high = sum(1 for j in scored_jobs if j.get("score") == "high")
        medium = sum(1 for j in scored_jobs if j.get("score") == "medium")
        low = sum(1 for j in scored_jobs if j.get("score") == "low")
        end_span(span_score, {"high": high, "medium": medium, "low": low})

        # STEP 5 — Compose digest
        span_digest = create_span(trace, "compose-digest", {"candidate": candidate_name})
        digest = compose_digest(scored_jobs, candidate_name)
        end_span(span_digest, {"email_length": len(digest)})

        # STEP 6 — Flush Langfuse and return
        if langfuse_client is not None:
            try:
                langfuse_client.flush()
            except Exception:
                logger.exception("Langfuse flush failed")

        return {
            "status": "ok",
            "pages_scraped": len(to_scrape),
            "jobs_found": len(all_jobs),
            "high_matches": high,
            "medium_matches": medium,
            "digest": digest,
            "trace_id": _get_trace_id(trace),
        }
    except Exception as exc:
        logger.exception("Job scout pipeline failed")
        try:
            if langfuse_client is not None:
                langfuse_client.flush()
        except Exception:
            pass
        return {"status": "error", "message": str(exc)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    urls = ["https://revenuecat.com/careers", "https://anthropic.com/careers"]
    experience = (
        "Staff Software Engineer with 7+ years Java backend. "
        "Spring Boot, Kafka, event-driven systems. "
        "Building AI agent projects with LangChain, Gemini API, Langfuse observability. "
        "Targeting Staff/AI Agent Engineer roles."
    )
    result = asyncio.run(run(urls, experience, candidate_name="JC"))
    print(json.dumps(result, indent=2))