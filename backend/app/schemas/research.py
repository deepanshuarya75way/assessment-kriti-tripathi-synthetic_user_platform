from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import settings


class ResearchCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    product_description: str = Field(min_length=10)
    target_audience: str = Field(min_length=5)
    research_goal: str = Field(min_length=5)
    num_personas: int = Field(default=5, ge=settings.min_personas, le=settings.max_personas)
    num_questions: int = Field(default=6, ge=settings.min_questions, le=settings.max_questions)

    @field_validator("product_description", "target_audience", "research_goal")
    @classmethod
    def _cap_length(cls, v: str) -> str:
        # Cost/abuse control (spec §29): reject oversized free-text inputs.
        if len(v) > settings.max_input_chars:
            raise ValueError(f"must be at most {settings.max_input_chars} characters")
        return v.strip()


class ResearchSummary(BaseModel):
    """Lightweight row for list/dashboard views."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    status: str
    num_personas: int
    num_questions: int
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None


class ResearchDetail(ResearchSummary):
    product_description: str
    target_audience: str
    research_goal: str
    model_used: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None


class DashboardStats(BaseModel):
    total: int
    completed: int
    running: int
    failed: int
    pending: int
    recent: list[ResearchSummary]
