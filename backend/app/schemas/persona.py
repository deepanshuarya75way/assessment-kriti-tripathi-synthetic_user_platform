from pydantic import BaseModel, ConfigDict


class PersonaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    age: int
    occupation: str
    background: str
    personality_traits: list[str]
    behavioral_patterns: list[str]
    psychological_profile: str
    goals: list[str]
    pain_points: list[str]
    tech_savviness: str
    communication_style: str
    persona_summary: str
