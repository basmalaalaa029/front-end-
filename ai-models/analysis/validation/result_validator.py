"""Validates and coerces the fine-tuned model's JSON output into AnalysisResult."""

import logging
import re
from typing import List

from pydantic import BaseModel, Field, ValidationError, field_validator

from analysis.config import SCORE_MAX, SCORE_MIN

log = logging.getLogger("analysis")

MAX_LIST_ITEMS = 5
MIN_ITEM_CHARS = 15
_SENTENCE_END_RE = re.compile(r'[.!?]["\')\]]?$')
_DUPLICATE_SIMILARITY_THRESHOLD = 0.6
_PREFIX_WORD_COUNT = 6
_MAX_ITEMS_PER_PREFIX = 1
_STOPWORDS = {
    "the", "a", "an", "of", "to", "and", "or", "is", "are", "in", "on", "for",
    "that", "this", "it", "its", "with", "as", "be", "not", "any", "your",
    "resume", "cv", "does", "do", "which", "could", "would", "should",
}


def _looks_truncated(item: str) -> bool:
    """Heuristic: flags items that were cut off mid-word/mid-sentence rather than
    finished naturally. Catches salvage-parser fragments and token-limit cutoffs
    that slip past the model despite prompt instructions."""
    if len(item) < MIN_ITEM_CHARS:
        return True
    if not _SENTENCE_END_RE.search(item):
        return True
    return False


def _normalize_for_similarity(item: str) -> set:
    words = re.findall(r"[a-z']+", item.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def _jaccard_similarity(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


def _opening_template(item: str) -> str:
    """First few words, normalized. Catches the 'X under professional experience
    are not structured to ...' repetition pattern: items that vary only in their
    tail clause but share the same templated opening are really one observation
    restated, even when full-sentence Jaccard similarity falls below threshold."""
    words = re.findall(r"[a-z']+", item.lower())
    return " ".join(words[:_PREFIX_WORD_COUNT])


def _dedupe_and_clean(items: List[str]) -> List[str]:
    """Drops truncated fragments and near-duplicate items (same root cause worded
    differently, or the same templated opening clause repeated with a different
    tail), then caps the list length. This is a safety net independent of how
    well the model follows the prompt's own dedup instructions."""
    cleaned: List[str] = []
    seen_token_sets: List[set] = []
    prefix_counts: dict = {}

    for item in items:
        item = item.strip()
        if not item or _looks_truncated(item):
            continue

        prefix = _opening_template(item)
        if prefix_counts.get(prefix, 0) >= _MAX_ITEMS_PER_PREFIX:
            continue

        tokens = _normalize_for_similarity(item)
        is_duplicate = any(
            _jaccard_similarity(tokens, seen) >= _DUPLICATE_SIMILARITY_THRESHOLD
            for seen in seen_token_sets
        )
        if is_duplicate:
            continue

        cleaned.append(item)
        seen_token_sets.append(tokens)
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

        if len(cleaned) >= MAX_LIST_ITEMS:
            break

    return cleaned


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
            v = [v]
        elif isinstance(v, list):
            v = [str(item).strip() for item in v if str(item).strip()]
        else:
            return []
        return _dedupe_and_clean(v)


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
    if not result.weaknesses:
        warnings.append("Model returned no weaknesses.")

    return result, warnings
