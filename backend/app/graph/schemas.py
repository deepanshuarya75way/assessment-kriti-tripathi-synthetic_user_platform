"""
Pydantic models used as structured-output targets for the LLM.

Forcing the model to fill these schemas (via ``with_structured_output``) is what
keeps persona/survey/insight generation reliable instead of hoping the LLM
formats free text correctly. These are the *pipeline* contracts — distinct from
the API request/response schemas in ``app/schemas`` and the ORM models in
``app/models``.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------- PERSONA ----------


class Persona(BaseModel):
    id: str = Field(description="short unique slug, e.g. 'p1_riya_tier3_cse'")
    name: str
    age: int = Field(ge=1, le=120)
    occupation: str = Field(description="e.g. 'Final-year B.Tech CSE student, Tier-3 college'")
    background: str = Field(description="2-3 sentences of relevant life/education/career context")
    personality_traits: list[str] = Field(
        description="4-6 adjectives, e.g. ['anxious', 'diligent']"
    )
    behavioral_patterns: list[str] = Field(
        description="3-5 concrete, observable habits/behaviors relevant to the product domain"
    )
    psychological_profile: str = Field(
        description="1-2 sentences on motivations, fears, decision-making style and emotional "
        "relationship to the product domain (deeper than personality_traits)"
    )
    goals: list[str] = Field(description="what this persona wants from the product")
    pain_points: list[str] = Field(description="frustrations relevant to the product domain")
    tech_savviness: Literal["low", "medium", "high"]
    communication_style: str = Field(description="how they talk/write, e.g. 'formal, hesitant'")
    persona_summary: str = Field(description="one-paragraph natural-language summary")


class PersonaSet(BaseModel):
    personas: list[Persona]


# ---------- SURVEY ----------


class SurveyQuestion(BaseModel):
    id: str
    text: str
    question_type: Literal["likert_1_5", "open_ended", "multiple_choice", "yes_no"]
    options: list[str] | None = Field(
        default=None, description="only for multiple_choice; null otherwise"
    )
    rationale: str = Field(description="why this question matters for the product decision")

    @model_validator(mode="after")
    def _validate_options(self):
        """Structural validation (spec §12): multiple_choice needs >=2 options;
        other types must not carry options."""
        if self.question_type == "multiple_choice":
            if not self.options or len(self.options) < 2:
                raise ValueError("multiple_choice questions require at least 2 options")
        elif self.options:
            self.options = None
        return self


class SurveySet(BaseModel):
    questions: list[SurveyQuestion]


# ---------- SURVEY RESPONSES ----------


class SurveyAnswer(BaseModel):
    question_id: str
    answer: str = Field(description="the persona's answer, in their own voice/style")
    sentiment: Literal["positive", "neutral", "negative", "mixed"]
    confidence: float = Field(ge=0, le=1, description="how strongly the persona feels")

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp_confidence(cls, v):
        try:
            return max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            return 0.5


class PersonaSurveyResponse(BaseModel):
    persona_id: str
    answers: list[SurveyAnswer]


# ---------- INSIGHTS ----------


class Theme(BaseModel):
    title: str
    description: str
    supporting_persona_ids: list[str] = Field(default_factory=list)
    prevalence: Literal["low", "medium", "high"]


class InsightReport(BaseModel):
    executive_summary: str
    overall_sentiment: Literal["positive", "neutral", "negative", "mixed"]
    key_themes: list[Theme] = Field(default_factory=list)
    notable_quotes: list[str] = Field(
        default_factory=list,
        description="short paraphrased/attributed quotes, persona_id in brackets",
    )
    weak_areas_or_risks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


# ---------- INTERVIEW MODE (bonus) ----------


class InterviewPersona(BaseModel):
    id: str
    name: str
    role: str = Field(description="e.g. 'Strict Infosys HR Round Interviewer'")
    company_style: str
    tone: str
    focus_areas: list[str]
    sample_opening_line: str


class InterviewFeedback(BaseModel):
    strengths: list[str]
    weak_areas: list[str]
    communication_score: int = Field(ge=1, le=10)
    technical_score: int = Field(ge=1, le=10)
    confidence_score: int = Field(ge=1, le=10)
    actionable_next_steps: list[str]
