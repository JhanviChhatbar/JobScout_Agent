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
    experience = (
        "I am a Java backend engineer with experience building Spring Boot services, "
        "REST APIs, and distributed systems. "
        "I am actively upskilling in AI agent engineering, including LLM orchestration, "
        "observability, and automation workflows."
    )

    result = run(job_urls, experience)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()