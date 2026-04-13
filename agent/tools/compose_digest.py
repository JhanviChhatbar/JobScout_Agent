from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List, Dict

_AGENT_DIR = Path(__file__).resolve().parents[1]
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from llm_provider import chat


logger = logging.getLogger(__name__)


def compose_digest(scored_jobs: List[Dict], candidate_name: str = "there") -> str:
    matched = [j for j in scored_jobs if j.get("score") in ("high", "medium")]
    if not matched:
        return "No matching jobs found today. Will check again tomorrow."

    job_summaries_lines = [
        f"- {job.get('title','')} | Score: {job.get('score')} | {job.get('reason','')} | {job.get('url','')}"
        for job in matched
    ]
    job_summaries = "\n".join(job_summaries_lines)

    system = (
        "You are an email composer. Write clean, professional, concise job digest emails."
    )

    user = f"""Compose a job digest email for {candidate_name}.
                 
                 Matched jobs today:
                 {job_summaries}
                 
                 Format:
                 - Start with: Hi {candidate_name}, here are today's matched jobs:
                 - List each job clearly with title, match level, reason, and URL
                 - End with: Good luck! — Your Job Scout Agent
                 
                 Keep it concise and professional."""

    result = chat(system=system, user=user, max_tokens=600)
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_jobs = [
        {"title": "Senior Backend Engineer", "score": "high", "reason": "Strong Java/Spring experience", "url": "https://example.com/job1"},
        {"title": "AI Agent Engineer", "score": "high", "reason": "Relevant agent orchestration experience", "url": "https://example.com/job2"},
        {"title": "Frontend Engineer", "score": "low", "reason": "No React experience", "url": "https://example.com/job3"},
    ]
    email = compose_digest(sample_jobs, candidate_name="Alex")
    print(email)
