"""Job matching — HTTP request/response schemas."""

from __future__ import annotations

from typing import List, Literal, Optional

from cv_agent.shared.session_schemas import SessionStartResponse, SessionStatusResponse
from pydantic import BaseModel, Field


class JobListing(BaseModel):
    id: str
    brand: str = ""
    logo: str = ""
    title: str
    company: str
    location: str = "Remote"
    salary: str = ""
    description: str = ""


class MatchedJob(BaseModel):
    id: str
    brand: str = ""
    logo: str = ""
    title: str
    company: str
    location: str = ""
    salary: str = ""
    match_score: int = Field(ge=0, le=100, default=0)
    why: str = ""
    source: str = ""
    url: str = ""
    posted: str = ""
    score_breakdown: dict = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    description: str = ""


class MatchRequest(BaseModel):
    cv_text: str = Field(..., min_length=50)
    target_role: str = ""
    location: str = ""
    min_salary: str = ""


class MatchStartResponse(SessionStartResponse):
    """POST /jobs/match response."""


class MatchStatusResponse(SessionStatusResponse):
    stage: Optional[str] = None


class MatchResultsResponse(BaseModel):
    session_id: str
    status: Literal["ready"] = "ready"
    jobs: List[MatchedJob] = Field(default_factory=list)
    target_role: str = ""
    latency_ms: int = 0
    error: Optional[str] = None
