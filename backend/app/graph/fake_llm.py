"""
Deterministic fake LLM provider.

Returns plausible, schema-valid structured data with **no network call**, so:
- the automated test suite never depends on a live API or an API key;
- a reviewer can run the whole product end-to-end offline (``LLM_PROVIDER=fake``).

This is clearly-labelled synthetic scaffolding for demos/tests. It is *not*
presented anywhere as real research or real model output — the UI and reports
always state the data is synthetic, and fake-mode is surfaced explicitly.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.graph.schemas import (
    InsightReport,
    InterviewFeedback,
    InterviewPersona,
    Persona,
    PersonaSurveyResponse,
    SurveyAnswer,
    SurveyQuestion,
    SurveySet,
    Theme,
)

_NAMES = [
    "Riya Sharma",
    "Arjun Mehta",
    "Fatima Khan",
    "Daniel Osei",
    "Ananya Rao",
    "Marcus Lee",
    "Priya Nair",
    "Sofia Alvarez",
    "Tomás Costa",
    "Wei Chen",
]
_TRAITS = [
    ["anxious", "diligent", "budget-conscious", "curious"],
    ["confident", "impatient", "pragmatic", "social"],
    ["skeptical", "analytical", "reserved", "thorough"],
    ["optimistic", "distracted", "collaborative", "adaptable"],
]
_SAVVY = ["low", "medium", "high"]


def _seed(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest(), 16)


class FakeChatMessage:
    """Minimal stand-in for a LangChain AIMessage (only ``.content`` is used)."""

    def __init__(self, content: str):
        self.content = content


def fake_structured(schema: type, inputs: dict[str, Any]) -> Any:
    """Return a deterministic, valid instance of ``schema`` derived from ``inputs``."""
    if schema is Persona:
        return _fake_persona(inputs)
    if schema is SurveySet:
        return _fake_survey(inputs)
    if schema is PersonaSurveyResponse:
        return _fake_response(inputs)
    if schema is InsightReport:
        return _fake_insight(inputs)
    if schema is InterviewPersona:
        return _fake_interview_persona(inputs)
    if schema is InterviewFeedback:
        return _fake_interview_feedback(inputs)
    raise ValueError(f"fake_structured has no generator for schema {schema!r}")


def _fake_persona(inputs: dict) -> Persona:
    idx = int(inputs.get("index", 1))
    # Base offset varies per product; adding idx keeps names distinct within a run.
    base = _seed(inputs.get("product_description", ""))
    name = _NAMES[(base + idx) % len(_NAMES)]
    seed = base + idx
    savvy = _SAVVY[(base + idx) % 3]
    traits = _TRAITS[(base + idx) % len(_TRAITS)]
    return Persona(
        id=str(inputs.get("persona_id", f"p{idx}")),
        name=name,
        age=20 + ((seed + idx) % 30),
        occupation=f"Representative user #{idx} of the target audience",
        background=(
            f"{name} is part of the described audience and interacts with products "
            f"like this one regularly. (Synthetic persona generated in fake-LLM mode.)"
        ),
        personality_traits=traits,
        behavioral_patterns=[
            "compares options before committing",
            "abandons flows that feel slow or confusing",
            "asks peers for recommendations",
        ],
        psychological_profile=(
            "Motivated by getting a reliable outcome with minimal wasted effort; "
            "wary of tools that overpromise."
        ),
        goals=["solve the core problem quickly", "trust the results", "avoid extra cost"],
        pain_points=["confusing onboarding", "unclear value", "too much manual work"],
        tech_savviness=savvy,  # type: ignore[arg-type]  # deterministic value from _SAVVY
        communication_style="direct, practical, occasionally skeptical",
        persona_summary=(
            f"{name}, {20 + ((seed + idx) % 30)}, a representative member of the target "
            f"audience with {savvy} tech-savviness, pragmatic and outcome-focused."
        ),
    )


def _fake_survey(inputs: dict) -> SurveySet:
    n = int(inputs.get("num_questions", 6))
    templates = [
        ("How valuable would this product be for you?", "likert_1_5", None),
        ("What is the single biggest problem you hope this solves?", "open_ended", None),
        (
            "Which feature matters most to you?",
            "multiple_choice",
            ["Core workflow", "Reporting", "Integrations", "Support"],
        ),
        ("Would you try this product in the next month?", "yes_no", None),
        ("How likely are you to recommend it to a peer?", "likert_1_5", None),
        ("What would make you stop using it?", "open_ended", None),
        ("How do you currently solve this problem?", "open_ended", None),
        ("Is the pricing model clear to you?", "yes_no", None),
    ]
    questions = []
    for i in range(n):
        text, qtype, opts = templates[i % len(templates)]
        questions.append(
            SurveyQuestion(
                id=f"q{i + 1}",
                text=text,
                question_type=qtype,  # type: ignore[arg-type]  # value from templates
                options=opts,
                rationale="Surfaces decision-relevant signal for the stated research goal.",
            )
        )
    return SurveySet(questions=questions)


def _fake_response(inputs: dict) -> PersonaSurveyResponse:
    block = inputs.get("questions_block", "")
    qids = [line.split("]")[0].strip("[ ") for line in block.splitlines() if line.startswith("[")]
    sentiments = ["positive", "neutral", "negative", "mixed"]
    seed = _seed(inputs.get("name", "persona") + block)
    answers = [
        SurveyAnswer(
            question_id=qid,
            answer=(
                f"As {inputs.get('name', 'this persona')}, my honest take: it could help, "
                f"but I'd need it to be simple and clearly worth the effort."
            ),
            sentiment=sentiments[(seed + i) % 4],  # type: ignore[arg-type]
            confidence=round(0.4 + ((seed + i) % 6) / 10, 2),
        )
        for i, qid in enumerate(qids)
    ]
    return PersonaSurveyResponse(persona_id="", answers=answers)


def _fake_insight(inputs: dict) -> InsightReport:
    persona_block = inputs.get("persona_block", "")
    pids = [ln.split(":")[0].strip("- ") for ln in persona_block.splitlines() if ln.strip()]
    pids = pids[:5] or ["p1"]
    return InsightReport(
        executive_summary=(
            "Synthetic personas see clear potential in the product but consistently flag "
            "onboarding clarity and demonstrated value as decisive. Prioritizing a simple, "
            "high-signal core workflow is the safest MVP bet. (Fake-LLM demo output.)"
        ),
        overall_sentiment="mixed",
        key_themes=[
            Theme(
                title="Onboarding clarity is decisive",
                description="Personas abandon tools that feel slow or unclear early on.",
                supporting_persona_ids=pids,
                prevalence="high",
            ),
            Theme(
                title="Value must be demonstrated fast",
                description="Skeptical users want proof before investing effort or money.",
                supporting_persona_ids=pids[:3],
                prevalence="medium",
            ),
        ],
        notable_quotes=[
            f"[{pids[0]}] It could help, but only if it's simple.",
            f"[{pids[-1]}] I'd need to see the value in the first few minutes.",
        ],
        weak_areas_or_risks=[
            "Onboarding friction could cause early drop-off.",
            "Unclear differentiation from existing workflows.",
        ],
        recommendations=[
            "Ship a focused core workflow first; defer secondary features.",
            "Invest in a fast, guided onboarding with an early 'aha' moment.",
            "Make pricing and value explicit up front.",
        ],
    )


def _fake_interview_persona(inputs: dict) -> InterviewPersona:
    company = inputs.get("company", "Acme")
    round_type = inputs.get("round_type", "HR")
    return InterviewPersona(
        id="iv1",
        name=f"{company} {round_type} Interviewer",
        role=f"{round_type} round interviewer at {company}",
        company_style=f"{company}-style {round_type} screening: structured and professional.",
        tone="formal, probing, fair",
        focus_areas=["communication", "role fit", "fundamentals"],
        sample_opening_line="Hello, thanks for joining. Tell me a bit about yourself.",
    )


def _fake_interview_feedback(inputs: dict) -> InterviewFeedback:
    return InterviewFeedback(
        strengths=["Clear structure in answers", "Stayed calm"],
        weak_areas=["Could give more concrete examples", "Depth on fundamentals"],
        communication_score=6,
        technical_score=5,
        confidence_score=6,
        actionable_next_steps=[
            "Practice the STAR method for behavioral answers.",
            "Prepare two concrete project examples.",
        ],
    )


def fake_chat(inputs: dict) -> FakeChatMessage:
    """Deterministic reply for a persona/interview chat turn."""
    history = inputs.get("history", [])
    last = ""
    for msg in reversed(history):
        content = getattr(msg, "content", "")
        if content:
            last = content
            break
    return FakeChatMessage(
        content=(
            "Speaking in character: that's a fair question. Honestly, I'd want it to be "
            "simple and clearly useful before I commit. "
            + (
                f'You asked: "{last[:80]}" — my take is it depends on how much effort it saves me.'
                if last
                else "What would you like to know?"
            )
        )
    )
