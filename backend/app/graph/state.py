"""
Shared state that flows through every node in the LangGraph pipeline.

Each agent reads what it needs and returns a partial dict that LangGraph merges
into this state. This is the pipeline-level "memory" that carries context
(product, audience, personas, survey, responses) from one agent to the next
within a single run. Durable, cross-run memory is the **database** — see
docs/design-decisions.md for why the DB replaced the original in-memory
checkpointer for recovery.
"""

from typing import TypedDict

from app.graph.schemas import InsightReport, Persona, PersonaSurveyResponse, SurveyQuestion


class GraphState(TypedDict, total=False):
    # ---- inputs ----
    product_description: str
    target_audience: str
    research_goal: str
    num_personas: int
    num_questions: int

    # ---- produced by agents, in order ----
    personas: list[Persona]
    survey_questions: list[SurveyQuestion]
    survey_responses: list[PersonaSurveyResponse]
    insight_report: InsightReport

    # ---- bookkeeping ----
    run_id: str
    log: list[str]
