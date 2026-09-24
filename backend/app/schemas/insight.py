from pydantic import BaseModel, ConfigDict


class ThemeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    prevalence: str
    supporting_persona_ids: list[str]


class InsightReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    executive_summary: str
    overall_sentiment: str
    notable_quotes: list[str]
    weak_areas_or_risks: list[str]
    recommendations: list[str]
    themes: list[ThemeResponse]
    disclaimer: str = (
        "This report is generated from AI-simulated personas and should be treated as "
        "exploratory research rather than statistically representative user research."
    )
