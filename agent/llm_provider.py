from __future__ import annotations

import os
from pathlib import Path

import google.generativeai as genai
from anthropic import Anthropic
from dotenv import load_dotenv


_ENV_PATH = Path(__file__).resolve().parent / ".env"
_FALLBACK_ENV_PATH = Path(__file__).resolve().parent / "venv" / ".env"

if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    load_dotenv(_FALLBACK_ENV_PATH)


def _get_provider() -> str:
    return os.getenv("LLM_PROVIDER", "").strip().lower()


def _get_model() -> str:
    model = os.getenv("LLM_MODEL", "").strip()
    if not model:
        raise ValueError("LLM_MODEL is not set.")
    return model


def _chat_anthropic(system: str, user: str, max_tokens: int) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set.")

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=_get_model(),
        max_tokens=max_tokens,
        system=system,
        messages=[
            {
                "role": "user",
                "content": user,
            }
        ],
    )

    if not response.content:
        return ""

    first_block = response.content[0]
    return getattr(first_block, "text", "")


def _chat_gemini(system: str, user: str, max_tokens: int) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(_get_model())
    prompt = f"System: {system}\n\nUser: {user}"
    response = model.generate_content(
        prompt,
        generation_config={"max_output_tokens": max_tokens},
    )
    return response.text or ""


def chat(system: str, user: str, max_tokens: int = 1000) -> str:
    provider = _get_provider()

    if provider == "anthropic":
        return _chat_anthropic(system, user, max_tokens)

    if provider == "gemini":
        return _chat_gemini(system, user, max_tokens)

    raise ValueError(
        "Unsupported LLM_PROVIDER. Expected 'anthropic' or 'gemini'."
    )


if __name__ == "__main__":
    print(
        chat(
            system="You are a helpful assistant.",
            user="Reply with OK if you are working correctly.",
            max_tokens=100,
        )
    )