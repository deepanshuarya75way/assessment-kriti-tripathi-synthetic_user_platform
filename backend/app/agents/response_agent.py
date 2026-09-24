"""
AGENT 3 — Survey Response Simulation Agent ("Survey Mode").

Each persona answers every survey question in its own isolated LLM call, so one
persona's voice/context never bleeds into another's (spec §13). After each call
the answers are reconciled against the actual question set: extra answers are
dropped and any missing question is back-filled with a neutral placeholder, so
the response count always matches the survey — the insight agent never sees
malformed data.
"""

import logging

from langchain_core.prompts import ChatPromptTemplate

from app.graph.llm import invoke_structured
from app.graph.schemas import PersonaSurveyResponse, SurveyAnswer
from app.graph.state import GraphState

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are role-playing as ONE specific synthetic persona answering a survey.

Stay strictly in character:
- Name: {name}
- Occupation: {occupation}
- Background: {background}
- Personality traits: {personality_traits}
- Behavioral patterns: {behavioral_patterns}
- Psychological profile: {psychological_profile}
- Goals: {goals}
- Pain points: {pain_points}
- Tech savviness: {tech_savviness}
- Communication style: {communication_style}

Answer every question as this person genuinely would — their real opinion, their
real sentiment, in their own communication style. Do not be artificially
positive. If something wouldn't matter to this persona, say so plainly.
"""

USER_TEMPLATE = """Product being researched:
{product_description}

Answer each of these survey questions:
{questions_block}

For each, give: the answer in your voice, your sentiment
(positive/neutral/negative/mixed), and a confidence 0-1 for how strongly you feel.
"""


def _questions_block(questions) -> str:
    lines = []
    for q in questions:
        opts = f" Options: {q.options}" if q.options else ""
        lines.append(f"[{q.id}] ({q.question_type}) {q.text}{opts}")
    return "\n".join(lines)


def _reconcile(result: PersonaSurveyResponse, questions) -> PersonaSurveyResponse:
    """Ensure exactly one answer per question, in question order."""
    by_qid = {a.question_id: a for a in result.answers}
    reconciled: list[SurveyAnswer] = []
    for q in questions:
        ans = by_qid.get(q.id)
        if ans is None:
            ans = SurveyAnswer(
                question_id=q.id,
                answer="(No answer produced for this question.)",
                sentiment="neutral",
                confidence=0.0,
            )
        else:
            ans.question_id = q.id
        reconciled.append(ans)
    result.answers = reconciled
    return result


def response_agent_node(state: GraphState) -> dict:
    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("user", USER_TEMPLATE)])
    questions = state["survey_questions"]
    questions_block = _questions_block(questions)
    responses = []
    log_lines = state.get("log", [])

    for persona in state["personas"]:
        try:
            result: PersonaSurveyResponse = invoke_structured(
                prompt,
                PersonaSurveyResponse,
                {
                    "name": persona.name,
                    "occupation": persona.occupation,
                    "background": persona.background,
                    "personality_traits": ", ".join(persona.personality_traits),
                    "behavioral_patterns": ", ".join(persona.behavioral_patterns),
                    "psychological_profile": persona.psychological_profile,
                    "goals": ", ".join(persona.goals),
                    "pain_points": ", ".join(persona.pain_points),
                    "tech_savviness": persona.tech_savviness,
                    "communication_style": persona.communication_style,
                    "product_description": state["product_description"],
                    "questions_block": questions_block,
                },
                temperature=0.8,
                label=f"response_agent(persona={persona.id})",
            )
        except Exception as e:
            log_lines.append(f"[response_agent] persona {persona.id} failed: {e}")
            log.error("response_agent failed for persona %s: %s", persona.id, e)
            raise RuntimeError(
                f"response_agent: failed to get survey response for persona {persona.id}"
            ) from e

        result.persona_id = persona.id  # stable id regardless of model echo
        result = _reconcile(result, questions)
        responses.append(result)

    log_lines.append(f"[response_agent] collected responses from {len(responses)} personas")
    return {"survey_responses": responses, "log": log_lines}
