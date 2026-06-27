"""CV analysis — HTTP request/response schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from analysis.validation.result_validator import AnalysisResult


class AnalysisRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    target_role: str = ""


class AnalysisStartResponse(BaseModel):
    """POST /cv-analysis/analyze response (frontend contract)."""

    job_id: str
    status: Literal["processing"] = "processing"


class AnalysisJobResponse(BaseModel):
    """GET /cv-analysis/analyze/{job_id} combined poll response."""

    job_id: str
    status: Literal["processing", "ready", "failed"]
    stage: Literal["parsing", "features", "judging", "done"] = "parsing"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    elapsed_s: Optional[float] = None


class AnalysisStatusResponse(BaseModel):
    session_id: str
    status: str
    stage: Optional[str] = None
    elapsed_s: Optional[float] = None
    error: Optional[str] = None


class AnalysisResultsResponse(BaseModel):
    session_id: str
    status: str = "ready"
    filename: str = ""
    analysis: Optional[AnalysisResult] = None
    warnings: List[str] = Field(default_factory=list)
    error: Optional[str] = None
