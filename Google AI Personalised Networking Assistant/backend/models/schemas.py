"""
schemas.py
----------
Pydantic request/response models. Keeping these separate from the SQLAlchemy
models in database.py is intentional: API contracts and DB tables are allowed
to evolve independently.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    event_description: str = Field(..., min_length=3, example="AI for Sustainable Cities")
    interests: List[str] = Field(default_factory=list, example=["climate change", "urban planning"])
    bio: Optional[str] = Field(None, example="Product manager interested in climate tech")
    profile_name: Optional[str] = Field(None, example="Jordan")
    num_starters: int = Field(3, ge=1, le=5)


class GenerateResponse(BaseModel):
    interaction_id: int
    extracted_themes: List[str]
    conversation_starters: List[str]


class VerifyRequest(BaseModel):
    query: str = Field(..., min_length=2, example="blockchain in healthcare")
    interaction_id: Optional[int] = None


class VerifyResponse(BaseModel):
    query: str
    summary: str
    source_url: Optional[str] = None
    found: bool


class FeedbackRequest(BaseModel):
    interaction_id: int
    useful: bool


class HistoryItem(BaseModel):
    id: int
    event_description: str
    extracted_themes: List[str]
    generated_starters: List[str]
    fact_check_query: Optional[str]
    fact_check_result: Optional[str]
    feedback: Optional[bool]
    created_at: str

    class Config:
        orm_mode = True


class HistoryResponse(BaseModel):
    items: List[HistoryItem]
