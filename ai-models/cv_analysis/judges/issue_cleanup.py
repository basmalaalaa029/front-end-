"""Lightweight post-model cleanup — not full judge validation.

Drops obvious false positives (rewrite already in CV) and dedupes near-identical issues.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from cv_analysis.judges.schemas import JudgeOutput
from cv_analysis.keywords.keyword_engine import keyword_absent_from_cv

_WORD_RE = re.compile(r"[a-z0-9]{4,}", re.I)
_OVERLAP_DROP = 0.72


def _content_words(text: str) -> List[str]:
    return [w.lower() for w in _WORD_RE.findall(text or "")]


def text_overlap_ratio(text: str, cv_lower: str) -> float:
    words = _content_words(text)
    if len(words) < 4:
        return 0.0
    hits = sum(1 for w in words if w in cv_lower)
    return hits / len(words)


def _normalize_issue(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _is_near_duplicate(a: str, b: str) -> bool:
    na, nb = _normalize_issue(a), _normalize_issue(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    wa, wb = set(_content_words(na)), set(_content_words(nb))
    if not wa or not wb:
        return False
    return len(wa & wb) / len(wa | wb) >= 0.55


def _rewrite_contradicts_cv(rewrite: str, suggestion: str, cv_lower: str) -> bool:
    for part in (rewrite, suggestion):
        if part.strip() and text_overlap_ratio(part, cv_lower) >= _OVERLAP_DROP:
            return True
    return False


def prune_judge_output(scores: JudgeOutput, cv_text: str) -> JudgeOutput:
    """Remove issue rows whose fix text already appears in the CV."""
    cv_lower = cv_text.lower()
    weaknesses: List[str] = []
    suggestions: List[str] = []
    rewrites: List[str] = []

    wlist = scores.weaknesses or []
    slist = scores.improvement_suggestions or []
    rlist = scores.rewrite_suggestions or []

    for i, raw_w in enumerate(wlist):
        weakness = (raw_w or "").strip()
        if not weakness:
            continue
        suggestion = (slist[i] if i < len(slist) else "").strip()
        rewrite = (rlist[i] if i < len(rlist) else "").strip()
        if _rewrite_contradicts_cv(rewrite, suggestion, cv_lower):
            continue
        if any(_is_near_duplicate(weakness, existing) for existing in weaknesses):
            continue
        weaknesses.append(weakness)
        suggestions.append(suggestion)
        rewrites.append(rewrite)

    return scores.model_copy(
        update={
            "weaknesses": weaknesses,
            "improvement_suggestions": suggestions,
            "rewrite_suggestions": rewrites,
        }
    )


def filter_missing_keywords_for_prompt(cv_text: str, keywords: List[str]) -> List[str]:
    """Only pass JD terms that heuristic matching still considers absent."""
    return [k for k in keywords if keyword_absent_from_cv(cv_text, k)]


def dedupe_strengths(items: List[str]) -> List[str]:
    out: List[str] = []
    for item in items:
        text = (item or "").strip()
        if not text:
            continue
        if any(_is_near_duplicate(text, existing) for existing in out):
            continue
        out.append(text)
    return out
