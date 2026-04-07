from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langfuse import Langfuse


load_dotenv()


def _warn(message: str) -> None:
    print(f"Warning: {message}")


def _create_langfuse_client() -> Langfuse | None:
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST")

    missing_vars = [
        env_var
        for env_var, value in {
            "LANGFUSE_PUBLIC_KEY": public_key,
            "LANGFUSE_SECRET_KEY": secret_key,
            "LANGFUSE_HOST": host,
        }.items()
        if not value
    ]

    if missing_vars:
        _warn(
            "Langfuse is disabled because these environment variables are missing: "
            + ", ".join(missing_vars)
        )
        return None

    return Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
    )


langfuse_client = _create_langfuse_client()


def create_trace(name: str, metadata: dict[str, Any]) -> Any | None:
    if langfuse_client is None:
        _warn("create_trace skipped because Langfuse is not configured.")
        return None

    return langfuse_client.start_observation(
        name=name,
        as_type="span",
        metadata=metadata,
    )


def create_span(trace: Any, name: str, input: dict[str, Any]) -> Any | None:
    if trace is None:
        _warn("create_span skipped because no trace was provided.")
        return None

    return trace.start_observation(
        name=name,
        as_type="span",
        input=input,
    )


def end_span(span: Any, output: dict[str, Any], level: str = "DEFAULT") -> Any | None:
    if span is None:
        _warn("end_span skipped because no span was provided.")
        return None

    update_level = None if level == "DEFAULT" else level.lower()
    span.update(output=output, level=update_level)
    span.end()
    return span


__all__ = ["create_trace", "create_span", "end_span", "langfuse_client"]