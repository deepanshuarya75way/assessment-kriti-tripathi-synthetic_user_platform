"""
AGENT 1 — Persona Generation Agent.

Generates personas ONE AT A TIME. Asking a model to fill every rich field for
several personas in a single response produces large output that smaller/free
models frequently truncate, leaving later personas with missing required fields.
One persona per call keeps each response small and reliable; each previously
generated persona is summarized back into the prompt so the next stays distinct.

Improvements over the original (spec §11): a lightweight duplicate check drops a
persona that is near-identical (same name or same occupation+savviness) to one
already generated, and retries once with an explicit "make it different" nudge.
"""

import logging

from langchain_core.prompts import ChatPromptTemplate

from app.graph.llm import invoke_structured
from app.graph.schemas import Persona
from app.graph.state import GraphState

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Synthetic Persona Generation Agent.

Given a product description, a target audience description, and a research goal,
generate ONE realistic synthetic persona representing a sub-segment of that
target audience.

Rules:
- Ground the persona in specifics plausible for the stated audience.
- The persona must be internally consistent (a "low tech-savviness" persona
  shouldn't complain about advanced API rate limits).
- `behavioral_patterns` must be concrete, observable habits (not adjectives).
- `psychological_profile` must go deeper than `personality_traits`.
- `persona_summary` should read like a natural introductory paragraph.
- If personas already generated are shown, make this one clearly DISTINCT:
  vary demographics, tech-savviness, motivation and pain points.
"""

USER_TEMPLATE = """Product:
{product_description}

Target audience:
{target_audience}

Research goal:
{research_goal}

Personas already generated in this batch (avoid duplicating these):
{existing_personas_block}

Generate persona {index} of {total} now. Give it id "{persona_id}".
"""


def _existing_block(personas: list[Persona]) -> str:
    if not personas:
        return "(none yet — this is the first persona)"
    return "\n".join(
        f"- {p.name}: {p.occupation}, tech-savviness={p.tech_savviness}, "
        f"traits={', '.join(p.personality_traits)}"
        for p in personas
    )


def _is_duplicate(candidate: Persona, existing: list[Persona]) -> bool:
    for p in existing:
        if candidate.name.strip().lower() == p.name.strip().lower():
            return True
        if (
            candidate.occupation.strip().lower() == p.occupation.strip().lower()
            and candidate.tech_savviness == p.tech_savviness
        ):
            return True
    return False


def persona_agent_node(state: GraphState) -> dict:
    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("user", USER_TEMPLATE)])
    num_personas = state.get("num_personas", 5)
    log_lines = state.get("log", [])
    personas: list[Persona] = []

    for i in range(1, num_personas + 1):
        persona_id = f"p{i}"
        persona = _generate_one(prompt, state, personas, i, num_personas, persona_id, log_lines)
        persona.id = persona_id  # stable id regardless of what the model echoed
        personas.append(persona)

    log_lines.append(f"[persona_agent] generated {len(personas)} personas")
    return {"personas": personas, "log": log_lines}


def _generate_one(prompt, state, personas, i, total, persona_id, log_lines) -> Persona:
    for _attempt in range(2):
        try:
            persona: Persona = invoke_structured(
                prompt,
                Persona,
                {
                    "product_description": state["product_description"],
                    "target_audience": state["target_audience"],
                    "research_goal": state.get("research_goal", "general product validation"),
                    "existing_personas_block": _existing_block(personas),
                    "index": i,
                    "total": total,
                    "persona_id": persona_id,
                },
                temperature=0.9,
                label=f"persona_agent(persona={i}/{total})",
            )
        except Exception as e:
            log_lines.append(f"[persona_agent] persona {i}/{total} failed: {e}")
            log.error("persona_agent failed for persona %d/%d: %s", i, total, e)
            raise RuntimeError(f"persona_agent: failed to generate persona {i}/{total}") from e

        if not _is_duplicate(persona, personas):
            return persona
        log_lines.append(f"[persona_agent] persona {i} was a near-duplicate; retrying")
    # Accept the last candidate rather than fail the whole run over a duplicate.
    return persona
