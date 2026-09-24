"""Unit tests for the LLM structured-output schema validators (spec §21)."""

import pytest
from pydantic import ValidationError

from app.graph.schemas import SurveyAnswer, SurveyQuestion


def test_multiple_choice_requires_options():
    with pytest.raises(ValidationError):
        SurveyQuestion(
            id="q1", text="Pick one", question_type="multiple_choice", options=None, rationale="x"
        )


def test_multiple_choice_requires_at_least_two_options():
    with pytest.raises(ValidationError):
        SurveyQuestion(
            id="q1",
            text="Pick one",
            question_type="multiple_choice",
            options=["only one"],
            rationale="x",
        )


def test_non_mc_options_are_stripped():
    q = SurveyQuestion(
        id="q1", text="Rate it", question_type="likert_1_5", options=["1", "2"], rationale="x"
    )
    assert q.options is None


def test_valid_multiple_choice_kept():
    q = SurveyQuestion(
        id="q1", text="Pick", question_type="multiple_choice", options=["a", "b"], rationale="x"
    )
    assert q.options == ["a", "b"]


def test_confidence_is_clamped():
    assert (
        SurveyAnswer(question_id="q1", answer="a", sentiment="positive", confidence=5).confidence
        == 1.0
    )
    assert (
        SurveyAnswer(question_id="q1", answer="a", sentiment="positive", confidence=-2).confidence
        == 0.0
    )


def test_confidence_invalid_defaults_to_half():
    a = SurveyAnswer(question_id="q1", answer="a", sentiment="neutral", confidence="not-a-number")
    assert a.confidence == 0.5
