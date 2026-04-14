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
    truncated = page_text[:6000]

    system = (
        "You are a JSON-only job extraction bot.\n"
        "You NEVER explain yourself.\n"
        "You ONLY output raw valid JSON arrays.\n"
        "No markdown. No code blocks. No explanation.\n"
        "Just the JSON array starting with [ and ending with ]."
    )

    user = f"""Extract job postings from this career page text.
                 
                 RULES:
                 - Output ONLY a JSON array
                 - Start your response with [
                 - End your response with ]
                 - No text before [ or after ]
                 - No markdown, no ```json, no explanation
                 - If no jobs found output exactly: []
                 
                 Each job object must have:
                 - "title": job title string
                 - "url": "{url}"
                 - "date_posted": "unknown" (use unknown if no date visible)
                 - "description": department, location, employment type concatenated as a string
                 
                 Career page text:
                 {truncated}"""

    try:
        response = chat(system=system, user=user, max_tokens=4000)
    except Exception as exc:
        logger.exception("LLM call failed while extracting jobs from %s: %s", url, exc)
        return []

    # Aggressively clean the response and extract JSON array
    response = response.strip()
    response = response.replace("```json", "").replace("```", "")
    response = response.strip()

    start = response.find("[")
    end = response.rfind("]") + 1
    if start == -1 or end == 0:
        logger.warning("No JSON array found in response for %s", url)
        logger.debug("Raw LLM response: %s", response[:500])
        return []

    json_str = response[start:end]

    try:
        parsed = json.loads(json_str)
    except Exception:
        logger.warning("Failed to parse JSON for %s", url)
        logger.debug("Extracted JSON substring: %s", json_str[:500])
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
