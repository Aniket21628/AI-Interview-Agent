import logging
import os
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger("interview_agent.llm")


def get_llm_provider() -> str:
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    if provider != "gemini":
        logger.warning("LLM_PROVIDER=%s is not allowed; forcing gemini", provider)
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


def get_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY is required for Gemini")
    return api_key


def transcribe_audio_file(file_bytes: bytes, filename: str = "voice.webm", language: Optional[str] = None) -> str:
    logger.info("Gemini-only audio transcription requested: filename=%s, size_bytes=%s, language=%s", filename, len(file_bytes), language)
    raise NotImplementedError("Gemini-only mode does not support audio transcription in this backend; use browser speech transcription or a Gemini-compatible speech service with its own endpoint.")


def generate_speech_audio(text: str, voice: str = "alloy") -> bytes:
    logger.info("Gemini-only speech generation requested: voice=%s, text_length=%s", voice, len(text))
    raise NotImplementedError("Gemini-only mode does not support browserless speech generation in this backend; use browser speech synthesis or a separate Gemini TTS integration.")


def get_chat_model():
    provider = get_llm_provider()
    logger.info("Initializing Gemini chat model: provider=%s", provider)

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY is required when LLM_PROVIDER=gemini")

    model_name = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip() or "gemini-2.5-flash"
    logger.info("Using Gemini chat model: model=%s", model_name)
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.7,
        retries=0,
        request_timeout=15,
    )
