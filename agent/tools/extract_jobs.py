from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

_AGENT_DIR = Path(__file__).resolve().parents[1]
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from llm_provider import chat


logger = logging.getLogger(__name__)


def extract_jobs(page_text: str, url: str) -> List[Dict[str, Any]]:
    # Truncate to avoid token limits
    truncated = page_text[:8000]

    system = (
        "You are a job extraction agent. You extract structured job postings from raw career page text."
    )

    user = f"""Extract all job postings from this career page text.
                 Return ONLY a valid JSON array with no markdown, no explanation,
                 no code blocks. Each object must have exactly these keys:
                 - title: job title string
                 - url: use this page url if no specific job url found: {url}
                 - date_posted: date string or "unknown"
                 - description: job description max 200 words
                 
                 Career page text:
                 {truncated}
                 
                 Return empty array [] if no jobs found."""

    try:
        raw = chat(system=system, user=user, max_tokens=1000)
    except Exception as exc:
        logger.exception("LLM call failed while extracting jobs from %s: %s", url, exc)
        return []

    # Remove fenced code blocks and markers
    cleaned = re.sub(r"```[\s\S]*?```", "", raw)
    cleaned = cleaned.replace("```json", "").replace("```", "")

    try:
        parsed = json.loads(cleaned)
    except Exception:
        # Try to extract JSON substring if model wrapped response
        m = re.search(r"\[\s*\{[\s\S]*\}\s*\]", cleaned)
        if not m:
            logger.warning("Failed to parse JSON when extracting jobs from %s", url)
            return []
        try:
            parsed = json.loads(m.group(0))
        except Exception:
            logger.warning("Failed to parse extracted JSON substring for %s", url)
            return []

    if not isinstance(parsed, list):
        logger.warning("LLM returned non-list when extracting jobs from %s", url)
        return []

    jobs = parsed
    logger.info("Extracted %d jobs from %s", len(jobs), url)
    return jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = (
        "Our careers:\n\n"
        "Senior Backend Engineer - Build services using Java and Spring.\n\n"
        "AI Agent Engineer - Work on agent orchestration and LLM pipelines."
    )
    results = extract_jobs(sample, "https://example.com/careers")
    print(json.dumps(results, indent=2))
