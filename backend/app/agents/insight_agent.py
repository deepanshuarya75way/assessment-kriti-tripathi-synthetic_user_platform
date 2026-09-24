"""
AGENT 4 — Insight Extraction Agent.

Analyzes ALL persona responses together, surfaces themes, sentiment patterns and
risks, and produces a structured InsightReport. The prompt keeps a clear line
between the observed synthetic responses, the AI's interpretation, and the
recommendations (spec §14) — and never claims the data is real user research.
"""

import logging

from langchain_core.prompts import ChatPromptTemplate

from app.graph.llm import invoke_structured
from app.graph.schemas import InsightReport
from app.graph.state import GraphState

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an Insight Extraction Agent for SYNTHETIC user research.

The responses you are given come from AI-simulated personas, NOT real users. Treat
them as exploratory signal, never as statistically representative data.

You will be given a product, the research goal, the personas, the survey questions
and every persona's answers. Your job:
- Identify cross-cutting themes (patterns across multiple personas).
- Note where personas diverge and why (tie divergence to persona traits).
- Give an honest overall sentiment read — do not inflate positivity.
- Call out weak areas / risks the team should address.
- End with concrete, prioritized recommendations.

Keep three layers distinct: the observed synthetic response, your interpretation,
and your recommendation. Ground every claim in the actual responses. Do not invent data.
"""

USER_TEMPLATE = """Product:
{product_description}

Research goal:
{research_goal}

Personas:
{persona_block}

Survey questions:
{questions_block}

Full response data (persona_id -> question_id -> answer/sentiment):
{responses_block}

Produce the structured insight report now.
"""


def _persona_block(personas) -> str:
    return "\n".join(
        f"- {p.id}: {p.name}, {p.occupation}, traits: {', '.join(p.personality_traits)}, "
        f"psychological profile: {p.psychological_profile}"
        for p in personas
    )


def _questions_block(questions) -> str:
    return "\n".join(f"- {q.id}: {q.text}" for q in questions)


def _responses_block(responses) -> str:
    lines = []
    for r in responses:
        for a in r.answers:
            lines.append(
                f"- persona={r.persona_id} | question={a.question_id} | "
                f'sentiment={a.sentiment} | confidence={a.confidence} | answer="{a.answer}"'
            )
    return "\n".join(lines)


def insight_agent_node(state: GraphState) -> dict:
    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("user", USER_TEMPLATE)])
    log_lines = state.get("log", [])
    try:
        result: InsightReport = invoke_structured(
            prompt,
            InsightReport,
            {
                "product_description": state["product_description"],
                "research_goal": state.get("research_goal", "general product validation"),
                "persona_block": _persona_block(state["personas"]),
                "questions_block": _questions_block(state["survey_questions"]),
                "responses_block": _responses_block(state["survey_responses"]),
            },
            temperature=0.3,
            label="insight_agent",
        )
    except Exception as e:
        log_lines.append(f"[insight_agent] failed: {e}")
        log.error("insight_agent failed: %s", e)
        raise RuntimeError("insight_agent: failed to generate insight report") from e

    log_lines.append("[insight_agent] insight report generated")
    return {"insight_report": result, "log": log_lines}
