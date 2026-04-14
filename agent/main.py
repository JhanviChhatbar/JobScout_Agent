from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from orchestrator import run


_ENV_PATH = Path(__file__).resolve().parent / ".env"
_FALLBACK_ENV_PATH = Path(__file__).resolve().parent / "venv" / ".env"

if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    load_dotenv(_FALLBACK_ENV_PATH)


def main() -> None:
    job_urls = [
        "https://revenuecat.com/careers",
        "https://anthropic.com/careers",
    ]
    experience = ("""
        9 years Java backend engineering. Expert in Spring Boot, Kafka, 
event-driven architecture, microservices, distributed systems, 
REST API design, PostgreSQL, Redis, system design.

Current projects:
- Real-Time Match Momentum Engine: Java, Spring Boot, microkernel plugin 
  pattern, event-driven pipeline, sport-agnostic adapter registry
- Job Scout Agent: Python, LangChain, Gemini API, Playwright scraping, 
  pgvector RAG, Langfuse observability, agent orchestration, tool use,
  structured output

Upskilling: LangChain4j, LLM tool use, agent orchestration, RAG with 
pgvector, Langfuse tracing, LangGraph, agentic design patterns.

Targeting: Staff Engineer or AI Agent Engineer roles at product companies.
Strong backend fundamentals with hands-on AI agent engineering experience.
Comfortable with ambiguity, self-directed, remote-first culture experience.
""""
    )

    result = run(job_urls, experience)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()