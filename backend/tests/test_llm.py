"""
LLM-layer tests (spec §21). No real API is ever called: the fake provider and
monkeypatched chains stand in. Covers success, retry, fallback and total failure.
"""

import pytest

from app.graph import llm
from app.graph.schemas import Persona, SurveySet


def test_fake_provider_returns_valid_schemas():
    persona = llm.invoke_structured(
        None, Persona, {"index": 1, "persona_id": "p1", "product_description": "x"}
    )
    assert isinstance(persona, Persona)
    survey = llm.invoke_structured(None, SurveySet, {"num_questions": 5})
    assert isinstance(survey, SurveySet) and len(survey.questions) == 5


def test_fake_chat_returns_message():
    msg = llm.invoke_chat(None, {"history": []})
    assert hasattr(msg, "content") and msg.content


class _Chain:
    """Stub chain: raises `fail_times` then returns `value` (None counts as failure)."""

    def __init__(self, value, fail_times=0, exc=RuntimeError("boom")):
        self.value = value
        self.fail_times = fail_times
        self.exc = exc
        self.calls = 0

    def invoke(self, _inputs):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.exc
        return self.value


def test_retry_then_success(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_retries_per_model", 3)
    monkeypatch.setattr(llm.settings, "llm_retry_backoff_seconds", 0)
    monkeypatch.setattr(llm.settings, "model_name", "m1")
    monkeypatch.setattr(llm.settings, "fallback_model", "m2")
    chain = _Chain(value="ok", fail_times=2)
    result = llm._run_with_retries(lambda _model: chain, {}, label="t")
    assert result == "ok"
    assert chain.calls == 3  # failed twice, succeeded on third


def test_falls_back_to_next_model(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_retries_per_model", 1)
    monkeypatch.setattr(llm.settings, "llm_retry_backoff_seconds", 0)
    monkeypatch.setattr(llm.settings, "model_name", "m1")
    monkeypatch.setattr(llm.settings, "fallback_model", "m2")
    chains = {"m1": _Chain(value=None, fail_times=1), "m2": _Chain(value="ok")}
    result = llm._run_with_retries(lambda model: chains[model], {}, label="t")
    assert result == "ok"
    assert chains["m1"].calls == 1 and chains["m2"].calls == 1


def test_none_result_treated_as_failure(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_retries_per_model", 1)
    monkeypatch.setattr(llm.settings, "llm_retry_backoff_seconds", 0)
    monkeypatch.setattr(llm.settings, "model_name", "only")
    monkeypatch.setattr(llm.settings, "fallback_model", "only")
    chain = _Chain(value=None)  # model answered in prose, parser returned None
    with pytest.raises(RuntimeError):
        llm._run_with_retries(lambda _m: chain, {}, label="t")


def test_all_models_fail_raises(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_retries_per_model", 2)
    monkeypatch.setattr(llm.settings, "llm_retry_backoff_seconds", 0)
    monkeypatch.setattr(llm.settings, "model_name", "m1")
    monkeypatch.setattr(llm.settings, "fallback_model", "m2")
    chain = _Chain(value="never", fail_times=99)
    with pytest.raises(RuntimeError, match="all candidate models failed"):
        llm._run_with_retries(lambda _m: chain, {}, label="t")


def test_active_model_label_fake():
    assert "fake" in llm.active_model_label()
