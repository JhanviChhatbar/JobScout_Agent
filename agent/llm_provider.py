from google import genai
from google.genai import types
import anthropic
import os
from dotenv import load_dotenv
import time
import logging


load_dotenv()

# Read provider/model at module level
provider = os.getenv("LLM_PROVIDER", "gemini")
model = os.getenv("LLM_MODEL", "gemini-2.0-flash")
print(f"LLM Provider: {provider} | Model: {model}")


max_retries = 5
for attempt in range(max_retries):
    try:
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens
            )
        )
        return response.text
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            wait = 60 * (attempt + 1)  # 60s, 120s, 180s...
            logging.warning(
                f"Rate limited. Waiting {wait}s "
                f"before retry {attempt + 1}/{max_retries}"
            )
            time.sleep(wait)
        else:
            raise
raise Exception("Max retries exceeded after rate limiting")


def _chat_anthropic(system: str, user: str, max_tokens: int) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text


def chat(system: str, user: str, max_tokens: int = 1000) -> str:
    if provider == "gemini":
        return _chat_gemini(system, user, max_tokens)
    if provider == "anthropic":
        return _chat_anthropic(system, user, max_tokens)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


if __name__ == "__main__":
    result = chat(
        system="You are a helpful assistant.",
        user="Reply with OK if you are working correctly.",
        max_tokens=50,
    )
    print(f"Response: {result}")