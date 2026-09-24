"""
AGENT 2 — Survey Generation Agent.

Reads the product, research goal and the already-generated personas, then
produces a structured survey (a mix of Likert, open-ended, multiple-choice and
yes/no questions). Structural validity (e.g. multiple_choice must carry options)
is enforced by the SurveyQuestion schema validator.
"""

import logging

from langchain_core.prompts import ChatPromptTemplate

from app.graph.llm import invoke_structured
from app.graph.schemas import SurveySet
from app.graph.state import GraphState

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Survey Design Agent for product research.

Given a product, a research goal, and a set of target personas, design a survey
that surfaces the most decision-relevant insight for the research goal.

Rules:
- Mix question types: some likert_1_5, some open_ended, a couple multiple_choice
  or yes_no where a discrete choice matters.
- Every multiple_choice question MUST include at least 2 options.
- Every question needs a one-line rationale tying it to the research goal.
- Avoid leading or double-barreled questions.
- Order from broad/warm-up to specific/decision-critical.
"""

USER_TEMPLATE = """Product:
{product_description}

Research goal:
{research_goal}

Target personas who will answer this survey (for calibration only — write
generic questions each can answer, do not address them individually):
{persona_briefs}

Generate exactly {num_questions} survey questions.
"""


def _brief(p) -> str:
    return (
        f"- {p.name} ({p.occupation}, tech-savviness: {p.tech_savviness}; "
        f"behavioral patterns: {', '.join(p.behavioral_patterns)})"
    )


def survey_agent_node(state: GraphState) -> dict:
    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("user", USER_TEMPLATE)])
    persona_briefs = "\n".join(_brief(p) for p in state["personas"])
    log_lines = state.get("log", [])
    try:
        result: SurveySet = invoke_structured(
            prompt,
            SurveySet,
            {
                "product_description": state["product_description"],
                "research_goal": state.get("research_goal", "general product validation"),
                "persona_briefs": persona_briefs,
                "num_questions": state.get("num_questions", 6),
            },
            temperature=0.5,
            label="survey_agent",
        )
    except Exception as e:
        log_lines.append(f"[survey_agent] failed: {e}")
        log.error("survey_agent failed: %s", e)
        raise RuntimeError("survey_agent: failed to generate survey questions") from e

    # Re-stamp stable question ids so downstream joins are predictable.
    for idx, q in enumerate(result.questions, start=1):
        q.id = f"q{idx}"

    log_lines.append(f"[survey_agent] generated {len(result.questions)} questions")
    return {"survey_questions": result.questions, "log": log_lines}
