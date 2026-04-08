from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from llm_provider import chat
from dotenv import load_dotenv

from observability import create_span, create_trace, end_span, langfuse_client


logger = logging.getLogger(__name__)

_ENV_PATH = Path(__file__).resolve().parent / ".env"
_FALLBACK_ENV_PATH = Path(__file__).resolve().parent / "venv" / ".env"

if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    load_dotenv(_FALLBACK_ENV_PATH)





def _get_trace_id(trace: object | None) -> str | None:
    if trace is None:
        return None

    return getattr(trace, "trace_id", None) or getattr(trace, "id", None)


def run(job_urls: list[str], experience: str) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    trace = None
    span = None

    try:
        trace = create_trace(
            name="job-scout-run",
            metadata={
                "url_count": len(job_urls),
                "timestamp": timestamp,
            },
        )
        span = create_span(
            trace=trace,
            name="llm-health-check",
            input={
                "job_urls": job_urls,
                "experience": experience,
            },
        )

        # LLM call — provider configured via LLM_PROVIDER env var
        response = chat(
            system="You are a job scout agent.",
            user="Reply with OK if you are working correctly.",
            max_tokens=100,
        )
        llm_response = response.strip() if isinstance(response, str) else str(response)

        end_span(
            span,
            output={
                "llm_response": llm_response,
            },
        )

        if langfuse_client is not None:
            langfuse_client.flush()

        return {
            "status": "success",
            "llm_response": llm_response,
            "trace_id": _get_trace_id(trace),
        }
    except Exception as exc:
        logger.exception("Job scout orchestrator run failed")

        if span is not None:
            end_span(
                span,
                output={
                    "error": str(exc),
                },
                level="ERROR",
            )

        if langfuse_client is not None:
            langfuse_client.flush()

        return {
            "status": "error",
            "error": str(exc),
            "trace_id": _get_trace_id(trace),
        }