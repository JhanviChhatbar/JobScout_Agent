from google import genai
from google.genai import types
import anthropic
import os
from dotenv import load_dotenv


load_dotenv()

# Read provider/model at module level
provider = os.getenv("LLM_PROVIDER", "gemini")
model = os.getenv("LLM_MODEL", "gemini-2.0-flash")
print(f"LLM Provider: {provider} | Model: {model}")


def _chat_gemini(system: str, user: str, max_tokens: int) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    full_prompt = f"{system}\n\n{user}"
    response = client.models.generate_content(
        model=model,
        contents=full_prompt,
        config=types.GenerateContentConfig(max_output_tokens=max_tokens),
    )
    return getattr(response, "text", None) or getattr(response, "content", None) or ""


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