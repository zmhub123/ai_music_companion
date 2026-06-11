from pydantic import BaseModel, Field


class OnboardingRequest(BaseModel):
    skill_level: str
    style_preferences: list[str] = Field(min_length=1)


class PreferencesRequest(BaseModel):
    skill_level: str
    style_preferences: list[str] = Field(min_length=1)
