"""
Multi-provider LLM adapter.

Supports Anthropic, Groq, OpenAI, and Gemini via a unified call_llm() interface.
Only the SDK for the active provider needs to be installed.
"""

from dataclasses import dataclass

from app.config import settings

# Optional imports — only the active provider's SDK is required
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str


async def call_llm(
    *, user_content: str, system_prompt: str = "", max_tokens: int = 1024
) -> LLMResponse:
    """Route an LLM call to the configured provider."""
    provider = settings.llm_provider
    dispatch = {
        "anthropic": _call_anthropic,
        "groq": _call_groq,
        "openai": _call_openai,
        "gemini": _call_gemini,
    }
    fn = dispatch.get(provider)
    if not fn:
        raise ValueError(f"Unknown LLM provider: {provider}")
    return await fn(user_content, system_prompt, max_tokens)


# -- Provider implementations ------------------------------------------------


async def _call_anthropic(
    user_content: str, system_prompt: str, max_tokens: int
) -> LLMResponse:
    if anthropic is None:
        raise ImportError("Install the 'anthropic' package to use the Anthropic provider")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    kwargs = {
        "model": settings.anthropic_model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user_content}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    message = await client.messages.create(**kwargs)
    return LLMResponse(
        text=message.content[0].text,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
        model=settings.anthropic_model,
    )


async def _call_openai_compatible(
    client_cls, api_key: str, model: str, user_content: str, system_prompt: str, max_tokens: int
) -> LLMResponse:
    """Shared logic for OpenAI-compatible APIs (Groq, OpenAI)."""
    if client_cls is None:
        raise ImportError(f"Install the required package for this provider")

    client = client_cls(api_key=api_key)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_content})

    response = await client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
    )
    return LLMResponse(
        text=response.choices[0].message.content,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        model=model,
    )


async def _call_groq(
    user_content: str, system_prompt: str, max_tokens: int
) -> LLMResponse:
    return await _call_openai_compatible(
        AsyncGroq, settings.groq_api_key, settings.groq_model,
        user_content, system_prompt, max_tokens,
    )


async def _call_openai(
    user_content: str, system_prompt: str, max_tokens: int
) -> LLMResponse:
    return await _call_openai_compatible(
        AsyncOpenAI, settings.openai_api_key, settings.openai_model,
        user_content, system_prompt, max_tokens,
    )


async def _call_gemini(
    user_content: str, system_prompt: str, max_tokens: int
) -> LLMResponse:
    if genai is None:
        raise ImportError("Install the 'google-genai' package to use the Gemini provider")

    client = genai.Client(api_key=settings.gemini_api_key)
    config = genai_types.GenerateContentConfig(
        max_output_tokens=max_tokens,
    )
    if system_prompt:
        config.system_instruction = system_prompt

    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=user_content,
        config=config,
    )
    return LLMResponse(
        text=response.text,
        input_tokens=response.usage_metadata.prompt_token_count,
        output_tokens=response.usage_metadata.candidates_token_count,
        model=settings.gemini_model,
    )
