"""Pipeline result types for CV generation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JudgeOutput(BaseModel):
    """Rule-based judge output for generation scoring."""

    clarity_score: int = Field(ge=0, le=100, default=0)
    structure_score: int = Field(ge=0, le=100, default=0)
    impact_score: int = Field(ge=0, le=100, default=0)
    skills_relevance_score: int = Field(ge=0, le=100, default=0)
    ats_readiness_score: int = Field(ge=0, le=100, default=0)
    overall_score: int = Field(ge=0, le=100, default=0)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    rewrite_suggestions: List[str] = Field(default_factory=list)

    @classmethod
    def fallback(cls, reason: str = "parse failure") -> "JudgeOutput":
        return cls(weaknesses=[f"Judge output could not be parsed: {reason}"])

    def average_score(self) -> float:
        return (
            self.clarity_score + self.structure_score + self.impact_score
            + self.skills_relevance_score + self.ats_readiness_score
        ) / 5

    def lowest_metric(self) -> str:
        metrics = {
            "Clarity": self.clarity_score,
            "Structure": self.structure_score,
            "Impact": self.impact_score,
            "Skills relevance": self.skills_relevance_score,
            "ATS readiness": self.ats_readiness_score,
        }
        return min(metrics, key=metrics.get)  # type: ignore[arg-type]

    def passes(self, threshold: int) -> bool:
        return all(
            v >= threshold for v in [
                self.clarity_score, self.structure_score, self.impact_score,
                self.skills_relevance_score, self.ats_readiness_score,
            ]
        ) and self.overall_score >= threshold


class PipelineResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    session_id: str
    candidate_name: str
    target_role: str
    total_iterations: int
    final_cv: str
    template_cv: str = ""
    enhanced_data: Optional[Dict[str, Any]] = None
    final_scores: Optional[JudgeOutput] = None
    score_trajectory: List[float] = Field(default_factory=list)
    node_errors: List[str] = Field(default_factory=list)
    jd_keywords: List[str] = Field(default_factory=list)
    total_latency_ms: int = 0
