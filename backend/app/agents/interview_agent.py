"""
Persona chat + placement-interview building blocks.

The persona-chat helper is intentionally **stateless**: the API/service layer
owns conversation history (persisted in the database), and passes it in on each
turn. This fixes the original design where chat history lived only in memory and
was lost on restart. The placement mock-interview helpers (bonus feature) are
kept here too, reusing the same centralized LLM service.
"""

import logging

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.graph.llm import invoke_chat, invoke_structured
from app.graph.schemas import InterviewFeedback, InterviewPersona

log = logging.getLogger(__name__)


def persona_system_prompt(persona: dict, product_description: str = "") -> str:
    """Build the in-character system prompt from a persona dict (ORM- or schema-derived)."""
    parts = [
        f"You are {persona['name']}, a real person being interviewed about a product.",
        f"Age: {persona.get('age', 'n/a')}. Occupation: {persona.get('occupation', '')}.",
        f"Background: {persona.get('background', '')}",
        f"Personality traits: {', '.join(persona.get('personality_traits', []))}.",
        f"Behavioral patterns: {', '.join(persona.get('behavioral_patterns', []))}.",
        f"Psychological profile: {persona.get('psychological_profile', '')}.",
        f"Goals: {', '.join(persona.get('goals', []))}.",
        f"Pain points: {', '.join(persona.get('pain_points', []))}.",
        f"Tech savviness: {persona.get('tech_savviness', '')}.",
        f"Communication style: {persona.get('communication_style', '')}.",
    ]
    if product_description:
        parts.append(f"The product being discussed: {product_description}")
    parts.append(
        "Stay fully and consistently in character for the entire interview: never break "
        "character, never mention you are an AI, and never contradict opinions about the "
        "product you already expressed earlier in this conversation. Answer as this specific "
        "person genuinely would, in their own style — do not be artificially positive."
    )
    return " ".join(parts)


def persona_reply(
    persona: dict,
    history: list[tuple[str, str]],
    user_message: str,
    product_description: str = "",
    temperature: float = 0.6,
) -> str:
    """
    Produce one in-character persona reply.

    ``history`` is a list of (role, content) where role is "user" or "persona".
    The new ``user_message`` is appended before invoking the model. History is
    supplied by the caller (loaded from the DB) so this function holds no state.
    """
    messages: list = []
    for role, content in history:
        messages.append(
            HumanMessage(content=content) if role == "user" else AIMessage(content=content)
        )
    messages.append(HumanMessage(content=user_message))

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", persona_system_prompt(persona, product_description)),
            MessagesPlaceholder("history"),
        ]
    )
    try:
        ai_message = invoke_chat(
            prompt,
            {"history": messages},
            temperature=temperature,
            label=f"persona_chat(persona={persona.get('slug', persona.get('id', '?'))})",
        )
    except Exception as e:
        log.error("persona_reply failed: %s", e)
        raise RuntimeError("persona_chat: failed to get a response from the persona") from e
    return ai_message.content


# ---------- Placement mock-interview bonus (kept, reusable) ----------

INTERVIEW_PERSONA_SYSTEM_PROMPT = (
    "You design synthetic interviewer personas for a campus placement prep platform. "
    "Given a company name and round type (HR / Technical / Coding / Managerial), create a "
    "realistic interviewer persona, including a distinctive tone, a sample opening line and "
    "what this interviewer screens for."
)


def generate_interview_persona(company: str, round_type: str) -> InterviewPersona:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", INTERVIEW_PERSONA_SYSTEM_PROMPT),
            (
                "user",
                "Company: {company}\nRound type: {round_type}\nGenerate the interviewer persona.",
            ),
        ]
    )
    return invoke_structured(
        prompt,
        InterviewPersona,
        {"company": company, "round_type": round_type},
        temperature=0.8,
        label="generate_interview_persona",
    )


def interview_feedback(transcript: str) -> InterviewFeedback:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a placement-readiness evaluator. Read the transcript and produce "
                "honest, specific, actionable feedback. Score conservatively.",
            ),
            ("user", "Transcript:\n{transcript}\n\nProduce the structured feedback now."),
        ]
    )
    return invoke_structured(
        prompt,
        InterviewFeedback,
        {"transcript": transcript},
        temperature=0.2,
        label="interview_feedback",
    )
