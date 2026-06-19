"""CV analysis API schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AnalysisStartResponse(BaseModel):
    job_id: str
    status: Literal["processing"] = "processing"


class AnalysisJobResponse(BaseModel):
    job_id: str
    status: Literal["processing", "ready", "failed"]
    stage: Literal["parsing", "features", "judging", "done"] = "parsing"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    elapsed_s: Optional[float] = None
