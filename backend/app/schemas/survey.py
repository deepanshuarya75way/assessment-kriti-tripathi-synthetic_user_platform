from pydantic import BaseModel, ConfigDict


class SurveyQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    order_index: int
    text: str
    question_type: str
    options: list[str] | None = None
    rationale: str


class SurveyResponseItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_id: str
    persona_slug: str
    answer: str
    sentiment: str
    confidence: float
