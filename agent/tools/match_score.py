from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
import time

_AGENT_DIR = Path(__file__).resolve().parents[1]
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from llm_provider import chat
from database.vector_store import get_similar_past_jobs, get_relevant_experience


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
    
    # Get RAG context
    similar_past = get_similar_past_jobs(job.get("description", ""), limit=2)
    relevant_exp = get_relevant_experience(job.get("description", ""), limit=2)
    
    past_context = ""
    if similar_past:
        past_context = "Similar jobs you've seen before:\n"
        for p in similar_past:
            past_context += f"- {p['job_title']}: scored {p['score']} — {p['reason']}\n"
    
    user = f"""Compare this job against the candidate experience.
             
             Job title: {job.get('title', '')}
             Job description: {job.get('description', '')[:1000]}
             
             Relevant candidate experience:
             {relevant_exp if relevant_exp else experience}
             
             {past_context}
             
             Return ONLY a valid JSON object with no markdown:
             {{
               "score": "high" or "medium" or "low",
               "reason": "one sentence explanation",
               "missing_skills": ["skill1", "skill2"]
             }}"""

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
    scored = []
    for i, job in enumerate(jobs):
        logging.info(f"Scoring job {i+1}/{len(jobs)}: {job.get('title', '')}")
        scored.append(score_job(job, experience))
        if i < len(jobs) - 1:
            time.sleep(13)
    return scored


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