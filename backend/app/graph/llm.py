"""
Centralized LLM service (spec §9).

Every LLM call in the application goes through ``invoke_structured`` /
``invoke_chat``. Raw provider calls never appear in agent code. The service adds:

- provider selection (real ``openrouter`` or the deterministic ``fake`` provider);
- retry per model + fallback across models (config-driven);
- a timeout per call;
- structured tracing: each call logs its label, provider, model and duration;
- treating a silent ``None`` (model answered in prose instead of calling the
  required tool) as a failure, so it is retried/failed-over like any error.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.core.config import settings
from app.core.logging import log_event
from app.graph import fake_llm

log = logging.getLogger(__name__)


def _fallback_models() -> list[str]:
    # Deduplicate while preserving order; env model first, then configured fallback.
    return list(dict.fromkeys(m for m in [settings.model_name, settings.fallback_model] if m))


def _build_real_llm(model: str, temperature: float):
    # Imported lazily so the app (and tests) don't require langchain in fake mode.
    from langchain_openai import ChatOpenAI

    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set but LLM_PROVIDER=openrouter.")
    return ChatOpenAI(  # type: ignore[call-arg]  # langchain accepts these kwargs at runtime
        model=model,
        temperature=temperature,
        max_tokens=settings.llm_max_tokens,
        timeout=settings.llm_timeout_seconds,
        api_key=settings.openrouter_api_key,  # type: ignore[arg-type]  # str accepted at runtime
        base_url=settings.openrouter_base_url,
        default_headers={"HTTP-Referer": settings.app_referer, "X-Title": settings.app_title},
    )


def _run_with_retries(build_chain, inputs, label: str) -> Any:
    """Retry per model, fall back across models. Raises RuntimeError if all fail."""
    models = _fallback_models() or ["openrouter/free"]
    last_exc: Exception | None = None
    for model in models:
        chain = build_chain(model)
        for attempt in range(1, settings.llm_retries_per_model + 1):
            started = time.perf_counter()
            try:
                result = chain.invoke(inputs)
                if result is None:
                    raise ValueError(
                        "model returned no structured output (did not call the required "
                        "tool/function — likely responded in plain text)"
                    )
                log_event(
                    log,
                    logging.INFO,
                    "llm.call.ok",
                    label=label,
                    provider="openrouter",
                    model=model,
                    attempt=attempt,
                    duration_ms=round((time.perf_counter() - started) * 1000),
                )
                return result
            except Exception as exc:  # noqa: BLE001 - broad by design (see docstring)
                last_exc = exc
                log_event(
                    log,
                    logging.WARNING,
                    "llm.call.retry",
                    label=label,
                    model=model,
                    attempt=attempt,
                    max_attempts=settings.llm_retries_per_model,
                    error=str(exc),
                )
                if attempt < settings.llm_retries_per_model:
                    time.sleep(settings.llm_retry_backoff_seconds * attempt)
        log_event(log, logging.WARNING, "llm.model.exhausted", label=label, model=model)

    raise RuntimeError(f"{label}: all candidate models failed ({', '.join(models)})") from last_exc


def invoke_structured(
    prompt, schema, inputs: dict, temperature: float | None = None, label: str = "llm_call"
):
    """Return a validated ``schema`` instance from the LLM (or fake provider)."""
    temperature = settings.llm_temperature_default if temperature is None else temperature

    if settings.llm_provider == "fake":
        result = fake_llm.fake_structured(schema, inputs)
        log_event(
            log,
            logging.INFO,
            "llm.call.ok",
            label=label,
            provider="fake",
            model="fake",
            attempt=1,
            duration_ms=0,
        )
        return result

    def build_chain(model: str):
        structured = _build_real_llm(model, temperature).with_structured_output(
            schema, method="function_calling"
        )
        return prompt | structured

    return _run_with_retries(build_chain, inputs, label)


def invoke_chat(prompt, inputs: dict, temperature: float | None = None, label: str = "llm_call"):
    """Plain (non-structured) chat call, e.g. a persona interview turn."""
    temperature = settings.llm_temperature_default if temperature is None else temperature

    if settings.llm_provider == "fake":
        result = fake_llm.fake_chat(inputs)
        log_event(
            log,
            logging.INFO,
            "llm.call.ok",
            label=label,
            provider="fake",
            model="fake",
            attempt=1,
            duration_ms=0,
        )
        return result

    def build_chain(model: str):
        return prompt | _build_real_llm(model, temperature)

    return _run_with_retries(build_chain, inputs, label)


def active_model_label() -> str:
    """Human-readable label of what produced a run (for observability / the report)."""
    if settings.llm_provider == "fake":
        return "fake (offline deterministic provider)"
    return (_fallback_models() or ["openrouter/free"])[0]
