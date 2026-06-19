"""CV generation — HTTP request/response schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from cv_generator.models.cv_schema import Education, Experience, Project


class GenerateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    target_role: str = Field(..., min_length=2, max_length=120)
    target_industry: str = ""
    years_experience: str = ""
    summary: str = ""
    tone: Literal["professional", "creative", "technical"] = "professional"
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    location: str = ""
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    education_structured: List[Education] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    skills: List[str] = Field(..., min_length=1)
    experiences: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    job_description: str = ""
    parsed_resume: str = ""
    max_iterations: Optional[int] = Field(default=None, ge=1, le=20)
    score_threshold: Optional[int] = Field(default=None, ge=50, le=100)
    num_candidates: Optional[int] = Field(default=None, ge=1, le=5)
    session_id: str = ""

    @field_validator("skills")
    @classmethod
    def non_empty_skills(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("must contain at least one item")
        return v

    @field_validator("experience", "projects", "education_structured", mode="before")
    @classmethod
    def coerce_structured(cls, v: Any) -> Any:
        return v or []

    @field_validator("experiences", "education", mode="before")
    @classmethod
    def coerce_legacy_lists(cls, v: Any) -> Any:
        return v or []

    def has_content(self) -> bool:
        return bool(self.experience) or bool(self.experiences) or bool(self.projects)


class GenerateResponse(BaseModel):
    session_id: str
    status: str
    message: str
    template_cv: str = ""


class StatusResponse(BaseModel):
    session_id: str
    status: str
    created_at: str
    updated_at: str
    progress_msgs: List[str]
    error: Optional[str] = None


class ResultResponse(BaseModel):
    session_id: str
    status: str
    candidate_name: str = ""
    target_role: str = ""
    total_iterations: int = 0
    final_cv: str = ""
    template_cv: str = ""
    enhanced_data: Optional[Dict[str, Any]] = None
    final_scores: Optional[Dict[str, Any]] = None
    score_trajectory: List[float] = Field(default_factory=list)
    jd_keywords: List[str] = Field(default_factory=list)
    node_errors: List[str] = Field(default_factory=list)
    total_latency_ms: int = 0
    error: Optional[str] = None
