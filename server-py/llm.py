import os
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI


def get_llm_provider() -> str:
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    if provider not in {"gemini", "openai"}:
        return "gemini"
    return provider


def is_quota_error(error: Exception) -> bool:
    text = str(error).lower()
    quota_markers = (
        "429",
        "quota",
        "resourceexhausted",
        "rate limit",
        "exceeded your current quota",
        "free_tier_requests",
    )
    return any(marker in text for marker in quota_markers)


def get_chat_model():
    provider = get_llm_provider()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=api_key,
            temperature=0.7,
        )

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY is required when LLM_PROVIDER=gemini")

    model_name = (os.getenv("GEMINI_MODEL") or "gemini-1.5-flash").strip() or "gemini-1.5-flash"
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.7,
        retries=0,
        request_timeout=15,
    )
