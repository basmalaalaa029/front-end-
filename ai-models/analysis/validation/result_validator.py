"""Validates and coerces the fine-tuned model's JSON output into AnalysisResult."""

import logging
import re
from typing import Any, List

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from analysis.config import SCORE_MAX, SCORE_MIN

log = logging.getLogger("analysis")

MAX_LIST_ITEMS = 10
MIN_ITEM_CHARS = 15
MIN_EXAMPLE_CHARS = 8
MIN_WHAT_TO_DO_CHARS = 10
_SENTENCE_END_RE = re.compile(r'[.!?]["\')\]]?$')
_DUPLICATE_SIMILARITY_THRESHOLD = 0.6
_PREFIX_WORD_COUNT = 6
_MAX_ITEMS_PER_PREFIX = 1
_VAGUE_WHAT_TO_DO_RE = re.compile(
    r"(?i)"
    r"(?:update|revise|improve|fix|edit|change)\s+(?:\w+\s+){0,6}(?:cv|resume|section|part)\b"
    r"|run (?:the |another )?analysis"
    r"|come back (?:and )?(?:run|try)"
)
_STOPWORDS = {
    "the", "a", "an", "of", "to", "and", "or", "is", "are", "in", "on", "for",
    "that", "this", "it", "its", "with", "as", "be", "not", "any", "your",
    "resume", "cv", "does", "do", "which", "could", "would", "should",
}


def _looks_truncated(item: str, *, min_chars: int = MIN_ITEM_CHARS) -> bool:
    """Heuristic: flags items that were cut off mid-word/mid-sentence."""
    item = item.strip()
    if len(item) < min_chars:
        return True
    if item.endswith((",", ":", ";", "-", "—")):
        return True
    if not _SENTENCE_END_RE.search(item):
        # Allow complete phrases without terminal punctuation; drop obvious cutoffs.
        trailing = item.rsplit(None, 1)[-1] if item.split() else ""
        if trailing and trailing[0].islower() and len(item) > 80:
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
    words = re.findall(r"[a-z']+", item.lower())
    return " ".join(words[:_PREFIX_WORD_COUNT])


def _is_vague_what_to_do(text: str) -> bool:
    return bool(_VAGUE_WHAT_TO_DO_RE.search(text.strip()))


def _issues_have_actionable_guidance(issues: List[dict]) -> bool:
    for raw in issues:
        what_to_do = str(raw.get("what_to_do") or raw.get("recommendation") or "").strip()
        if (
            what_to_do
            and len(what_to_do) >= MIN_WHAT_TO_DO_CHARS
            and not _is_vague_what_to_do(what_to_do)
        ):
            return True
    return False


def _dedupe_and_clean_strings(items: List[str]) -> List[str]:
    """Drops truncated fragments and near-duplicate strings, then caps length."""
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


def _issue_dedup_key(issue: "ResumeIssue") -> str:
    return f"{issue.issue} {issue.whats_wrong}".strip()


def _dedupe_and_clean_issues(items: List["ResumeIssue"]) -> List["ResumeIssue"]:
    """Drops truncated or near-duplicate issue objects as a whole."""
    cleaned: List[ResumeIssue] = []
    seen_token_sets: List[set] = []
    prefix_counts: dict = {}

    for item in items:
        whats_wrong = item.whats_wrong.strip()
        what_to_do = item.what_to_do.strip()
        if not whats_wrong or _looks_truncated(whats_wrong):
            continue
        if (
            not what_to_do
            or len(what_to_do) < MIN_WHAT_TO_DO_CHARS
            or _looks_truncated(what_to_do, min_chars=MIN_WHAT_TO_DO_CHARS)
            or _is_vague_what_to_do(what_to_do)
        ):
            continue

        prefix = _opening_template(_issue_dedup_key(item))
        if prefix_counts.get(prefix, 0) >= _MAX_ITEMS_PER_PREFIX:
            continue

        tokens = _normalize_for_similarity(_issue_dedup_key(item))
        is_duplicate = any(
            _jaccard_similarity(tokens, seen) >= _DUPLICATE_SIMILARITY_THRESHOLD
            for seen in seen_token_sets
        )
        if is_duplicate:
            continue

        example = item.example.strip()
        if example and _looks_truncated(example, min_chars=MIN_EXAMPLE_CHARS):
            example = ""

        cleaned.append(
            ResumeIssue(
                issue=item.issue.strip() or whats_wrong.split(".")[0][:72],
                whats_wrong=whats_wrong,
                what_to_do=what_to_do,
                example=example,
            )
        )
        seen_token_sets.append(tokens)
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

        if len(cleaned) >= MAX_LIST_ITEMS:
            break

    return cleaned


def _legacy_lists_to_issues(data: dict) -> List[dict]:
    """Zip legacy parallel arrays into structured issue objects (no per-list dedup)."""
    weaknesses = data.get("weaknesses") or []
    suggestions = data.get("improvement_suggestions") or []
    rewrites = data.get("rewrite_suggestions") or []

    if isinstance(weaknesses, str):
        weaknesses = [weaknesses]
    if isinstance(suggestions, str):
        suggestions = [suggestions]
    if isinstance(rewrites, str):
        rewrites = [rewrites]

    issues: List[dict] = []
    for i, raw_weakness in enumerate(weaknesses):
        whats_wrong = str(raw_weakness).strip()
        if not whats_wrong:
            continue
        what_to_do = str(suggestions[i]).strip() if i < len(suggestions) else ""
        example = str(rewrites[i]).strip() if i < len(rewrites) else ""
        issue_title = whats_wrong.split(".")[0].strip()[:72] or f"Issue {len(issues) + 1}"
        issues.append(
            {
                "issue": issue_title,
                "whats_wrong": whats_wrong,
                "what_to_do": what_to_do,
                "example": example,
            }
        )
    return issues


def _coerce_issue_dict(raw: Any) -> dict | None:
    if not isinstance(raw, dict):
        return None
    whats_wrong = str(raw.get("whats_wrong") or raw.get("problem") or "").strip()
    if not whats_wrong:
        return None
    issue = str(raw.get("issue") or raw.get("title") or "").strip()
    if not issue:
        issue = whats_wrong.split(".")[0].strip()[:72] or "Needs improvement"
    return {
        "issue": issue,
        "whats_wrong": whats_wrong,
        "what_to_do": str(raw.get("what_to_do") or raw.get("recommendation") or "").strip(),
        "example": str(raw.get("example") or raw.get("rewrite") or "").strip(),
    }


class ResumeIssue(BaseModel):
    issue: str = Field(..., min_length=1)
    whats_wrong: str = Field(..., min_length=1)
    what_to_do: str = Field(..., min_length=1)
    example: str = ""

    @field_validator("issue", "whats_wrong", "what_to_do", "example", mode="before")
    @classmethod
    def _strip_text(cls, v):
        if v is None:
            return ""
        return str(v).strip()


class AnalysisResult(BaseModel):
    clarity_score: int = Field(ge=SCORE_MIN, le=SCORE_MAX, default=0)
    structure_score: int = Field(ge=SCORE_MIN, le=SCORE_MAX, default=0)
    impact_score: int = Field(ge=SCORE_MIN, le=SCORE_MAX, default=0)
    skills_relevance_score: int = Field(ge=SCORE_MIN, le=SCORE_MAX, default=0)
    ats_readiness_score: int = Field(ge=SCORE_MIN, le=SCORE_MAX, default=0)
    overall_score: int = Field(ge=SCORE_MIN, le=SCORE_MAX, default=0)

    strengths: List[str] = Field(default_factory=list)
    issues: List[ResumeIssue] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_legacy_shape(cls, data: Any):
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        weaknesses = normalized.get("weaknesses") or []
        suggestions = normalized.get("improvement_suggestions") or []
        legacy_issues = (
            _legacy_lists_to_issues(normalized)
            if weaknesses or suggestions or normalized.get("rewrite_suggestions")
            else []
        )

        structured_issues: List[dict] = []
        for raw in normalized.get("issues") or []:
            item = _coerce_issue_dict(raw)
            if item:
                structured_issues.append(item)

        if legacy_issues and _issues_have_actionable_guidance(legacy_issues):
            normalized["issues"] = legacy_issues
        elif structured_issues and _issues_have_actionable_guidance(structured_issues):
            normalized["issues"] = structured_issues
        elif legacy_issues:
            normalized["issues"] = legacy_issues
        else:
            normalized["issues"] = structured_issues

        for legacy_key in ("weaknesses", "improvement_suggestions", "rewrite_suggestions"):
            normalized.pop(legacy_key, None)

        return normalized

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

    @field_validator("strengths", mode="before")
    @classmethod
    def _coerce_strengths(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            v = [v]
        elif isinstance(v, list):
            v = [str(item).strip() for item in v if str(item).strip()]
        else:
            return []
        return _dedupe_and_clean_strings(v)

    @field_validator("issues", mode="before")
    @classmethod
    def _coerce_issues(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            return []
        parsed: List[ResumeIssue] = []
        for raw in v:
            item = _coerce_issue_dict(raw)
            if not item:
                continue
            try:
                parsed.append(ResumeIssue.model_validate(item))
            except ValidationError:
                continue
        return _dedupe_and_clean_issues(parsed)


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
    if not result.issues:
        log.warning("Analysis result rejected: no issues with actionable guidance.")
        return None, ["Model returned no issues with actionable recommendations."]

    return result, warnings
