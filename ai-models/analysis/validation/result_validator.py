"""Validates and coerces the fine-tuned model's JSON output into AnalysisResult."""

import logging
from typing import List

from pydantic import BaseModel, Field, ValidationError, field_validator

from analysis.config import SCORE_MAX, SCORE_MIN

log = logging.getLogger("analysis")


class AnalysisResult(BaseModel):
    clarity_score: int = Field(ge=SCORE_MIN, le=SCORE_MAX, default=0)
    structure_score: int = Field(ge=SCORE_MIN, le=SCORE_MAX, default=0)
    impact_score: int = Field(ge=SCORE_MIN, le=SCORE_MAX, default=0)
    skills_relevance_score: int = Field(ge=SCORE_MIN, le=SCORE_MAX, default=0)
    ats_readiness_score: int = Field(ge=SCORE_MIN, le=SCORE_MAX, default=0)
    overall_score: int = Field(ge=SCORE_MIN, le=SCORE_MAX, default=0)

    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    rewrite_suggestions: List[str] = Field(default_factory=list)

    @field_validator(
        "clarity_score", "structure_score", "impact_score",
        "skills_relevance_score", "ats_readiness_score", "overall_score",
        mode="before",
    )
    @classmethod
    def _clamp_score(cls, v):
        try:
            v = int(round(float(v)))
        except (TypeError, ValueError):
            return SCORE_MIN
        return max(SCORE_MIN, min(SCORE_MAX, v))

    @field_validator(
        "strengths", "weaknesses", "improvement_suggestions", "rewrite_suggestions",
        mode="before",
    )
    @classmethod
    def _coerce_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return []


def validate_result(parsed: dict) -> tuple:
    """Returns (result, warnings) on success, or (None, [error_message]) on failure."""
    try:
        result = AnalysisResult.model_validate(parsed)
    except ValidationError as exc:
        log.warning("Analysis result failed schema validation: %s", exc)
        return None, [str(exc)]

    warnings = []
    if not result.strengths:
        warnings.append("Model returned no strengths.")

    return result, warnings
