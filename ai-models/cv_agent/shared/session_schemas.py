"""Canonical async session HTTP contract shared by cv_generator, analysis, job_matcher."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

SessionStatusValue = Literal["processing", "ready", "failed"]


class SessionStartResponse(BaseModel):
    session_id: str
    status: Literal["processing"] = "processing"


class SessionStatusResponse(BaseModel):
    session_id: str
    status: SessionStatusValue
    stage: Optional[str] = None
    progress_msgs: List[str] = Field(default_factory=list)
    elapsed_s: Optional[float] = None
    error: Optional[str] = None


def map_internal_status(internal: str) -> SessionStatusValue:
    """Map legacy internal session statuses to the canonical API enum."""
    if internal in ("ready", "completed"):
        return "ready"
    if internal == "failed":
        return "failed"
    return "processing"
