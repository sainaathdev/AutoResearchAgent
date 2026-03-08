"""
LLM wrapper — Ollama-backed via LangChain with retry logic.
Falls back gracefully when Ollama is slow or returns errors.
"""

import json
import re
from typing import Any
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

import src.config as cfg


def get_llm(model: str | None = None, temperature: float | None = None) -> Any:
    """Return a LangChain ChatOllama instance."""
    if not OLLAMA_AVAILABLE:
        raise ImportError("langchain-ollama not installed.")
    return ChatOllama(
        base_url=cfg.OLLAMA_BASE_URL,
        model=model or cfg.OLLAMA_MODEL,
        temperature=temperature if temperature is not None else cfg.OLLAMA_TEMPERATURE,
        num_ctx=2048,           # ← reduced: avoids OOM on smaller machines
        num_predict=1024,       # ← cap output tokens to prevent hangs
        timeout=120,            # ← 2 min hard timeout per call
        keep_alive="10m",       # ← keep model warm between calls
    )


@retry(
    stop=stop_after_attempt(2),               # only 2 attempts (was 3)
    wait=wait_exponential(multiplier=1, min=3, max=15),
    reraise=True,
)
def call_llm(prompt: str, system: str = "", model: str | None = None,
             temperature: float | None = None) -> str:
    """Call the LLM and return plain text response."""
    from langchain_core.messages import SystemMessage, HumanMessage

    # Hard-cap prompt length to avoid overflowing context
    prompt = prompt[:4000]
    system = system[:1000]

    llm = get_llm(model=model, temperature=temperature)
    messages = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=prompt))

    response = llm.invoke(messages)
    return response.content.strip()


def call_llm_safe(prompt: str, system: str = "", fallback: str = "",
                  model: str | None = None, temperature: float | None = None) -> str:
    """Call LLM with a guaranteed fallback — never raises."""
    try:
        return call_llm(prompt, system=system, model=model, temperature=temperature)
    except Exception as e:
        logger.warning(f"[LLM] call_llm_safe caught: {type(e).__name__}: {str(e)[:120]}")
        return fallback


def call_llm_json(prompt: str, system: str = "", model: str | None = None,
                  temperature: float | None = None) -> dict | list:
    """Call LLM expecting JSON output. Handles markdown code blocks."""
    raw = call_llm(prompt, system=system, model=model, temperature=temperature)

    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract JSON object from middle of text
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        logger.warning(f"[LLM] Non-JSON response, returning raw: {cleaned[:200]}")
        return {"raw_response": cleaned}


def call_llm_json_safe(prompt: str, system: str = "", fallback: dict | None = None,
                       model: str | None = None, temperature: float | None = None) -> dict | list:
    """call_llm_json with a guaranteed fallback — never raises."""
    if fallback is None:
        fallback = {}
    try:
        return call_llm_json(prompt, system=system, model=model, temperature=temperature)
    except Exception as e:
        logger.warning(f"[LLM] call_llm_json_safe caught: {type(e).__name__}: {str(e)[:120]}")
        return fallback
