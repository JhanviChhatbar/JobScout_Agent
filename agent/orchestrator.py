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
from email_sender import send_digest
from database.db import setup_tables, save_jobs, save_run, filter_new_jobs
from database.vector_store import (
    setup_vector_tables,
    store_job_embedding,
    store_experience_chunks
)
from trust.trust_gate import should_send_email, log_audit


load_dotenv()

logger = logging.getLogger(__name__)


def _get_trace_id(trace: object | None) -> str | None:
    if trace is None:
        return None
    return getattr(trace, "trace_id", None) or getattr(trace, "id", None)


async def run(job_urls: List[str], experience: str, candidate_name: str = "there") -> Dict[str, Any]:
    trace = None
    try:
        setup_tables()
        setup_vector_tables()
        store_experience_chunks(experience)
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

        # STEP 3.6 — Filter out already-seen jobs
        span_dedup = create_span(trace, "dedup-jobs", {"before_dedup": len(filtered_jobs)})
        new_jobs = filter_new_jobs(filtered_jobs)
        end_span(span_dedup, {"after_dedup": len(new_jobs)})

        if not new_jobs:
            if langfuse_client is not None:
                try:
                    langfuse_client.flush()
                except Exception:
                    pass
            return {"status": "no_new_jobs", "pages_scraped": len(to_scrape), "jobs_found": len(all_jobs), 
                    "high_matches": 0, "medium_matches": 0, "trace_id": _get_trace_id(trace)}

        # STEP 4 — Score only new jobs (skip already-seen jobs)
        span_score = create_span(trace, "match-scoring", {"jobs": len(new_jobs)})
        scored_jobs = score_all(new_jobs, experience)
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

        # STEP 6 — Trust gate check
        allowed, reason = should_send_email(scored_jobs, digest)
        log_audit({"jobs_found": len(all_jobs), 
                   "high_matches": high,
                   "trace_id": trace.id if trace else None}, 
                  allowed, reason)
        
        # STEP 7 — Send email only if trust gate passes
        email_sent = False
        span_email = create_span(trace, "send-email", {"allowed": allowed})
        if allowed:
            email_sent = send_digest(
                digest=digest,
                subject=f"Job Scout — {high} high match(es) today"
            )
        else:
            logging.warning(f"Email blocked by trust gate: {reason}")
        end_span(span_email, {"sent": email_sent, "blocked_reason": reason})

        # STEP 8 — Save to database
        span_db = create_span(trace, "save-to-db", {})
        new_jobs = save_jobs(scored_jobs)
        end_span(span_db, {"new_jobs_saved": new_jobs})

        # STEP 8.5 — Store job embeddings
        for job in scored_jobs:
            store_job_embedding(job)

        # STEP 9 — Flush Langfuse and return
        if langfuse_client is not None:
            try:
                langfuse_client.flush()
            except Exception:
                logger.exception("Langfuse flush failed")

        result = {
            "status": "ok",
            "pages_scraped": len(to_scrape),
            "jobs_found": len(all_jobs),
            "high_matches": high,
            "medium_matches": medium,
            "digest": digest,
            "email_sent": email_sent,
            "trace_id": _get_trace_id(trace),
        }
        save_run(result)
        return result
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