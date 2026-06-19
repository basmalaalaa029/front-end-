"""Job matching — HTTP request/response schemas."""

from __future__ import annotations

from typing import List, Optional

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


class MatchRequest(BaseModel):
    cv_text: str = Field(..., min_length=50)
    target_role: str = ""
    location: str = ""
    min_salary: str = ""


class MatchResponse(BaseModel):
    session_id: str
    status: str = "completed"
    total_jobs: int = 0
    message: str = ""


class MatchResultsResponse(BaseModel):
    session_id: str
    status: str = "completed"
    jobs: List[MatchedJob] = Field(default_factory=list)
    target_role: str = ""
    latency_ms: int = 0
    error: Optional[str] = None
