from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

_AGENT_DIR = Path(__file__).resolve().parents[1]
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from llm_provider import chat


logger = logging.getLogger(__name__)

_FALLBACK_SCORE = {
    "score": "low",
    "reason": "Could not parse match",
    "missing_skills": [],
}


def _strip_code_blocks(response: str) -> str:
    cleaned = response.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def score_job(job: dict, experience: str) -> dict:
    system = (
        "You are a job matching agent. You compare job requirements against "
        "candidate experience and return a match assessment."
    )
    user = f"""Compare this job against the candidate experience.
                 Return ONLY a valid JSON object with no markdown, no explanation:
                 {{
                   "score": "high" or "medium" or "low",
                   "reason": "one sentence why this is a good or bad match",
                   "missing_skills": ["skill1", "skill2"]
                 }}
                 
                 Job title: {job.get('title', '')}
                 Job description: {job.get('description', '')[:1000]}
                 
                 Candidate experience: {experience}"""

    try:
        response = chat(system=system, user=user, max_tokens=1000)
        cleaned = _strip_code_blocks(response)
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            parsed = _FALLBACK_SCORE.copy()
    except Exception:
        parsed = _FALLBACK_SCORE.copy()

    merged = dict(job)
    merged.update(parsed)
    return merged


def score_all(jobs: list[dict], experience: str) -> list[dict]:
    scored_jobs: list[dict] = []
    for index, job in enumerate(jobs):
        scored_job = score_job(job, experience)
        logger.info("Scored job %d/%d: %s", index + 1, len(jobs), job.get("title", ""))
        scored_jobs.append(scored_job)
    return scored_jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_job = {
        "title": "Senior Backend Engineer",
        "description": "Build Java and Spring Boot services, design APIs, and work with cloud systems.",
    }
    sample_experience = (
        "Java backend engineer with Spring Boot, REST APIs, and distributed systems experience. "
        "Currently upskilling in AI agent engineering and LLM orchestration."
    )
    result = score_job(sample_job, sample_experience)
    print(json.dumps(result, indent=2))